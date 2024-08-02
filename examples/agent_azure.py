from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal

from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.contexts.openai import AzureOpenaiContext
from lavague.drivers.selenium import SeleniumDriver
import os

from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from lavague.core.context import Context
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.openai import AzureOpenaiContext


# Initialize context with our custom elements
context = AzureOpenaiContext(
    api_key="<YOUR_API_KEY>",
    deployment="<YOUR_DEPLOYMENT_NAME>",
    llm="MODEL_NAME",
    mm_llm="M0DEL_NAME",
    endpoint="<YOUR_ENDPOINT>",
    embedding="<EMBEDDING_MODEL_NAME>",
    embedding_deployment="<YOUR_EMBEDDING_DEPLOYMENT_NAME>",
)

# Initialize the Selenium driver
selenium_driver = SeleniumDriver()

# Initialize a WorldModel and ActionEnginem passing them the custom context
world_model = WorldModel.from_context(context)
action_engine = ActionEngine.from_context(context, selenium_driver)

# Create your agent
agent = WebAgent(world_model, action_engine)

agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
