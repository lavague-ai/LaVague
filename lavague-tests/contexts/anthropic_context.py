from lavague.core.token_counter import TokenCounter
from lavague.contexts.anthropic import AnthropicContext

# declare the token counter before any LLMs are initialized
token_counter = TokenCounter()

# init context
context = AnthropicContext()
