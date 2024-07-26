from lavague.core.token_counter import TokenCounter
from lavague.contexts.fireworks import FireworksContext
from lavague.core.context import Context

# declare the token counter before any LLMs are initialized
token_counter = TokenCounter()

# init context
context = FireworksContext()
