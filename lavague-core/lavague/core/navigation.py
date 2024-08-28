from io import BytesIO
import logging
import time
from typing import Any, List, Optional
from lavague.core.action_template import ActionTemplate
from lavague.core.context import Context, get_default_context
from lavague.core.exceptions import NavigationException
from lavague.core.extractors import (
    BaseExtractor,
    YamlFromMarkdownExtractor,
    DynamicExtractor,
    extract_xpaths_from_html,
)
from lavague.core.retrievers import BaseHtmlRetriever, get_default_retriever
from lavague.core.utilities.web_utils import (
    display_screenshot,
    sort_files_by_creation,
)
from lavague.core.exceptions import HallucinatedException, ElementOutOfContextException
from lavague.core.logger import AgentLogger
from lavague.core.base_engine import BaseEngine, ActionResult
from lavague.core.base_driver import BaseDriver
from llama_index.core import QueryBundle, PromptTemplate
from PIL import Image
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.embeddings import BaseEmbedding
from lavague.core.utilities.profiling import time_profiler

NAVIGATION_ENGINE_PROMPT_TEMPLATE = ActionTemplate(
    """
{driver_capability}

Here is a the next example to answer:

HTML:
{context_str}
Authorized Xpaths: {authorized_xpaths}
Query: {query_str}
Completion:

""",
    YamlFromMarkdownExtractor(),
)

# JSON schema for the action shape
JSON_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "action": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "args": {"type": "object"}},
                "required": ["name", "args"],
            }
        },
        "required": ["action"],
    },
}


