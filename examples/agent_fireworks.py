from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.fireworks import FireworksContext


context = FireworksContext()
selenium_driver = SeleniumDriver()
world_model = WorldModel()
action_engine = ActionEngine.from_context(context, selenium_driver)
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/")
agent.run("What is this week's top dataset?")
