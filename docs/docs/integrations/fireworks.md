# Fireworks Context

The Fireworks Context uses models provided by the Fireworks API for the Action Engine's LLM and embedding models.

By default, it will use the open-source `llama-v3p1-70b-instruct` as the LLM & `nomic-embed-text-v1.5` as the embedding model. You can change these models for other models provided by Fireworks.

Since there are no multi-modal LLMs available through the Fireworks API with LlamaIndex, we still use the default `gpt-4o` with OpenAI as the World Model `mm_llm`.

## Pre-requisites

To use the Fireworks Context, you will first need to install the lavague `FireworksContext` package (as well as the `lavague` package if you haven't already):

```bash
pip install lavague-contexts-fireworks
```

!!! note "API keys"
    You will need to set your Fireworks API & OpenAI API keys as `FIREWORKS_API_KEY` and `OPENAI_API_KEY` environment variables respectively. You can alternatively pass your API keys to the `FireworksContext` with the `api_key` and`openai_api_key` parameters respectively.

    For guidance on setting environment variables in your environment, see [our FAQ](../get-started/FAQs.md#how-can-i-set-environment-variables).

### End-to-end example

We can then import the FireworksContext from the `lavague.contexts.fireworks` package, initialize it and pass it to our `Action Engine` using the `from_context()` initialization method.

There is no need to pass it the World Model here since this context uses the default multi-modal (World Model) model.

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.fireworks import FireworksContext

# Initialize Context
context = FireworksContext()

selenium_driver = SeleniumDriver()

# Build Action Engine and World Model from Context
action_engine = ActionEngine.from_context(context=context, driver=selenium_driver)
world_model = WorldModel()

# Build agent & run query
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/")
agent.run("What is this week's top Space of the week?")
```

## Customizing the Fireworks Context

You can change the Fireworks models used by the context by passing the name of the model you wish to use to the `llm` and `embedding` parameters respectively.

You should use the full name for your model as listed by Fireworks [here](https://fireworks.ai/models).

??? hint "Fireworks embedding models"

    Here is a list of currently available embedding models via the Fireworks API.

    Model name | Model size |
    | --- | --- |
    | nomic-ai/nomic-embed-text-v1.5 (recommended) | 137M |
    | nomic-ai/nomic-embed-text-v1 | 137M |
    | WhereIsAI/UAE-Large-V1 | 335M |
    | thenlper/gte-large | 335M |
    | thenlper/gte-base | 109M |

```py
from lavague.contexts.fireworks import FireworksContext

# Initialize Context
context = FireworksContext(llm="accounts/fireworks/models/code-llama-34b", embedding="nomic-ai/nomic-embed-text-v1")
```

> While you can also change the multi-modal used by passing the name of the model as the `mm_llm` argument, this will need to be an `OpenAI` model since LlamaIndex does not yet support multi-modal models with Fireworks.
