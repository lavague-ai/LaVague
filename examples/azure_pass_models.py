from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from lavague.core.context import Context
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver


llm = AzureOpenAI(
    api_key="<api_key>",
    azure_endpoint="<your_endpoint>",
    engine="<deployment_name>",
    model="gpt-4o",
    api_version="2023-03-15-preview",
)

mm_llm = AzureOpenAIMultiModal(
    api_key="<api_key>",
    azure_endpoint="<your_endpoint>",
    engine="<deployment_name>",
    model="gpt-4o",
    api_version="2023-03-15-preview",
)

# Initialize the Selenium driver
selenium_driver = SeleniumDriver()

# Initialize a WorldModel and ActionEnginem passing them the custom context
world_model = WorldModel(mm_llm=mm_llm)
action_engine = ActionEngine(llm=llm, driver=selenium_driver)

# Create your agent
agent = WebAgent(world_model, action_engine)

agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
