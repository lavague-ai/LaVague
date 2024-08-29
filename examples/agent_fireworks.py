from lavague.contexts.fireworks import FireworksContext
from lavague.drivers.selenium import SeleniumDriver

from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent

# Initialize Context
context = FireworksContext()

selenium_driver = SeleniumDriver()

# Build AE and WM from Context
action_engine = ActionEngine.from_context(context, selenium_driver)
world_model = WorldModel.from_context(context)

agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/")
agent.run("What is this week's top Space of the week?")