logging_print = logging.getLogger(__name__)
logging_print.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(format)
logging_print.addHandler(ch)
logging_print.propagate = False


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
        if retriever is None:
            retriever = get_default_retriever(driver, embedding=embedding)
        self.driver: BaseDriver = driver
        self.llm: BaseLLM = llm
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
        self.shape_validator = JSON_SCHEMA

    @classmethod
    def from_context(
        cls,
        context: Context,
        driver: BaseDriver,
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
        viewport_only = not self.driver.previously_scanned

        html = self.driver.get_html()

        with time_profiler("Retriever Inference", html_size=len(html)) as profiler:
            source_nodes = self.retriever.retrieve(
                QueryBundle(query_str=query), [html], viewport_only
            )

            profiler["retrieved_nodes_size"] = sum(len(node) for node in source_nodes)

        return source_nodes

    def add_knowledge(self, knowledge: str):
        self.prompt_template = self.prompt_template + knowledge

    def get_action_from_context(self, context: str, query: str) -> str:
        """
        Generate the code from a query and a context
        """
        authorized_xpaths = extract_xpaths_from_html(context)

        prompt = self.prompt_template.format(
            context_str=context,
            query_str=query,
            authorized_xpaths=authorized_xpaths,
        )

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

        success = False
        action_full = ""
        output = None

        action_nb = 0
        navigation_log_total = []

        logging_print.debug("Query for retriever: " + instruction)

        start = time.time()
        source_nodes = self.get_nodes(instruction)
        end = time.time()
        retrieval_time = end - start

        llm_context = "\n".join(source_nodes)
        success = False
        logger = self.logger
        self.url_input = self.driver.get_url()

        navigation_log = {
            "navigation_engine_input": instruction,
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
            authorized_xpaths = extract_xpaths_from_html(llm_context)
            prompt = self.prompt_template.format(
                context_str=llm_context,
                query_str=instruction,
                authorized_xpaths=authorized_xpaths,
            )
            response = self.llm.complete(prompt).text
            end = time.time()
            action_generation_time = end - start
            action_outcome = {
                "llm_raw_response": response,
                "action_generation_time": action_generation_time,
                "navigation_engine_full_prompt": prompt,
                "navigation_engine_llm": get_model_name(self.llm),
            }

            try:
                # We extract the action
                action = self.extractor.extract(response)
                self._verify_llm_reponse(response, llm_context)
                action_outcome["action"] = action
                action_full += action

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
                        self.history,
                        output,
                    )

                self.driver.exec_code(action)
                self.history[-1] = ChatMessage(
                    role="assistant",
                    content=f"{action_engine.world_model_output}\n",
                    metadata={
                        "title": f"✅ Step {action_engine.curr_step} - {action_engine.curr_instruction}"
                    },
                )
                self.history.append(
                    ChatMessage(role="assistant", content="⏳ Loading the page...")
                )
                self.url_input = self.driver.get_url()
                yield (
                    self.objective,
                    self.url_input,
                    self.image_display,
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
                    self.history,
                    output,
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
            self.driver.wait_for_idle()

        navigation_log["action_outcomes"] = action_outcomes
        navigation_log["action_nb"] = action_nb
        action_nb += 1
        navigation_log_total.append(navigation_log)

        if not success:
            self.history[-1] = ChatMessage(
                role="assistant",
                content=f"{action_engine.world_model_output}",
                metadata={
                    "title": f"❌ Step {action_engine.curr_step + 1} - {action_engine.curr_instruction}"
                },
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

        self.url_input = self.driver.get_url()

        yield (
            self.objective,
            self.url_input,
            self.image_display,
            self.history,
            output.output,
        )

    def _verify_llm_reponse(self, llm_response: str, authorized_xpaths: List[str]):
        """Make sure the action is performed on a given context to avoid hallucination"""
        actions_obj = self.extractor.extract_as_object(llm_response)
        if not isinstance(actions_obj, list):
            actions_obj = [actions_obj]

        for action_list in actions_obj:
            for action in action_list.get("actions", []):
                xpath = action.get("action", {}).get("args", {}).get("xpath", "")
                if xpath and xpath not in authorized_xpaths:
                    try:
                        self.driver.resolve_xpath(xpath)
                        exception = ElementOutOfContextException(xpath)
                    except:
                        exception = HallucinatedException(xpath)
                    raise exception

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
        action_nb = 0
        navigation_log_total = []

        logging_print.debug("Query for retriever: " + instruction)

        start = time.time()
        source_nodes = self.get_nodes(instruction)
        end = time.time()
        retrieval_time = end - start

        llm_context = "\n".join(source_nodes)
        success = False
        logger = self.logger

        navigation_log = {
            "navigation_engine_input": instruction,
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
            authorized_xpaths = extract_xpaths_from_html(llm_context)
            prompt = self.prompt_template.format(
                context_str=llm_context,
                query_str=instruction,
                authorized_xpaths=authorized_xpaths,
            )

            with time_profiler("Navigation Engine Inference", prompt_size=len(prompt)):
                response = self.llm.complete(prompt).text

            end = time.time()
            action_generation_time = end - start
            action_outcome = {
                "llm_raw_response": response,
                "action_generation_time": action_generation_time,
                "navigation_engine_full_prompt": prompt,
                "navigation_engine_llm": get_model_name(self.llm),
            }

            try:
                # We extract the action
                action = self.extractor.extract(response)
                self._verify_llm_reponse(response, authorized_xpaths)

                action_outcome["action"] = action
                action_full += action

                # Get information to see which elements are selected
                vision_data = self.driver.get_highlighted_element(action)
                if self.display:
                    for item in vision_data:
                        display_screenshot(item["screenshot"])
                        time.sleep(0.2)

                with time_profiler("Execute Code"):
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

    def execute_instruction(self, instruction: str) -> ActionResult:
        import inspect

        code = ""
        output = None
        success = True
        logger = self.logger

        try:
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
            elif "SCAN" in instruction:
                self.driver.get_screenshots_whole_page()
                code = inspect.getsource(self.driver.get_screenshots_whole_page)
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
            else:
                raise ValueError(f"Unknown instruction: {instruction}")

        except NavigationException as e:
            success = False
            output = str(e)
            logging_print.error(f"Navigation error: {e}")

        if logger:
            log = {
                "engine": "Navigation Controls",
                "instruction": instruction,
                "engine_log": None,
                "success": success,
                "output": output,
                "code": code,
            }
            logger.add_log(log)

        self.driver.wait_for_idle()

        return ActionResult(
            instruction=instruction, code=code, success=success, output=output
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
