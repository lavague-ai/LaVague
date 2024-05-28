# Customizing your Agent

When using our Web Agents, you can customize the LLM (`llm`), multi-modal LLM (`mm_llm`) and embedding model (`embedding`).

These are attributes of a `Context` object, which can be optionally passed to the `Action Engine` and `World Model` using their `from_context()` initializing methods. The `Action Engine` and `World Model` are then in turn are passed to the `Web Agent`.

!!! info "Modifiable elements"

    - **llm**: The `LLM` used by the `Action Engine` to translate text instructions into automation code. You can set the `llm` to any `LlamaIndex LLM object`.

    - **mm_llm**: The `multi-modal LLM` used by the `World Model` to generate the next instruction to be enacted by the Action Engine based on the current state of the web page. You can set the `mm_llm` argument to any `LlamaIndex multi-modal LLM object`.

    - **embedding**: The `embedding model` is used by the `retriever` to convert segments of the HTML page of the target website into vectors, capturing semantic meaning. You can set this to any `LlamaIndex Embedding object`. 

These elements are initialized in a `Context` object, which can optionally passed to both the `Action Engine` and `World Model` used by an Agent. If you don't pass them your own Context object, the default OpenaiContext will be used.

!!! abstract "Default Configuration"

    The default configuration is as follows:

    - `llm`: OpenAI's gpt-3.5-turbo,
    - `mm_llm`: OpenAi's gpt-4o,
    - `embedding`: text-embedding-3-large,

## Customization an existing Context

Let's take a look at how we can modify specific elements of an existing built-in Context.

#### Example: Modifying a built in context

```python
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.contexts.openai import OpenaiContext
from lavague.drivers.selenium import SeleniumDriver

# Initialize the default context
context = OpenaiContext()

# Customizing the LLM, multi-modal LLM and embedding models
context.llm = Gemini(model_name="models/gemini-1.5-flash-latest")
context.mm_llm =  OpenAIMultiModal(model="gpt-4o", temperature=0.0)
context.embedding = GeminiEmbedding(model_name="models/text-embedding-004")

# Initialize the Selenium driver
selenium_driver = SeleniumDriver()

# Initialize the WorldModel and ActionEngine, passing it the custom context
world_model = WorldModel.from_context(context)
action_engine = ActionEngine.from_context(context, selenium_driver)

# Create your agent
agent = WebAgent(world_model, action_engine)

agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```

Here, we modify the default `OpenaiContext` by replacing its LLM, multi-modal LLM & embedding models. We can then pass this to our `Action Engine`.

## Creating a Context object from scratch

Alternative, you can create a `Context` from scratch by initializing a `lavague.core.Context` object and providing all the Context arguments: 

- `llm`
- `mm_llm`
- `embedding`

#### Example: Creating a fully custom context

```python
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.core.context import Context
from lavague.drivers.selenium import SeleniumDriver


# Customize the LLM, multi-modal LLM and embedding models
llm = Gemini(model_name="models/gemini-1.5-flash-latest")
mm_llm =  OpenAIMultiModal(model="gpt-4o", temperature=0.0)
embedding = GeminiEmbedding(model_name="models/text-embedding-004")

# Initialize context with our custom elements
context = Context(llm, mm_llm, embedding)

# Initialize the Selenium driver
selenium_driver = SeleniumDriver()

# Initialize a WorldModel and ActionEnginem passing them the custom context
world_model = WorldModel.from_context(context)
action_engine = ActionEngine.from_context(context, selenium_driver)

# Create your agent
agent = WebAgent(world_model, action_engine)

agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```

## Summary

By leveraging the Context module, you can customize the components used by the `Action Engine` and `World Model`, two of the key elements leveraged by a `Web Agent`.

You can do this by updating specific elements in one of our built-in contexts like `OpenaiContext`, or by create a new Context from scratch.

You can then pass the customized context to the `Action Engine` and `World Model` during their initialization.