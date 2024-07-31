# Contexts

Contexts are `python` files responsible for initializing the models used by the `lavague-tests` module. 

They need to contain two things: 
- a `token_counter` object
- a `context` object

## Usage

Run `lavague-tests -c path_to_your_custom_context.py` to run tests with the context you created. 

## Examples

### Default context
```python
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
```

### Custom context
```python
from lavague.core.token_counter import TokenCounter
from llama_index.llms.gemini import Gemini
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.embeddings.openai import OpenAIEmbedding
from lavague.core.context import Context

llm_name = "gemini-1.5-flash-001"
mm_llm_name = "gpt-4o-mini"
embedding_name = "text-embedding-3-small"

token_counter = TokenCounter()

# init models
llm = Gemini(
    model="models/" + llm_name
)  # gemini models are prefixed with "models/" in LlamaIndex
mm_llm = OpenAIMultiModal(model=mm_llm_name)
embedding = OpenAIEmbedding(model=embedding_name)

# init context
context = Context(llm, mm_llm, embedding)
```
