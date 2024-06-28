from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from lavague.core.context import Context
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver


llm = AzureOpenAI(
    api_key="<api_key>",
    api_version="2023-03-15-preview",
    azure_endpoint="<your_endpoint>",
    engine="<deployment_name>",
    model="gpt-4o",
)

mm_llm = AzureOpenAIMultiModal(
    api_key="<api_key>",
    api_version="2023-03-15-preview",
    azure_endpoint="<your_endpoint>",
    engine="<deployment_name>",
    model="gpt-4o",
)

embedding = AzureOpenAIEmbedding(
    api_key="<api_key>",
    api_version="2023-03-15-preview",
    azure_endpoint="<your_endpoint>",
    azure_deployment="<deployment_name>",
    model="text-embedding-ada-002",
)

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
