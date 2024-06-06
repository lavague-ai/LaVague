from __future__ import annotations
from typing import Any, Dict
from llama_index.core import PromptTemplate
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding
from lavague.core.extractors import BaseExtractor
from lavague.core.retrievers import BaseHtmlRetriever, OpsmSplitRetriever
from lavague.core.base_driver import BaseDriver
from lavague.core.context import Context, get_default_context
from lavague.core.logger import AgentLogger
from lavague.core.base_engine import BaseEngine
from lavague.core.navigation import NAVIGATION_ENGINE_PROMPT_TEMPLATE
from lavague.core.navigation import NavigationControl, NavigationEngine
from lavague.core.python_engine import PythonEngine


class ActionEngine:
    """
    ActionEngine is a wrapper that instantiate every other engines (Navigation Engine, Python Engine, Navigation Control)

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
        navigation_engine: BaseEngine = None,
        python_engine: BaseEngine = None,
        navigation_control: BaseEngine = None,
        llm: BaseLLM = None,
        embedding: BaseEmbedding = None,
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = NAVIGATION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = NAVIGATION_ENGINE_PROMPT_TEMPLATE.extractor,
        time_between_actions: float = 1.5,
        n_attempts: int = 5,
        logger: AgentLogger = None,
    ):
        if llm is None:
            llm = get_default_context().llm

        if embedding is None:
            embedding = get_default_context().embedding

        self.driver = driver
        if navigation_engine is None:
            navigation_engine = NavigationEngine(
                driver,
                llm,
                embedding,
                retriever,
                prompt_template,
                extractor,
                time_between_actions,
                n_attempts,
                logger,
            )
        if python_engine is None:
            python_engine = PythonEngine(driver, llm, embedding)
        if navigation_control is None:
            navigation_control = NavigationControl(driver)
        self.navigation_engine = navigation_engine
        self.python_engine = python_engine
        self.navigation_control = navigation_control
        self.engines: Dict[str, BaseEngine] = {
            "Navigation Engine": self.navigation_engine,
            "Python Engine": self.python_engine,
            "Navigation Controls": self.navigation_control,
        }

    @classmethod
    def from_context(
        cls,
        context: Context,
        driver: BaseDriver,
        navigation_engine: BaseEngine = None,
        python_engine: BaseEngine = None,
        navigation_control: BaseEngine = None,
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = NAVIGATION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = NAVIGATION_ENGINE_PROMPT_TEMPLATE.extractor,
    ) -> ActionEngine:
        """
        Create an ActionEngine from a context
        """
        return cls(
            driver,
            navigation_engine,
            python_engine,
            navigation_control,
            context.llm,
            context.embedding,
            retriever,
            prompt_template,
            extractor,
        )

    def set_gradio_mode_all(self, gradio_mode: bool, image_display: Any = None):
        self.navigation_engine.set_gradio_mode(gradio_mode, image_display)
        self.python_engine.set_gradio_mode(gradio_mode, image_display)
        self.navigation_control.set_gradio_mode(gradio_mode, image_display)

    def set_display_all(self, display: bool):
        self.navigation_engine.set_display(display)
        self.python_engine.set_display(display)
        self.navigation_control.set_display(display)

    def set_logger_all(self, logger: AgentLogger):
        self.navigation_engine.set_logger(logger)
        self.python_engine.set_logger(logger)
        self.navigation_control.set_logger(logger)

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
        ret = next_engine.execute_instruction(instruction)
        return ret
