from io import BytesIO
import logging
import time
from typing import Any, List, Optional
from string import Template
from lavague.core.action_template import ActionTemplate
from lavague.core.context import Context, get_default_context
from lavague.core.extractors import (
    BaseExtractor,
    YamlFromMarkdownExtractor,
    DynamicExtractor,
)
from lavague.core.retrievers import BaseHtmlRetriever, get_default_retriever
from lavague.core.utilities.web_utils import (
    display_screenshot,
    sort_files_by_creation,
)
from lavague.core.logger import AgentLogger
from lavague.core.base_engine import BaseEngine, ActionResult
from lavague.core.base_driver import BaseDriver
from llama_index.core import QueryBundle, PromptTemplate
from PIL import Image
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.embeddings import BaseEmbedding

NAVIGATION_ENGINE_PROMPT_TEMPLATE = ActionTemplate(
    """
{driver_capability}

Here is a the next example to answer:

HTML:
{context_str}
Query: {query_str}
Completion:

""",
    YamlFromMarkdownExtractor(),
)

REPHRASE_PROMPT = Template(
    """You are an AI system designed to convert text-based instruction for web actions into standardized instruction for another AI to execute.
For the other AI to execute actions, it first searches through the DOM of the current page to find the code of the element to interact with.
It will then generate the code to interact with the element based on the previsouly retrieved code.

Therefore your goal is to convert the text-based instruction into a search query optimized to allow a retriever to find the right element using the current DOM. 

The search query should not contain information about the action but optimized to not confuse the retriever but rewrite the query to highlight as much as possible HTML information to make it easier for the retriever to find the element.
As the other AI has only access to the DOM and no visual input, remove all visual information cues. You can use cues by mentioning nearby elements to the element to interact with.
Only use plausible names for the elements (button, input, etc.), attribute names and values (values have to be in '')

Here are previous examples:
Text instruction: Type 'Command R plus' on the search bar with placeholder 'Search ...'
Search query: input 'Search ...'
---
Text instruction: Click on the search bar with placeholder 'Rechercher sur Wikipédia', type 'Yann LeCun,' and press Enter.
Search query: input 'Rechercher sur Wikipédia'
---
Text instruction: Click on 'Installation', next to 'Effective and efficient diffusion'
Search query: button 'Installation' text 'Effective and efficient diffusion'
---

Here is the next example to rephrase:

Text instruction: ${instruction}
Search query:"""
)


logging_print = logging.getLogger(__name__)
logging_print.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(format)
logging_print.addHandler(ch)
logging_print.propagate = False


class Rephraser:
    def __init__(
        self,
        llm: BaseLLM = None,
        prompt: PromptTemplate = REPHRASE_PROMPT,
    ):
        self.llm = llm
        self.prompt: Template = prompt
        if self.llm is None:
            self.llm = get_default_context().llm

    def rephrase_query(self, instruction: str) -> str:
        """
        Rephrase the query
        Args:
            instruction (`str`): The instruction to rephrase for the retriever
        Return:
            `str`: The rephrased query
        """
        rephrase_prompt = self.prompt.safe_substitute(instruction=instruction)
        rephrased_query = self.llm.complete(rephrase_prompt).text
        if "Search query:" in rephrased_query:
            rephrased_query = rephrased_query.replace("Search query:", "")
        return rephrased_query


