from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core import PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from lavague.core import BaseHtmlRetriever, OpsmSplitRetriever
from lavague.core.prompt_templates import GemmaPromptTemplate
from lavague.core.extractors import BaseExtractor, UntilEndOfMarkdownExtractor
from lavague.core import ActionContext
from lavague.llms.huggingface import ActionHuggingFaceLLM

class HuggingfaceContext:
    def from_defaults(
        llm: BaseLLM = ActionHuggingFaceLLM(),
        embedding: BaseEmbedding = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5", device="cuda"),
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = GemmaPromptTemplate(),
        extractor: BaseExtractor = UntilEndOfMarkdownExtractor(),
    ) -> ActionContext:
        return ActionContext(llm, embedding, retriever, prompt_template, extractor)
