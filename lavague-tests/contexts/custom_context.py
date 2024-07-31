from lavague.core.token_counter import TokenCounter
from llama_index.llms.gemini import Gemini
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.embeddings.openai import OpenAIEmbedding
from lavague.core.context import Context

llm_name = "gemini-1.5-flash-001"
mm_llm_name = "gpt-4o-mini"
embedding_name = "text-embedding-3-small"

token_counter = TokenCounter()

# init models
llm = Gemini(
    model="models/" + llm_name
)  # gemini models are prefixed with "models/" in LlamaIndex
mm_llm = OpenAIMultiModal(model=mm_llm_name)
embedding = OpenAIEmbedding(model=embedding_name)

# init context
context = Context(llm, mm_llm, embedding)