class NavigationEngine(BaseEngine):
    """
    NavigationEngine leverages the llm model and the to output code from the prompt and the html page.

    Args:
        driver (`BaseDriver`):
            The Web driver used to interact with the headless browser
        llm (`BaseLLM`)
            llama-index LLM that will generate the action
        retriever (`BaseHtmlRetriever`)
            Specify which algorithm will be used for RAG
        prompt_template (`PromptTemplate`)
            Squelette of the final prompt
        extractor (`BaseExtractor`)
            Specify how to extract the final code from the llm answer
        time_between_actions (`float`)
            Time between each action
        logger: (`AgentLogger`)
            Logger to log the actions taken by the agent
        embedding: (`BaseEmbedding`)
            Embedding to use for the retriever
    """

    def __init__(
        self,
        driver: BaseDriver,
        llm: BaseLLM = None,
        rephraser: Rephraser = None,
        retriever: BaseHtmlRetriever = None,
        prompt_template: PromptTemplate = NAVIGATION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = DynamicExtractor(),
        time_between_actions: float = 1.5,
        n_attempts: int = 5,
        logger: AgentLogger = None,
        display: bool = False,
        raise_on_error: bool = False,
        embedding: BaseEmbedding = None,
    ):
        if llm is None:
            llm: BaseLLM = get_default_context().llm
        if rephraser is None:
            rephraser = Rephraser(llm)
        if retriever is None:
            retriever = get_default_retriever(driver, embedding=embedding)
        self.driver: BaseDriver = driver
        self.llm: BaseLLM = llm
        self.rephraser = rephraser
        self.retriever: BaseHtmlRetriever = retriever
        self.prompt_template: PromptTemplate = prompt_template.partial_format(
            driver_capability=driver.get_capability()
        )
        self.extractor: BaseExtractor = extractor
        self.time_between_actions = time_between_actions
        self.logger = logger
        self.n_attempts = n_attempts
        self.display = display
        self.raise_on_error = raise_on_error
        self.viewport_only = True

    @classmethod
    def from_context(
        cls,
        context: Context,
        driver: BaseDriver,
        rephraser: Rephraser = None,
        retriever: BaseHtmlRetriever = None,
        prompt_template: PromptTemplate = NAVIGATION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = DynamicExtractor(),
    ) -> "NavigationEngine":
        """
        Create an NavigationEngine from a context
        """
        return cls(
            driver,
            context.llm,
            rephraser,
            retriever,
            prompt_template,
            extractor,
        )

    def get_nodes(self, query: str) -> List[str]:
        """
        Get the nodes from the html page

        Args:
            query (`str`): The query to search for

        Return:
            `List[str]`: The nodes
        """
        source_nodes = self.retriever.retrieve(
            QueryBundle(query_str=query), [self.driver.get_html()], self.viewport_only
        )
        return source_nodes

    def add_knowledge(self, knowledge: str):
        self.prompt_template = self.prompt_template + knowledge

    def get_action_from_context(self, context: str, query: str) -> str:
        """
        Generate the code from a query and a context
        """
        prompt = self.prompt_template.format(context_str=context, query_str=query)
        response = self.llm.complete(prompt).text
        code = self.extractor.extract(response)
        return code

    def set_display(self, display: bool):
        self.display = display

    def get_action(self, query: str) -> Optional[str]:
        """
        Generate the code from a query
        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page
        Return:
            `str`: The generated code
        """
        nodes = self.get_nodes(query)
        context = "\n".join(nodes)
        return self.get_action_from_context(context, query)

    def execute_instruction_gradio(self, instruction: str, action_engine: Any):
        """
        Generates code and executes it to answer the instruction

        Args:
            instruction (`str`): The instruction to perform

        Return:
            `bool`: True if the code was executed without error
            `Any`: The output of navigation is always None
        """

        from gradio import ChatMessage
        from selenium.webdriver.support.ui import WebDriverWait

        success = False
        action_full = ""
        output = None

        rephrased_query = self.rephraser.rephrase_query(instruction)

        action_nb = 0
        navigation_log_total = []

        logging_print.debug("Query for retriever: " + rephrased_query)

        start = time.time()
        source_nodes = self.get_nodes(rephrased_query)
        end = time.time()
        retrieval_time = end - start

        llm_context = "\n".join(source_nodes)
        success = False
        logger = self.logger

        navigation_log = {
            "navigation_engine_input": instruction,
            "rephrased_query": rephrased_query,
            "retrieved_html": source_nodes,
            "retrieval_time": retrieval_time,
            "retrieval_name": self.retriever.__class__.__name__,
        }

        action_outcomes = []
        for _ in range(self.n_attempts):
            if success:
                break
            if self.display:
                try:
                    scr_path = self.driver.get_current_screenshot_folder()
                    lst = sort_files_by_creation(scr_path)
                    for scr in lst:
                        img = Image.open(scr_path.as_posix() + "/" + scr)
                        display_screenshot(img)
                        time.sleep(0.35)
                except:
                    pass
            start = time.time()
            prompt = self.prompt_template.format(
                context_str=llm_context, query_str=instruction
            )
            response = self.llm.complete(prompt).text
            action = self.extractor.extract(response)
            end = time.time()
            action_generation_time = end - start
            action_outcome = {
                "action": action,
                "action_generation_time": action_generation_time,
                "navigation_engine_full_prompt": prompt,
                "navigation_engine_llm": get_model_name(self.llm),
            }
            try:
                # Get information to see which elements are selected
                vision_data = self.driver.get_highlighted_element(action)
                action_full += action
                for item in vision_data:
                    screenshot = item["screenshot"]
                    if action_engine.screenshot_ratio != 1:
                        screenshot = screenshot.resize(
                            (
                                int(screenshot.width / action_engine.screenshot_ratio),
                                int(screenshot.height / action_engine.screenshot_ratio),
                            )
                        )
                    self.image_display = screenshot
                    yield (
                        self.objective,
                        self.url_input,
                        screenshot,
                        self.instructions_history,
                        self.history,
                        output,
                    )

                self.driver.exec_code(action)
                self.history[-1] = ChatMessage(
                    role="assistant",
                    content=f"{action_engine.curr_instruction}\n",
                    metadata={"title": f"✅ Step {action_engine.curr_step}"},
                )
                self.history.append(
                    ChatMessage(role="assistant", content="⏳ Loading the page...")
                )
                yield (
                    self.objective,
                    self.url_input,
                    self.image_display,
                    self.instructions_history,
                    self.history,
                    output,
                )
                time.sleep(1)
                img = self.driver.get_screenshot_as_png()
                img = BytesIO(img)
                img = Image.open(img)
                if action_engine.screenshot_ratio != 1:
                    img = img.resize(
                        (
                            int(img.width / action_engine.screenshot_ratio),
                            int(img.height / action_engine.screenshot_ratio),
                        )
                    )
                self.image_display = img
                yield (
                    self.objective,
                    self.url_input,
                    self.image_display,
                    self.instructions_history,
                    self.history,
                    output,
                )

                WebDriverWait(self.driver.get_driver(), 30).until(
                    lambda d: d.execute_script("return document.readyState")
                    == "complete"
                )

                time.sleep(self.time_between_actions)

                success = True
                action_outcome["success"] = True
                navigation_log["vision_data"] = vision_data
            except Exception as e:
                logging_print.error(f"Navigation error: {e}")
                action_outcome["success"] = False
                action_outcome["error"] = str(e)
                if self.raise_on_error:
                    raise e

            action_outcomes.append(action_outcome)

        navigation_log["action_outcomes"] = action_outcomes
        navigation_log["action_nb"] = action_nb
        action_nb += 1
        navigation_log_total.append(navigation_log)

        if not success:
            self.history[-1] = ChatMessage(
                role="assistant",
                content=f"Instruction: {action_engine.curr_instruction}",
                metadata={"title": f"❌ Step {action_engine.curr_step + 1}"},
            )
        if logger:
            log = {
                "engine": "Navigation Engine",
                "instruction": instruction,
                "engine_log": navigation_log_total,
                "success": success,
                "output": None,
                "code": action_full,
            }

            logger.add_log(log)

        output = ActionResult(
            instruction=instruction,
            code=action_full,
            success=success,
            output=None,
        )
        action_engine.ret = output

        yield (
            self.objective,
            self.url_input,
            self.image_display,
            self.instructions_history,
            self.history,
            output.output,
        )

    def execute_instruction(self, instruction: str) -> ActionResult:
        """
        Generates code and executes it to answer the instruction

        Args:
            instruction (`str`): The instruction to perform

        Return:
            `bool`: True if the code was executed without error
            `Any`: The output of navigation is always None
        """

        success = False
        action_full = ""

        rephrased_query = self.rephraser.rephrase_query(instruction)

        action_nb = 0
        navigation_log_total = []

        logging_print.debug("Query for retriever: " + rephrased_query)

        start = time.time()
        source_nodes = self.get_nodes(rephrased_query)
        end = time.time()
        retrieval_time = end - start

        llm_context = "\n".join(source_nodes)
        success = False
        logger = self.logger

        navigation_log = {
            "navigation_engine_input": instruction,
            "rephrased_query": rephrased_query,
            "retrieved_html": source_nodes,
            "retrieval_time": retrieval_time,
            "retrieval_name": self.retriever.__class__.__name__,
        }

        action_outcomes = []
        for _ in range(self.n_attempts):
            if success:
                break
            if self.display:
                try:
                    scr_path = self.driver.get_current_screenshot_folder()
                    lst = sort_files_by_creation(scr_path)
                    for scr in lst:
                        img = Image.open(scr_path.as_posix() + "/" + scr)
                        display_screenshot(img)
                        time.sleep(0.35)
                except:
                    pass
            start = time.time()
            prompt = self.prompt_template.format(
                context_str=llm_context, query_str=instruction
            )
            response = self.llm.complete(prompt).text
            action = self.extractor.extract(response)
            end = time.time()
            action_generation_time = end - start
            action_outcome = {
                "action": action,
                "action_generation_time": action_generation_time,
                "navigation_engine_full_prompt": prompt,
                "navigation_engine_llm": get_model_name(self.llm),
            }
            action_full += action
            try:
                # Get information to see which elements are selected
                vision_data = self.driver.get_highlighted_element(action)
                if self.display:
                    for item in vision_data:
                        display_screenshot(item["screenshot"])
                        time.sleep(0.2)
                self.driver.exec_code(action)
                time.sleep(self.time_between_actions)
                if self.display:
                    try:
                        screenshot = self.driver.get_screenshot_as_png()
                        screenshot = BytesIO(screenshot)
                        screenshot = Image.open(screenshot)
                        display_screenshot(screenshot)
                    except:
                        pass
                success = True
                action_outcome["success"] = True
                navigation_log["vision_data"] = vision_data
            except Exception as e:
                logging_print.error(f"Navigation error: {e}")
                action_outcome["success"] = False
                action_outcome["error"] = str(e)
                if self.raise_on_error:
                    raise e

            action_outcomes.append(action_outcome)

        navigation_log["action_outcomes"] = action_outcomes
        navigation_log["action_nb"] = action_nb
        action_nb += 1
        navigation_log_total.append(navigation_log)

        if logger:
            log = {
                "engine": "Navigation Engine",
                "instruction": instruction,
                "engine_log": navigation_log_total,
                "success": success,
                "output": None,
                "code": action_full,
            }

            logger.add_log(log)

        return ActionResult(
            instruction=instruction,
            code=action_full,
            success=success,
            output=None,
        )


