from lavague.contexts.anthropic import AnthropicContext

from lavague.core.token_counter import TokenCounter

# declare the token counter before any LLMs are initialized
token_counter = TokenCounter()

# init context
context = AnthropicContext()
