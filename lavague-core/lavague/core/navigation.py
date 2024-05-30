from io import BytesIO
import time
from typing import Any, List, Optional, Tuple
from lavague.core.action_template import ActionTemplate
from lavague.core.context import Context, get_default_context
from lavague.core.extractors import BaseExtractor, PythonFromMarkdownExtractor
from lavague.core.retrievers import BaseHtmlRetriever, OpsmSplitRetriever
from lavague.core.utilities.web_utils import (
    display_screenshot,
    get_highlighted_element,
    sort_files_by_creation,
)
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from lavague.core.logger import AgentLogger
from llama_index.core.base.embeddings.base import BaseEmbedding
from lavague.core.base_engine import BaseEngine
from lavague.core.base_driver import BaseDriver
from llama_index.core import get_response_synthesizer, QueryBundle, PromptTemplate
from PIL import Image
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.query_engine import RetrieverQueryEngine

NAVIGATION_ENGINE_PROMPT_TEMPLATE = ActionTemplate(
    """
{driver_capability}

Here is a the next example to answer:

HTML:
{context_str}
Query: {query_str}
Completion:

""",
    PythonFromMarkdownExtractor(),
)


class NavigationEngine(BaseEngine):
    """
    NavigationEngine leverages the llm model and the embedding model to output code from the prompt and the html page.

    Args:
        driver (`BaseDriver`):
            The Web driver used to interact with the headless browser
        llm (`BaseLLM`)
            llama-index LLM that will generate the action
        embedding (`BaseEmbedding`)
            llama-index Embedding model
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
    """

    def __init__(
        self,
        driver: BaseDriver,
        llm: BaseLLM = get_default_context().llm,
        embedding: BaseEmbedding = get_default_context().embedding,
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = NAVIGATION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = NAVIGATION_ENGINE_PROMPT_TEMPLATE.extractor,
        time_between_actions: float = 1.5,
        n_attempts: int = 5,
        logger: AgentLogger = None,
        display: bool = False,
    ):
        self.driver: BaseDriver = driver
        self.llm: BaseLLM = llm
        self.embedding: BaseEmbedding = embedding
        self.retriever: BaseHtmlRetriever = retriever
        self.prompt_template: PromptTemplate = prompt_template.partial_format(
            driver_capability=driver.get_capability()
        )
        self.extractor: BaseExtractor = extractor
        self.time_between_actions = time_between_actions
        self.logger = logger
        self.n_attempts = n_attempts
        self.display = display

    @classmethod
    def from_context(
        cls,
        context: Context,
        driver: BaseDriver,
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = NAVIGATION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = NAVIGATION_ENGINE_PROMPT_TEMPLATE.extractor,
    ) -> "NavigationEngine":
        """
        Create an NavigationEngine from a context
        """
        return cls(
            driver,
            context.llm,
            context.embedding,
            retriever,
            prompt_template,
            extractor,
        )

    def _get_query_engine(self, streaming: bool = True) -> RetrieverQueryEngine:
        """
        Get the llama-index query engine

        Args:
            html: (`str`)
            streaming (`bool`)

        Return:
            `RetrieverQueryEngine`
        """

        response_synthesizer = get_response_synthesizer(
            streaming=streaming, llm=self.llm
        )

        # assemble query engine
        query_engine = RetrieverQueryEngine(
            retriever=self.retriever.to_llama_index(self.driver, self.embedding),
            response_synthesizer=response_synthesizer,
        )

        query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": self.prompt_template}
        )

        return query_engine

    def get_nodes(self, query: str) -> List[str]:
        """
        Get the nodes from the html page

        Args:
            html (`str`): The html page

        Return:
            `List[str]`: The nodes
        """
        source_nodes = self.retriever.retrieve_html(
            self.driver, self.embedding, QueryBundle(query_str=query)
        )
        source_nodes = [node.text for node in source_nodes]
        return source_nodes

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
        # TODO: Rename query to instruction to be consistent with other engines
        """
        Generate the code from a query

        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page

        Return:
            `str`: The generated code
        """
        query_engine = self._get_query_engine(streaming=False)
        response = query_engine.query(query)
        code = response.response
        return self.extractor.extract(code)

    def execute_instruction(self, instruction: str) -> Tuple[bool, Any]:
        """
        Generates code and executes it to answer the instruction

        Args:
            instruction (`str`): The instruction to perform

        Return:
            `bool`: True if the code was executed without error
            `Any`: The output of the code
        """

        # Navigation has no output

        output = None
        driver = self.driver.get_driver()

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
                local_scope = {"driver": driver}
                code_to_execute = f"""
{self.driver.import_lines}
{action}"""
                # Get information to see which elements are selected
                vision_data = get_highlighted_element(driver, action)
                if self.display:
                    for item in vision_data:
                        display_screenshot(item["screenshot"])
                        time.sleep(0.2)

                exec(code_to_execute, local_scope, local_scope)
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
                action_outcome["success"] = False
                action_outcome["error"] = str(e)

            action_outcomes.append(action_outcome)

        navigation_log["action_outcomes"] = action_outcomes

        if logger:
            log = {
                "engine": "Navigation Engine",
                "instruction": instruction,
                "engine_log": navigation_log,
                "success": success,
                "output": None,
                "code": action,
            }

            logger.add_log(log)

        return success, output


class NavigationControl(BaseEngine):
    driver: BaseDriver
    time_between_actions: float
    logger: AgentLogger

    def __init__(
        self,
        driver: BaseDriver,
        time_between_actions: float = 1.5,
        logger: AgentLogger = None,
    ) -> None:
        self.driver: BaseDriver = driver
        self.time_between_actions = time_between_actions
        self.logger = logger
        self.display = False

    def set_display(self, display: bool):
        self.display = display

    def execute_instruction(self, instruction: str):
        logger = self.logger
        # TODO: Not clean the fact that we have driver / meta_driver around. Should settle for better names
        meta_driver: BaseDriver = self.driver
        driver: WebDriver = meta_driver.get_driver()
        display_page = False

        if "SCROLL_DOWN" in instruction:
            code = (
                """driver.execute_script("window.scrollBy(0, window.innerHeight);")"""
            )
        elif "SCROLL_UP" in instruction:
            code = (
                """driver.execute_script("window.scrollBy(0, -window.innerHeight);")"""
            )
        elif "WAIT" in instruction:
            code = f"""
import time
time.sleep({self.time_between_actions})"""
        elif "BACK" in instruction:
            code = """driver.back()"""
        elif "SCAN" in instruction:
            # TODO: Should scan be in the navigation controls or in the driver?
            code = """meta_driver.get_screenshots_whole_page()"""
            display_page = True
        else:
            raise ValueError(f"Unknown instruction: {instruction}")

        local_scope = {"driver": driver, "meta_driver": meta_driver}
        exec(code, local_scope, local_scope)
        if display_page and self.display:
            try:
                scr_path = self.driver.get_current_screenshot_folder()
                lst = sort_files_by_creation(scr_path)
                for scr in lst:
                    img = Image.open(scr_path.as_posix() + "/" + scr)
                    display_screenshot(img)
                    time.sleep(0.35)
            except:
                pass
        success = True
        output = None

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

        return success, output


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
