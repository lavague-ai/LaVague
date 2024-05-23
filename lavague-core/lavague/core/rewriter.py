from typing import Optional
from lavague.core import Context, get_default_context
from llama_index.core import PromptTemplate

REWRITER_DEFAULT_CAPABILITIES = """
- Answer questions using the content of an HTML page using llama index and trafilatura
"""

REWRITER_DEFAULT_EXAMPLES = """
Original instruction: Use the content of the HTML page to answer the question 'How was falcon-11B trained?'
Capability: Answer questions using the content of an HTML page using llama index and trafilatura
Rewritten instruction: Extract the content of the HTML page and use llama index to answer the question 'How was falcon-11B trained?'
"""

REWRITER_PROMPT_TEMPLATE = PromptTemplate(
    """
You are an AI expert.
You are given a high level instruction on a generic action to perform.
Your output is an instruction of the action, rewritten to be more specific on the capabilities at your disposal to perform the action.
Here are your capabilities:
{capabilities}

Here are previous examples:
{examples}

Here is the next instruction to rewrite:
Original instruction: {original_instruction}
"""
)


class Rewriter:
    def __init__(
        self,
        capabilities: str = REWRITER_DEFAULT_CAPABILITIES,
        examples: str = REWRITER_DEFAULT_EXAMPLES,
        context: Optional[Context] = None,
    ):
        if context is None:
            context = get_default_context()
        self.llm = context.llm
        self.prompt_template = REWRITER_PROMPT_TEMPLATE.partial_format(
            capabilities=capabilities, examples=examples
        )

    def rewrite_instruction(self, original_instruction: str) -> str:
        prompt = self.prompt_template.format(original_instruction=original_instruction)
        rewritten_instruction = self.llm.complete(prompt).text
        return rewritten_instruction