class NavigationControl(BaseEngine):
    driver: BaseDriver
    time_between_actions: float
    logger: AgentLogger

    def __init__(
        self,
        driver: BaseDriver,
        time_between_actions: float = 1.5,
        logger: AgentLogger = None,
        navigation_engine: Optional[NavigationEngine] = None,
    ) -> None:
        self.driver: BaseDriver = driver
        self.time_between_actions = time_between_actions
        self.logger = logger
        self.display = False
        self.navigation_engine = navigation_engine

    def set_display(self, display: bool):
        self.display = display

    def set_is_full_page(self, is_fullpage: bool):
        if self.navigation_engine is not None:
            self.navigation_engine.viewport_only = not is_fullpage

    def execute_instruction(self, instruction: str) -> ActionResult:
        import inspect

        code = ""
        logger = self.logger

        if "SCROLL_DOWN" in instruction:
            self.driver.scroll_down()
            code = inspect.getsource(self.driver.scroll_down)
        elif "SCROLL_UP" in instruction:
            self.driver.scroll_up()
            code = inspect.getsource(self.driver.scroll_up)
        elif "WAIT" in instruction:
            self.driver.wait(self.time_between_actions)
            code = inspect.getsource(self.driver.wait)
        elif "BACK" in instruction:
            self.driver.back()
            code = inspect.getsource(self.driver.back)
            self.set_is_full_page(False)
        elif "SCAN" in instruction:
            self.driver.get_screenshots_whole_page()
            code = inspect.getsource(self.driver.get_screenshots_whole_page)
            self.set_is_full_page(True)
        elif "MAXIMIZE_WINDOW" in instruction:
            self.driver.maximize_window()
            code = inspect.getsource(self.driver.maximize_window)
        elif "SWITCH_TAB" in instruction:
            tab_id = int(instruction.split(" ")[1])
            try:
                self.driver.switch_tab(tab_id=tab_id)
            except Exception as e:
                raise ValueError(f"Error while switching tab: {e}")
            code = inspect.getsource(self.driver.switch_tab)
            self.set_is_full_page(False)
        else:
            raise ValueError(f"Unknown instruction: {instruction}")
        success = True
        if logger:
            log = {
                "engine": "Navigation Controls",
                "instruction": instruction,
                "engine_log": None,
                "success": success,
                "output": None,
                "code": code,
            }
            logger.add_log(log)

        return ActionResult(
            instruction=instruction, code=code, success=success, output=None
        )


def get_model_name(llm: BaseLLM) -> str:
    try:
        # Try accessing the 'model' attribute
        return llm.model
    except AttributeError:
        try:
            # Try accessing the 'model_name' attribute
            return llm.model_name
        except AttributeError:
            return "Unknown"
