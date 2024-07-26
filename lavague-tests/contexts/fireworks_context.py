from lavague.core.token_counter import TokenCounter
from lavague.contexts.fireworks import FireworksContext
from lavague.core.context import Context

# declare the token counter before any LLMs are initialized
token_counter = TokenCounter()

# init context
fireworks_context = FireworksContext()
context = Context(
    fireworks_context.llm, fireworks_context.mm_llm, fireworks_context.embedding
)
