from llama_index.llms.groq import Groq
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import PromptTemplate
from lavague.core import BaseHtmlRetriever, OpsmSplitRetriever
from lavague.core import DefaultPromptTemplate
from lavague.core import BaseExtractor, PythonFromMarkdownExtractor
from lavague.core import Context
from lavague.core.context import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE


class GroqContext:
    def from_defaults(
        llm: str = "llama3-70b-8192",
        embedding: BaseEmbedding = OpenAIEmbedding(model="text-embedding-3-large"),
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = DefaultPromptTemplate(),
        extractor: BaseExtractor = PythonFromMarkdownExtractor(),
    ) -> Context:
        return Context(
            Groq(
                model=llm,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
            ),
            embedding,
            retriever,
            prompt_template,
            extractor,
        )
