# OpenAI Context

The AzureOpenaiContext enabled you to use LaVague with your models deployed with Azure.

There are no default names for this context since the names of models can vary per region.

## Pre-requisites

The AzureOpenaiContext is part of the `OpenaiContext` package and is installed by default with `LaVague`.

## AzureOpenaiContext arguments

The AzureOpenaiContext accepts the following optional arguments. These may or may not be required depending on your Azure configuration.

| Option                 | Description                                          |
|------------------------|------------------------------------------------------|
| `api_key`              | Your API key for Azure OpenAI. |
| `llm`                  | The name of your LLM. |
| `endpoint`             | The endpoint URL for your Azure OpenAI deployment. |
| `deployment`           | The deployment name for your llm and mm_llm model. |
| `mm_llm`               | The name of your multi-modal LLM. |
| `mm_llm_endpoint`      | Only required if different to `endpoint`, the endpoint URL for your multi-modal LLM deployment. |
| `mm_llm_deployment`    | Only required if different to `deployment`, the deployment name for your llm and mm_llm model. |
| `embedding`            | The name of your embedding model - by default `text-embedding-ada-002` |
| `embedding_endpoint`   | Only required if different to `endpoint`, the endpoint URL for your embedding model. |
| `embedding_deployment` | The deployment name for your embedding model. |
| `embedding_api_base`   | The base URL for Azure embedding deployment. |
| `api_version`          | The API version to use for requests to the Azure OpenAI service. |

You can alternatively provide the following arguments by setting them as environment variables:

- AZURE_OPENAI_KEY instead of passing an `api_key`
- AZURE_OPENAI_ENDPOINT instead of passing `endpoint`
- AZURE_OPENAI_DEPLOYMENT instead of passing `deployment`
- AZURE_API_VERSION instead of passing `api_version`

For guidance on setting environment variables in your environment, see [our FAQ](../get-started/FAQs.md#how-can-i-set-environment-variables).

### End-to-end example

To use the AzureOpenaiContext, you should import the `lavagues.contexts.openai` package, initialize you `AzureOpenaiContext` and then pass it to our `Action Engine` using the `from_context()` initialization method.

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.openai import AzureOpenaiContext

# Initialize context
context = AzureOpenaiContext(
    api_key="<api_key>",
    llm="gpt-4o",
    mm_llm="gpt-4o",
    deployment="<deployment_Name>",
    endpoint="<endpoint>",
    api_version="2023-03-15-preview",
    embedding="<embedding model name>",
    embedding_deployment="<embedding_deployment_name>",
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

It may be that the AzureOpenaiContext does not fit your needs because you want to use Azure for only one or two of the models. In this case you can initialize and pass your azure models individually when creating your agent.

To do this you can use `llama-index` to initalize your models like in the example below:

```python
from llama_index.llms.azure_openai import AzureOpenAI

llm = AzureOpenAI(
    api_key="<api_key>",
    azure_endpoint="<your_endpoint>",
    engine="<deployment_name>",
    model="gpt-4o",
    api_version="2023-03-15-preview",
)

from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal
mm_llm = AzureOpenAIMultiModal(
    api_key="<api_key>",
    azure_endpoint="<your_endpoint>",
    engine="<deployment_name>",
    model="gpt-4o",
    api_version="2023-03-15-preview",
)

from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
embedding = AzureOpenAIEmbedding(
    api_key="<api_key>",
    model="<embedding_model_name>",
    azure_endpoint="<your_endpoint>",
    azure_deployment="<deployment_name>",
    api_version="2023-03-15-preview",
    api_base="<api base URL>"
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
