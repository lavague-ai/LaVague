# OpenAI Context

The AzureOpenaiContext enabled you to use LaVague with your models deployed with Azure.

By default, we set the `llm` and `mm_llm` models to `gpt-4o` and the embedding model to `text-embedding-3-small`. You will need to have these models deployed if you want to use these defaults.

## Pre-requisites

The AzureOpenaiContext is part of the `OpenaiContext` package and is installed by default with `LaVague`.

## AzureOpenaiContext arguments

The AzureOpenaiContext accepts the following optional arguments. These may or may not be required depending on your Azure configuration.

| Option                 | Description                                          |
|------------------------|------------------------------------------------------|
| `api_key`              | Your API key for Azure OpenAI. |
| `api_version`          | The API version - `2023-07-01-preview` by default |
| `llm`                  | The name of your LLM - `gpt-4o` by default |
| `mm_llm`               | The name of your multi-modal LLM - - `gpt-4o` by default |
| `embedding`            | The name of your embedding model - by default `text-embedding-3-small` by default |
| `endpoint`             | The endpoint URL for your Azure OpenAI deployment. |
| `deployment`           | The deployment name for your llm and mm_llm model. |
| `embedding_deployment` | The deployment name for your embedding model. |
| `embedding_endpoint`   | **Only required if different to `endpoint`**, the endpoint URL for your embedding model. |
| `mm_llm_deployment`    | **Only required if different to `deployment`**, the deployment name for your llm and mm_llm model. |
| `mm_llm_endpoint`      | **Only required if different to `endpoint`**, the endpoint URL for your multi-modal LLM deployment. |

You can alternatively provide the following arguments by setting them as environment variables:

- AZURE_OPENAI_KEY instead of passing an `api_key`
- AZURE_OPENAI_ENDPOINT instead of passing `endpoint`
- AZURE_OPENAI_DEPLOYMENT instead of passing `deployment`
- AZURE_API_VERSION instead of passing `api_version`

For guidance on setting environment variables in your environment, see [our FAQ](../get-started/FAQs.md#how-can-i-set-environment-variables).

### End-to-end example

To use the AzureOpenaiContext, you should import the `lavague.contexts.openai` package, initialize you `AzureOpenaiContext` and then pass it to our `Action Engine` using the `from_context()` initialization method.

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.openai import AzureOpenaiContext

# Initialize context with our custom elements
context = AzureOpenaiContext(
    api_key="your_api_key",
    deployment="deployment_name",
    llm="<model_name>",
    mm_llm="<model_name>",
    endpoint="<your_endpoint>",
    embedding="embedding_model_name",
    embedding_deployment="embedding_deployment_name"
)

selenium_driver = SeleniumDriver()

# Build Action Engine and World Model from Context
action_engine = ActionEngine.from_context(context=context, driver=selenium_driver)
world_model = WorldModel()

# Build agent & run query
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/")
agent.run("What is this week's top Space of the week?")
```

### Passing Azure models

It may be that the AzureOpenaiContext does not fit your needs because you only want to use Azure for only one or two of the models. In this case, you can initialize and pass your azure models individually when creating your agent.

To do this you can use `llama-index` to initialize your models like in the example below:

```python
from llama_index.llms.azure_openai import AzureOpenAI

llm = AzureOpenAI(
    api_key="<your_api_key>",
    model="<model_name>",
    azure_endpoint="<your_endpoint>",
    deployment_name="<your_deployment_name>"
)

from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal
mm_llm = AzureOpenAIMultiModal(
    api_key="<api_key>",
    model="<model_name>",
    azure_endpoint="<your_endpoint>",
    deployment_name="<your_deployment_name>"
)

from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
embedding = AzureOpenAIEmbedding(
    api_key="<api_key>",
    model="<embedding_model_name>",
    azure_endpoint="<your_endpoint>",
    azure_deployment="<your_deployment_name>",
),
```

You can then pass these models to the World Model and Action Engine when creating your agent:

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver

# Initialize the Selenium driver
selenium_driver = SeleniumDriver()

# Initialize a WorldModel and ActionEnginem passing them the custom context
world_model = WorldModel(mm_llm=mm_llm)
action_engine = ActionEngine(llm=llm, embedding=embedding, driver=selenium_driver)

# Create your agent
agent = WebAgent(world_model, action_engine)

agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```
