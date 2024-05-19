from llama_index.core import PromptTemplate
from typing import Optional
from lavague.core import Context, get_default_context
from llama_index.core.base.llms.base import BaseLLM
import copy

PYTHON_ENGINE_PROMPT_TEMPLATE = PromptTemplate("""
You are an AI system specialized in Python code generation to answer user queries.
The inputs are: an instruction, and the current state of the local variables available to the environment where your code will be executed.
Your output is the code that will perform the action described in the instruction, using the variables available in the environment.
You can import libraries and use any variables available in the environment.
Detail thoroughly the steps to perform the action in the code you generate with comments.
The last line of your code should be an assignment to the variable 'output' containing the result of the action.

Here are previous examples:
{examples}

Instruction: {instruction}
State:
{state_description}
Code:
""")

class PythonEngine:
    llm: BaseLLM    
    prompt_template: PromptTemplate

    def __init__(self, examples: str, context: Optional[Context] = None):
        if context is None:
            context = get_default_context()
        self.llm = context.llm
        self.extractor = context.extractor
        self.prompt_template = PYTHON_ENGINE_PROMPT_TEMPLATE.partial_format(
            examples=examples
        )
        
    def generate_code(self, instruction: str, state: dict) -> str:
        state_description = self.get_state_description(state)
        prompt = self.prompt_template.format(instruction=instruction, state_description=state_description)
        response = self.llm.complete(prompt).text
        return response
    
    def execute_code(self, code: str, state: dict):
        local_scope = copy.deepcopy(state)
        exec(code, local_scope, local_scope)
        output = local_scope["output"]
        return output
        
    def get_state_description(self, state: dict) -> str:
        """TO DO: provide more complex state descriptions"""
        state_description = """
    html ('str'): The content of the HTML page being analyzed"""
        return state_description
        
    
REWRITER_PROMPT_TEMPLATE = PromptTemplate("""
You are an AI expert.
You are given a high level instruction on a generic action to perform.
Your output is an instruction of the action, rewritten to be more specific on the capabilities at your disposal to perform the action.
Here are your capabilities:
{capabilities}

Here are previous examples:
{examples}

Here is the next instruction to rewrite:
Original instruction: {original_instruction}
""")

DEFAULT_CAPABILITIES = """
- Answer questions using the content of an HTML page using llama index and trafilatura
"""

DEFAULT_EXAMPLES = """
Original instruction: Use the content of the HTML page to answer the question 'How was falcon-11B trained?'
Capability: Answer questions using the content of an HTML page using llama index and trafilatura
Rewritten instruction: Extract the content of the HTML page and use llama index to answer the question 'How was falcon-11B trained?'
"""

class Rewriter:
    def __init__(self, capabilities: str = DEFAULT_CAPABILITIES, examples: str = DEFAULT_EXAMPLES, context: Optional[Context] = None):
        if context is None:
            context = get_default_context()
        self.llm = context.llm
        self.prompt_template = REWRITER_PROMPT_TEMPLATE.partial_format(
            capabilities=capabilities,
            examples=examples
        )      
    def rewrite_instruction(self, original_instruction: str) -> str:
        prompt = self.prompt_template.format(original_instruction=original_instruction)
        rewritten_instruction = self.llm.complete(prompt=prompt).text
        return rewritten_instruction