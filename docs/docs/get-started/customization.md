# Customization

By default, LaVague uses the configuration defined in our `OpenAIContext` which uses `gpt-4o` and `text-embedding-3-small` for the LLMs and embedding models respectively. However, you can replace these models with the models of your choice.

🦙 LaVague is compatible with all LlamaIndex `llms`, `multi-modal-llms` and `embeddings` models.

> Note that performance will vary with models and LaVague will not perform adequately with all supported models. With that said, we would welcome you to try out LaVague with different models and share your findings with us on Discord!

## Built-in Contexts

A `Context` object is an object that defines the LLM, multi-modal LLM and embedding models to be used by your LaVague agent. 

We provide some built-in Contexts, so you can quickly get started with some popular models & AI providers.

You can pass a Context to the `ActionEngine` and `WorldModel` when building your agent, by initializing them using the the `from_context(my_context)` method and providing you context as the argument.

Here are the current list of built-in Contexts we provide:

| Context | Pypi package name | Default multi-modal LLM (World Model) | Default LLM (Action Engine) | Default embedding model (Action Engine) |
|----------------------|:-----------:|:-----------:|:------------:|------------:|
|  [Anthropic](../integrations/anthropic.md)   |  lavague-contexts-anthropic |  Claude 3.5 Sonnet    |    Claude 3.5 Sonnet      |    text-embedding-3-small (OpenAI)       |
|  [Azure](../integrations/azure.md)  | lavague-contexts-openai |   gpt-4o      |    No default      |    gpt-4o        | text-embedding-3-small |
|  [Fireworks](../integrations/fireworks.md)   | lavague-contexts-fireworks |   gpt-4o  (OpenAI)      |    llama-v3p1-70b-instruct      |   nomic-embed-text-v1.5        |
|  [Gemini](../integrations/gemini.md)   |  lavague-contexts-gemini |   gemini-1.5-pro-latest    |    gemini-1.5-flash-latest      |     text-embedding-004       |
|  [OpenAI](../integrations/openai.md) (default context)   | lavague-contexts-openai |    gpt-4o     |   gpt-4o       |     text-embedding-3-small      |

!!! tip "Examples"

    Click on the Context names to see end-to-end examples of how to use our Contexts with our defaults or custom models.

🤗 We welcome contributions of new integrations to our repo. See our guide on how to create and contribute a custom Context [here](../integrations/contribute.md)

## Customization on-the-fly

While Contexts are a great way to `save` a certain configuration that can then easily be re-used, it may be that you want to use models outside of our built-in Contexts and may want to quickly customize you agents on-the-fly.

There are two ways you can do this.

### Passing models to your agent

One fast way to customize your agent on-the-fly is to overwrite the default models by passing your own `mm_llm` when initializing your `WorldModel` or passing an `llm` and/or `embedding` when initializing your `ActionEngine`.

One of the advantages of this method is that you can quickly change one or two models while using the default configuration for the other model(s).

You can pass:

- an instance of a `llama-index.llms` model with the `llm` argument when initializing your `ActionEngine`
- an instance of a `llama-index.embeddings` model with the `embedding` argument when initializing your `ActionEngine`
- an instance of a `llama--ndex.multi-modal.llms` model with the `mm_llm` argument when initializing your `WorldModel`

Here you can see an end-to-end example where we replace the default `llm` and `mm_llm`:

```python
from llama_index.llms.gemini import Gemini
from llama_index.multi_modal_llms.anthropic import AnthropicMultiModal
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver


# Customize the LLM, multi-modal LLM and embedding models
llm = Gemini(model_name="models/gemini-1.5-flash-latest")
mm_llm =  AnthropicMultiModal(model="claude-3-sonnet-20240229", max_tokens=3000)

# Initialize the Selenium driver
selenium_driver = SeleniumDriver()

# Initialize a WorldModel and ActionEngine passing them your models
world_model = WorldModel(mm_llm=mm_llm)
action_engine = ActionEngine(driver=selenium_driver, llm=llm)

# Create your agent
agent = WebAgent(world_model, action_engine)

agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```

### Custom Contexts on-the-fly

Another way to customize your agent on-the-fly is to create a custom Context on-the-fly by initializing a Context with the models of your choice.

In this case, there is no default values and you will need to provide a model instance for all three expected models (`mm_llm`, `llm` and `embedding`).

Here's an example of how you can create a custom Context on-the-fly and build your agent with it:

```python
from llama_index.llms.gemini import Gemini
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.embeddings.openai import OpenAIEmbedding
from lavague.core.context import Context

llm_name = "gemini-1.5-flash-001"
mm_llm_name = "gpt-4o-mini"
embedding_name = "text-embedding-3-small"

# init models
llm = Gemini(
    model="models/" + llm_name
)  # gemini models are prefixed with "models/" in LlamaIndex
mm_llm = OpenAIMultiModal(model=mm_llm_name)
embedding = OpenAIEmbedding(model=embedding_name)

# init context
context = Context(llm, mm_llm, embedding)
```
