from llama_index.llms.openai import OpenAI
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import PromptTemplate
from ....retrievers import BaseHtmlRetriever, OpsmSplitRetriever
from ....prompt_templates import DEFAULT_PROMPT_TEMPLATE
from ....extractors import BaseExtractor, PythonFromMarkdownExtractor
from ....action_context import ActionContext
from .. import MAX_TOKENS, TEMPERATURE

class OpenaiContext:
    def from_defaults(
        llm: BaseLLM = OpenAI(max_tokens=MAX_TOKENS, temperature=TEMPERATURE),
        embedding: BaseEmbedding = OpenAIEmbedding(model="text-embedding-3-large"),
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = DEFAULT_PROMPT_TEMPLATE,
        extractor: BaseExtractor = PythonFromMarkdownExtractor(),
    ) -> ActionContext:
        return ActionContext(llm, embedding, retriever, prompt_template, extractor)