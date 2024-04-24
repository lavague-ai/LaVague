from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from ...driver import BaseDriver
from ..drivers.playwright import PlaywrightDriver
from ..llms.apis.openai_api import OpenAIForAction
from ...retrievers import BaseHtmlRetriever, OpsmSplitRetriever
from ...prompt_templates import PLAYWRIGHT_PROMPT_TEMPLATE
from ...extractors import BaseExtractor, PythonFromMarkdownExtractor
from ...action_context import ActionContext

class PlaywrightContext:
    def from_defaults(
        driver: BaseDriver = PlaywrightDriver(),
        llm: BaseLLM = OpenAIForAction(),
        embedding: BaseEmbedding = OpenAIEmbedding(model="text-embedding-3-large"),
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: str = PLAYWRIGHT_PROMPT_TEMPLATE,
        extractor: BaseExtractor = PythonFromMarkdownExtractor(),
    ) -> ActionContext:
        return ActionContext(driver, llm, embedding, retriever, prompt_template, extractor)