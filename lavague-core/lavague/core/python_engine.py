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
from lavague.core.action_engine import BaseActionEngine
from PIL import Image


class PythonEngine(BaseActionEngine):
    llm: BaseLLM
    embedding: BaseEmbedding
    # TODO: Design question: should we have a driver available to Python engine?
    driver: BaseDriver

    def __init__(
        self,
        driver: BaseDriver,
        llm: BaseLLM = get_default_context().llm,
        embedding: BaseEmbedding = get_default_context().embedding,
        logger: AgentLogger = None,
    ):
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

    def execute_instruction(self, instruction: str):
        logger = self.logger

        html = self.driver.get_html()
        start = time.time()
        output = self.extract_information(instruction, html)
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

        return success, output

    def set_display(self, display: bool):
        self.display = display

    def extract_information(self, instruction: str, html: str) -> str:
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
        # Next we will use Llama Index to perform RAG on the extracted text content

        documents = [Document(text=page_content)]

        # We then build index
        index = VectorStoreIndex.from_documents(documents, embed_model=embedding)
        query_engine = index.as_query_engine(llm=llm)

        # We finally store the output in the variable 'output'
        output = query_engine.query(instruction).response

        return output
