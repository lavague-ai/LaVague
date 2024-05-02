from llama_index.core import PromptTemplate

DEFAULT_PROMPT_TEMPLATE = PromptTemplate('''

{driver_capability}

HTML:
{context_str}
Query: {query_str}
Completion:
''')


GEMMA_PROMPT_TEMPLATE = PromptTemplate('''

{driver_capability}

HTML:
{context_str}
Query: {query_str}
Completion:
```python
# Let's proceed step by step.

''')