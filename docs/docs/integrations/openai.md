# OpenAI Context

The OpenaiContext is our default configuration for LaVague. It uses OpenAI's `gpt-4o` by default as LaVague's multi-modal `mm_llm` and ActionEngine LLM models, and OpenAI's `text-embedding-3-small` model as the embedding model. You can swap these models to other OpenAI models as we explain below.

## Pre-requisites

The OpenaiContext is installed by default with `LaVague`.

!!! note "API keys"
    You will need to set your OpenAI API keys as an `OPENAI_API_KEY` environment variable. 
    
    You can also pass your API keys to the `OpenaiContext` using the `api_key` parameters if initializing an `OpenaiContext` object directly.

    For guidance on setting environment variables in your environment, see [our FAQ](../get-started/FAQs.md#how-can-i-set-environment-variables).

## Default usage

Since the OpenaiContext is used by default, there is no need to initialize or pass this context unless you wish to customize it.

## Customizing the OpenaiContext

You can change the Openai models used by the context by initializing an `OpenaiContext` object and passing the name of the model(s) you wish to use to the `llm`, `mm_llm` and/or `embedding` parameters respectively.

You can find a list of OpenAI models currently available and their names [here](https://platform.openai.com/docs/models).

```py
from lavague.contexts.openai import OpenaiContext

# Initialize Context
context = OpenaiContext(llm="gpt-4o-mini", mm_llm="gpt-4o-mini")
```
Once we have defined our OpenaiContext, we can use it by passing it to our ActionEngine and WorldModel when initializing them with the `from_context()` method.

```python
selenium_driver = SeleniumDriver()

# Build Action Engine and World Model from Context
action_engine = ActionEngine.from_context(context=context, driver=selenium_driver)
world_model = WorldModel.from_context(context)

# Build agent & run query
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/")
agent.run("What is this week's top Space of the week?")
```