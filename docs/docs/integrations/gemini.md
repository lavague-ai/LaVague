# Gemini Context

The GeminiContext uses Google's Gemini models for LaVague's World Model multi-modal LLM, Action Engine LLM and embedding model.

By default, we use `gemini-1.5-flash-latest` as the Action Engine LLM model, `gemini-1.5-pro-latest` as the multi-modal `mm_llm` and `text-embedding-004` as the embedding model. You can swap these models to other Gemini models as we explain below.

## Pre-requisites

To use the Gemini Context, you will first need to install the lavague `GeminiContext` package (as well as the `lavague` package if you haven't already):

```bash
pip install lavague-contexts-gemini
```

!!! note "API keys"
    You will need to set your Google API keys as a `GOOGLE_API_KEY` environment variable. You can alternatively pass your API keys to the `GeminiContext` using the `api_key` parameters.

    For guidance on setting environment variables in your environment, see [our FAQ](../get-started/FAQs.md#how-can-i-set-environment-variables).

### End-to-end example

We can then import the GeminiContext from the `lavague.contexts.gemini` package, initialize it and pass it to our `ActionEngine` and `WorldModel` using their `from_context()` initialization method.

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.gemini import GeminiContext

# Initialize Context
context = GeminiContext()

selenium_driver = SeleniumDriver()

# Build Action Engine and World Model from Context
action_engine = ActionEngine.from_context(context=context, driver=selenium_driver)
world_model = WorldModel.from_context(context)

# Build agent & run query
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/")
agent.run("What is this week's top Space of the week?")
```

## Customizing the Gemini Context

You can change the Gemini models used by the context by passing the name of the model you wish to use to the `llm`, `mm_llm` and `embedding` parameters respectively.

You can find a list of Gemini models currently available and their names [here](https://ai.google.dev/gemini-api/docs/models/gemini).

```py
from lavague.contexts.gemini import GeminiContext

# Initialize Context
context = GeminiContext(llm="gemini-1.5-pro", mm_llm="gemini-1.5-flash")
```
