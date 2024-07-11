from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.core.retrievers import IxpathRetriever


selenium_driver = SeleniumDriver(headless=False)
ixpath_retriever = IxpathRetriever(selenium_driver)
world_model = WorldModel()
action_engine = ActionEngine(selenium_driver, retriever=ixpath_retriever)
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/docs")
result = agent.run("Get the first paragraphe of the peft quicktour")
print()
print("output:\n", result.output)
print("generated code:\n" + result.code)
