from llama_index.core import PromptTemplate


class DefaultPromptTemplate(PromptTemplate):
    """Prompt template adapted for most models"""

    def __init__(self):
        super().__init__(
            """

{driver_capability}

HTML:
{context_str}
Query: {query_str}
Completion:

"""
        )


class GemmaPromptTemplate(PromptTemplate):
    """Modified prompt template which has shown better results with Gemma"""

    def __init__(self):
        super().__init__(
            """

{driver_capability}

HTML:
{context_str}
Query: {query_str}
Completion:
```python
# Let's proceed step by step.

"""
        )
