"""TODO: We used to have a version of this that was quite flexible and could allow for others to provide their capabilities and the Python engine could use them.
However, we have decided to simplify the Python engine to only use the LLM and Embedding from the context for the moment as the Python Engine we want is a bit complex.
We will revisit this in the future to be able to have both:
- Capabilities that can be provided by others
- State management that can allow a complex agentic workflow"""

from io import BytesIO
import time
from lavague.core.context import Context, get_default_context
from lavague.core.utilities.web_utils import display_screenshot
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.embeddings import BaseEmbedding
from lavague.core.base_driver import BaseDriver

import trafilatura
from llama_index.core import Document, VectorStoreIndex
from lavague.core.logger import AgentLogger
from lavague.core.base_engine import BaseEngine, ActionResult
from PIL import Image


class PythonEngine(BaseEngine):
    llm: BaseLLM
    embedding: BaseEmbedding
    driver: BaseDriver

    def __init__(
        self,
        driver: BaseDriver,
        llm: BaseLLM = None,
        embedding: BaseEmbedding = None,
        logger: AgentLogger = None,
    ):
        if llm is None:
            llm = get_default_context().llm
        if embedding is None:
            embedding = get_default_context().embedding
        self.llm = llm
        self.embedding = embedding
        self.driver = driver
        self.logger = logger
        self.display = False

    @classmethod
    def from_context(
        cls,
        context: Context,
    ):
        return cls(context.llm, context.embedding)

    def execute_instruction(self, instruction: str) -> ActionResult:
        logger = self.logger

        html = self.driver.get_html()
        start = time.time()
        llm = self.llm
        embedding = self.embedding

        if self.display:
            try:
                screenshot = self.driver.get_screenshot_as_png()
                screenshot = BytesIO(screenshot)
                screenshot = Image.open(screenshot)
                display_screenshot(screenshot)
            except:
                pass

        page_content = trafilatura.extract(html)

        documents = [Document(text=page_content)]

        index = VectorStoreIndex.from_documents(documents, embed_model=embedding)
        query_engine = index.as_query_engine(llm=llm)

        output = query_engine.query(instruction).response
        end = time.time()
        action_time = end - start

        success = True

        if logger:
            log = {
                "engine": "Python Engine",
                "instruction": instruction,
                "engine_log": {
                    "action_time": action_time,
                },
                "success": success,
                "output": output,
                "code": "",  # TODO add code of Python engine. Issue is that it might be harder to make it re runnable as the pipeline is more complex than just navigation.
            }

            logger.add_log(log)

        return ActionResult(
            instruction=instruction, code="", success=success, output=output
        )

    def set_display(self, display: bool):
        self.display = display
