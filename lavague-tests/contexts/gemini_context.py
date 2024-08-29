from lavague.contexts.gemini import GeminiContext
from llama_index.multi_modal_llms.gemini import GeminiMultiModal

from lavague.core.context import Context
from lavague.core.token_counter import TokenCounter

# declare the token counter before any LLMs are initialized
token_counter = TokenCounter()

# init context
context = GeminiContext()
