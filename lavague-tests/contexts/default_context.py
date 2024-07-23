from lavague.core.token_counter import TokenCounter
from llama_index.llms.openai import OpenAI
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.embeddings.openai import OpenAIEmbedding
from lavague.core.context import Context

llm_name = "gpt-4o"
mm_llm_name = "gpt-4o"
embedding_name = "text-embedding-3-large"

# declare the token counter before any LLMs are initialized
token_counter = TokenCounter()

# init models
llm = OpenAI(model=llm_name)
mm_llm = OpenAIMultiModal(model=llm_name)
embedding = OpenAIEmbedding(model=embedding_name)

# init context
context = Context(llm, mm_llm, embedding)
