from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.fireworks import FireworksContext


# Initialize Context
context = FireworksContext()

selenium_driver = SeleniumDriver()

# Build AE and WM from Context
action_engine = ActionEngine.from_context(context, selenium_driver)
world_model = WorldModel.from_context(context)

agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/")
agent.run("What is this week's top Space of the week?")
