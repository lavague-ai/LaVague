# Cache for LLM, Multimodal LLM and embeddings


## Overview

LaVague Context Cache is a caching layer designed for Language Models, Multimodal Language Models and embeddings.
It ensures deterministic results, avoids unnecessary token consumption, and speeds up local development by caching responses and embeddings.

This tool is ideal for:
- Developers seeking to streamline their workflow when working with models.
- Builders aiming to reduce model costs and enhance performance when agent objectives are stable.

Key features:
- Guarantees consistent results in both automated and manual testing by caching previous responses
- Reduces API token consumption by reusing cached results, avoiding redundant API calls
- Speeds up local development by eliminating the need to repeatedly query the same results
- Cached scenario can be replayed offline


## Installation

### From pypi

```bash
pip install lavague-contexts-cache
```

### From the sources
```bash
pip install -e lavague-integrations/contexts/lavague-contexts-cache
```


## Usage

### Using wrappers

```python
from lavague.contexts.cache import LLMCache
from llama_index.llms.openai import OpenAI

llm = LLMCache(yml_prompts_file="llm.yml", fallback=OpenAI(model = "gpt-4o"))
```

```python
from lavague.contexts.cache import MultiModalLLMCache
from llama_index.multi_modal_llms.openai import OpenAIMultiModal

mm_llm = MultiModalLLMCache(yml_prompts_file="mmllm.yml", fallback=OpenAIMultiModal(model = "gpt-4o"))
```

```python
from lavague.contexts.cache import EmbeddingCache
from llama_index.embeddings.openai import OpenAIEmbedding

embedding = EmbeddingCache(yml_prompts_file="embeddings.yml", fallback=OpenAIEmbedding(model = "text-embedding-3-large"))
```

### Using LaVague context

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.core.context import get_default_context
from lavague.contexts.cache import ContextCache

driver = SeleniumDriver()
context = get_default_context()
cached_context = ContextCache.from_context(context)
world_model = WorldModel.from_context(cached_context)
action_engine = ActionEngine.from_context(cached_context, driver)
agent = WebAgent(world_model, action_engine)
```


## Performance

Cached values are stored in YAML files and loaded into memory by default.
While this approach works well for a few runs, it can consume excessive memory when applied to various websites.
For production use cases, we recommend using an optimized storage system (database, cache, ...).

To do so, pass a `store` that implements abstract `PromptsStore` methods.

```python
from lavague.contexts.cache import LLMCache
from lavague.contexts.cache.prompts_store import PromptsStore
from llama_index.llms.openai import OpenAI

class MyDataBaseStore(PromptsStore[str]):
  def _get_for_prompt(self, prompt: str) -> str:
    # return from DB with prompt key
    pass

  def _add_prompt(self, prompt: str, output: str):
    # store in DB
    pass

my_database_store = MyDataBaseStore()

llm = LLMCache(yml_prompts_file="llm.yml", fallback=OpenAI(model = "gpt-4o"), store=store)
```