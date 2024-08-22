import json
import shutil
import time
from io import BytesIO
from typing import Callable, Optional
from pathlib import Path

from PIL import Image
import trafilatura


from lavague.core.context import Context, get_default_context
from lavague.core.utilities.web_utils import display_screenshot
from lavague.core.base_driver import BaseDriver
from lavague.core.logger import AgentLogger
from lavague.core.base_engine import BaseEngine, ActionResult

from llama_index.legacy.readers.file.base import SimpleDirectoryReader
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.embeddings import BaseEmbedding
import re

DEFAULT_TEMPERATURE = 0.0


class PythonEngine(BaseEngine):
    """
    The PythonEngine is responsible for knowledge retrieval, it extracts information from the webpage and performs RAG to complete the given instruction
    """

    driver: BaseDriver
    llm: BaseLLM
    embedding: BaseEmbedding
    logger: AgentLogger
    clean_html: Callable[[str], str]
    ocr_mm_llm: BaseLLM
    ocr_llm: BaseLLM
    batch_size: int
    confidence_threshold: float
    temp_screenshots_path: str
    n_search_attempts: int

    def __init__(
        self,
        driver: BaseDriver,
        llm: Optional[BaseLLM] = None,
        embedding: Optional[BaseEmbedding] = None,
        logger: Optional[AgentLogger] = None,
        clean_html: Callable[[str], str] = trafilatura.extract,
        ocr_mm_llm: Optional[BaseLLM] = None,
        ocr_llm: Optional[BaseLLM] = None,
        display: bool = False,
        batch_size: int = 5,
        confidence_threshold: float = 0.85,
        temp_screenshots_path="./tmp_screenshots",
        n_search_attemps=10,
    ):
        self.llm = llm or get_default_context().llm
        self.embedding = embedding or get_default_context().embedding
        self.clean_html = clean_html
        self.driver = driver
        self.logger = logger
        self.display = display
        self.ocr_mm_llm = ocr_mm_llm or OpenAIMultiModal(
            model="gpt-4o-mini", temperature=DEFAULT_TEMPERATURE
        )
        self.ocr_llm = ocr_llm or self.llm
        self.batch_size = batch_size
        self.confidence_threshold = confidence_threshold
        self.temp_screenshots_path = temp_screenshots_path
        self.n_search_attempts = n_search_attemps

    @classmethod
    def from_context(cls, context: Context, driver: BaseDriver):
        return cls(llm=context.llm, embedding=context.embedding, driver=driver)

    def extract_json(self, output: str) -> Optional[dict]:
        clean = (
            output.replace("'ret'", '"ret"')
            .replace("'score'", '"score"')
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )
        clean = re.sub(r"\n+", "\n", clean)
        try:
            output_dict = json.loads(clean)
        except json.JSONDecodeError as e:
            print(f"Error extracting JSON: {e}")
            return None
        return output_dict

    def get_screenshots_batch(self) -> list[str]:
        screenshot_paths = []
        logging_screenshot_path = self.driver.get_current_screenshot_folder()

        for i in range(self.batch_size):
            screenshot_path = self.driver.save_screenshot(
                Path(self.temp_screenshots_path)
            )
            screenshot_paths.append(screenshot_path)

            if self.display:
                self.display_screenshot()

            # copy image from temp Simple Directory folder to logging folder
            shutil.copy(Path(screenshot_path), logging_screenshot_path)

            self.driver.scroll_down()
            self.driver.wait_for_idle()

            if self.driver.is_bottom_of_page():
                break

        return screenshot_paths

    def perform_fallback(self, prompt, instruction) -> str:
        memory = ""
        context_score = -1

        prompt = f"""
        You must respond with a dictionary in the following format:
        {{
            "ret": "[any relevant text transcribed from the image in order to answer the query {instruction} - make sure to answer with full sentences so the reponse can be understood out of context.]",
            "score": [a confidence score between 0 and 1 that the necessary context has been captured in order to answer the following query]
        }}
        If you believe the transcription is incomplete or lacks context, adjust the 'score' accordingly.

        When setting the score value - you can also take into account the following additional information from previous transcriptions {memory}
        """

        for i in range(self.n_search_attempts):
            if context_score >= self.confidence_threshold:
                break
            if self.driver.is_bottom_of_page():
                return "We did not find sufficient context on this webpage to provide the information asked for"

            screenshot_folder = Path(self.temp_screenshots_path)
            if screenshot_folder == self.driver.get_current_screenshot_folder():
                raise ValueError(
                    "Temporary Python Engine screenshot folder must not be the same as the LaVague default screenshot folder"
                )
            if screenshot_folder.exists():
                shutil.rmtree(screenshot_folder)

            screenshot_folder.mkdir(parents=True, exist_ok=True)
            self.get_screenshots_batch()
            screenshots = SimpleDirectoryReader(screenshot_folder).load_data()
            output = self.ocr_mm_llm.complete(
                image_documents=screenshots, prompt=prompt
            ).text.strip()
            output_dict = self.extract_json(output)
            context_score = output_dict.get("score")
            output = output_dict.get("ret")
            memory += output

            # delete temp image folder
            shutil.rmtree(Path(self.temp_screenshots_path))

        if context_score >= self.confidence_threshold:
            summary_prompt = f"Phrase this answer or relevant information {output} to answer this {instruction}."
            output = self.ocr_llm.complete(summary_prompt).text
        else:
            output = "Unable to find relevant information on this page"
        return output

    def display_screenshot(self) -> None:
        try:
            screenshot = self.driver.get_screenshot_as_png()
            screenshot = BytesIO(screenshot)
            screenshot = Image.open(screenshot)
            display_screenshot(screenshot)
        except Exception as e:
            print(f"Error displaying screenshot: {e}")
            pass

    def execute_instruction(self, instruction: str) -> ActionResult:
        logger = self.logger

        html = self.driver.get_html()
        start = time.time()
        llm = self.llm
        embedding = self.embedding

        if self.display:
            self.display_screenshot()

        page_content = self.clean_html(html)
        documents = [Document(text=page_content)]

        index = VectorStoreIndex.from_documents(documents, embed_model=embedding)
        query_engine = index.as_query_engine(llm=llm)

        prompt = f"""
        Based on the context provided, you must respond to query with a JSON object in the following format:
        {{
            "ret": "[your answer]",
            "score": [a float value between 0 and 1 on your confidence that you have enough context to answer the question]
        }}
        If you do not have sufficient context, set 'ret' to 'Insufficient context' and 'score' to 0.
        The query is: {instruction}
        """

        output = query_engine.query(prompt).response.strip()
        output_dict = self.extract_json(output)

        try:
            if (
                output_dict.get("score", 0) < self.confidence_threshold
            ):  # use fallback method
                output = self.perform_fallback(prompt=prompt, instruction=instruction)

            else:  # original navigatin engine method
                output = output_dict.get("ret")
        except (SyntaxError, ValueError) as e:
            print("Error parsing the output:", e)

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
                "code": "",
            }

            logger.add_log(log)

        return ActionResult(
            instruction=instruction, code="", success=success, output=output
        )

    def set_display(self, display: bool):
        self.display = display
