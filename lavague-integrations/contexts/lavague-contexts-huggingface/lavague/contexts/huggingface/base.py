from llama_index.core import PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from lavague.core import BaseHtmlRetriever, OpsmSplitRetriever
from lavague.core.prompt_templates import GemmaPromptTemplate
from lavague.core.extractors import BaseExtractor, UntilEndOfMarkdownExtractor
from lavague.core import Context
from lavague.llms.huggingface import ActionHuggingFaceLLM


class HuggingfaceContext:
    def from_defaults(
        llm: str = "deepseek-ai/deepseek-coder-6.7b-instruct",
        embedding: str = "BAAI/bge-small-en-v1.5",
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = GemmaPromptTemplate(),
        extractor: BaseExtractor = UntilEndOfMarkdownExtractor(),
    ) -> Context:
        return Context(
            ActionHuggingFaceLLM(llm),
            HuggingFaceEmbedding(model_name=embedding, device="cuda"),
            embedding,
            retriever,
            prompt_template,
            extractor,
        )
