from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.core.retrievers import (
    InteractiveXPathRetriever,
    RetrieversPipeline,
    SyntaxicRetriever,
    XPathedChunkRetriever,
)

selenium_driver = SeleniumDriver(headless=False)

retriever = RetrieversPipeline(
    InteractiveXPathRetriever(selenium_driver),
    SyntaxicRetriever(),
    XPathedChunkRetriever(),
)

world_model = WorldModel()
action_engine = ActionEngine(selenium_driver, retriever=retriever)
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/docs")
result = agent.run("Get the first paragraph of the peft quicktour")
print()
print("output:\n", result.output)
print("generated code:\n" + result.code)
