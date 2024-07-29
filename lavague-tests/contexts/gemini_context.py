from lavague.core.token_counter import TokenCounter
from lavague.contexts.gemini import GeminiContext
from lavague.core.context import Context
from llama_index.multi_modal_llms.gemini import GeminiMultiModal

# declare the token counter before any LLMs are initialized
token_counter = TokenCounter()

# init context
context = GeminiContext()
