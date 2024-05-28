from __future__ import annotations
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any, Dict, Optional, Generator, List, Tuple
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer, QueryBundle, PromptTemplate
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding
from lavague.core.extractors import BaseExtractor, PythonFromMarkdownExtractor
from lavague.core.retrievers import BaseHtmlRetriever, OpsmSplitRetriever
from lavague.core.base_driver import BaseDriver
from lavague.core.action_template import ActionTemplate
from lavague.core.context import Context, get_default_context
import time
from PIL import Image
from lavague.core.logger import AgentLogger, Loggable
from lavague.core.utilities.web_utils import (
    display_screenshot,
    get_highlighted_element,
    sort_files_by_creation,
)

ACTION_ENGINE_PROMPT_TEMPLATE = ActionTemplate(
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


class BaseActionEngine(ABC, Loggable):
    @abstractmethod
    def execute_instruction(self, instruction: str) -> Tuple[bool, Any]:
        pass


class ActionEngine(BaseActionEngine):
    """
    ActionEngine leverages the llm model and the embedding model to output code from the prompt and the html page.

    Args:
        driver (`BaseDriver`):
            The Web driver used to interact with the headless browser
        python_engine (`BaseActionEngine`)
            Python Engine for generating code that doesn't interact with an html page.
        navigation_control (`BaseActionEngine`)
            Navigation Control
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
        python_engine: "BaseActionEngine" = None,
        navigation_control: "BaseActionEngine" = None,
        llm: BaseLLM = get_default_context().llm,
        embedding: BaseEmbedding = get_default_context().embedding,
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = ACTION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = ACTION_ENGINE_PROMPT_TEMPLATE.extractor,
        time_between_actions: float = 1.5,
        n_attempts: int = 5,
        logger: AgentLogger = None,
        display: bool = False,
    ):
        from lavague.core.navigation import NavigationControl
        from lavague.core.python_engine import PythonEngine

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
        if python_engine is None:
            python_engine = PythonEngine(self.driver, llm, embedding)
        if navigation_control is None:
            navigation_control = NavigationControl(self.driver)
        self.python_engine = python_engine
        self.navigation_control = navigation_control
        self.engines: Dict[str, BaseActionEngine] = {
            "Navigation Engine": self,
            "Python Engine": self.python_engine,
            "Navigation Controls": self.navigation_control,
        }
        self.display = display

    @classmethod
    def from_context(
        cls,
        context: Context,
        driver: BaseDriver,
        python_engine: BaseActionEngine = None,
        navigation_control: BaseActionEngine = None,
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = ACTION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = ACTION_ENGINE_PROMPT_TEMPLATE.extractor,
    ) -> ActionEngine:
        """
        Create an ActionEngine from a context
        """
        return cls(
            driver,
            python_engine,
            navigation_control,
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

    def set_logger_all(self, logger: AgentLogger):
        self.set_logger(logger)
        self.python_engine.set_logger(logger)
        self.navigation_control.set_logger(logger)

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

    def dispatch_instruction(self, next_engine_name: str, instruction: str):
        """
        Dispatch the instruction to the appropriate ActionEngine

        Args:
            next_engine_name (`str`): The name of the engine to call
            instruction (`str`): The instruction to perform

        Return:
            `bool`: True if the code was executed without error
            `Any`: The output of the code
        """

        next_engine = self.engines[next_engine_name]
        return next_engine.execute_instruction(instruction)

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
