# Anthropic Context

The Anthropic Context uses Anthropic models for the Action Engine's LLM and World Model's multi-modal models.

By default, it will use Claude 3.5 Sonnet for both these models. You can change these models for other models provided by Anthropic available via LlamaIndex.

Since Anthropic doesn't currently provide its own embedding models, we still use the default `text-embedding-3-small` with OpenAI for embedding.

## Pre-requisites

To use the Anthropic Context, you will first need to install the lavague `AnthropicContext` package (as well as the `lavague` package if you haven't already):

```bash
pip install lavague-contexts-anthropic
```

!!! note "API keys"
    You will need to either set your Anthropic API & OpenAI API keys as `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` environment variables respectively. You can alternatively pass your API keys to the `AnthropicContext` using the `api_key` and `openai_api_key` parameters respectively.

    For guidance on setting environment variables in your environment, see [our FAQ](../get-started/FAQs.md#how-can-i-set-environment-variables).

### End-to-end example

We can then import the AnthropicContext from the `lavague.contexts.anthropic` package, initialize it and pass it to our `Action Engine` and `WorldModel` using their `from_context()` initialization method.

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.anthropic import AnthropicContext

# Initialize Context
context = AnthropicContext()

selenium_driver = SeleniumDriver()

# Build Action Engine and World Model from Context
action_engine = ActionEngine.from_context(context=context, driver=selenium_driver)
world_model = WorldModel.from_context(context)

# Build agent & run query
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/")
agent.run("What is this week's top Space of the week?")
```

## Customizing the Anthropic Context

You can change the Anthropic models used by the context by passing the name of the model you wish to use to the `llm` and `mm_llm` parameters respectively.

You can find a list of Anthropic models currently available and their names [here](https://docs.anthropic.com/en/docs/about-claude/models).

```py
from lavague.contexts.anthropic import AnthropicContext

# Initialize Context
context = AnthropicContext(llm="claude-3-opus-20240229", mm_llm="claude-3-sonnet-20240229")
```

> You can also change the embedding model used by passing the name of the model as the `embedding` argument. However, this will need to be a `OpenAI` embedding model.