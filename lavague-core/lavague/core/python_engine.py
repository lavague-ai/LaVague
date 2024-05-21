from llama_index.core import PromptTemplate
from lavague.core.context import Context, get_default_context
from llama_index.core.base.llms.base import BaseLLM
import copy
from lavague.core.action_template import ActionTemplate
from lavague.core.extractors import PythonFromMarkdownExtractor, BaseExtractor

PYTHON_ENGINE_EXAMPLES = """
Capability: Answer questions using the content of an HTML page
Instruction: Extract the content of the HTML page and do a call to OpenAI GPT-3.5 turbo to answer the question 'How was falcon-11B trained?'
State:
    html ('str'): The content of the HTML page being analyzed
Code:
# Let's think step by step
# We first need to extract the text content of the HTML page. 
# Then we will use an LLM to answer the question. Because the page content might not fit in the LLM context window, we will use Llama Index to perform RAG on the extracted text content.

# First, We use the trafilatura library to extract the text content of the HTML page
import trafilatura

page_content = trafilatura.extract(html)

# Next we will use Llama Index to perform RAG on the extracted text content
from llama_index.core import Document, VectorStoreIndex

documents = [Document(text=page_content)]

# We then build index
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

# We will use the query engine to answer the question
instruction = "How was falcon-11B trained?"

# We finally store the output in the variable 'output'
output = query_engine.query(instruction).response
"""

PYTHON_ENGINE_ACTION_TEMPLATE = ActionTemplate(
    """
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
""",
    PythonFromMarkdownExtractor(),
)


class PythonEngine:
    """
    This engine generates python code which doesn't interactor with a web driver, and doesn't require RAG over an html page
    """

    def __init__(
        self,
        llm: BaseLLM = get_default_context().llm,
        prompt_template: PromptTemplate = PYTHON_ENGINE_ACTION_TEMPLATE.prompt_template,
        examples: str = PYTHON_ENGINE_EXAMPLES,
        extractor: BaseExtractor = PYTHON_ENGINE_ACTION_TEMPLATE.extractor,
    ):
        self.llm: BaseLLM = llm
        self.extractor: PromptTemplate = extractor
        self.prompt_template = prompt_template.partial_format(examples=examples)

    @classmethod
    def from_context(
        cls,
        context: Context,
        prompt_template: PromptTemplate = PYTHON_ENGINE_ACTION_TEMPLATE.prompt_template,
        examples: str = PYTHON_ENGINE_EXAMPLES,
        extractor: BaseExtractor = PYTHON_ENGINE_ACTION_TEMPLATE.extractor,
    ):
        return cls(context.llm, prompt_template, examples, extractor)

    def generate_code(self, instruction: str, state: dict) -> str:
        state_description = self.get_state_description(state)
        prompt = self.prompt_template.format(
            instruction=instruction, state_description=state_description
        )
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
