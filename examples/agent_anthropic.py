from lavague.contexts.anthropic import AnthropicContext
from lavague.drivers.selenium import SeleniumDriver

from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent

context = AnthropicContext()
selenium_driver = SeleniumDriver(headless=True)

world_model = WorldModel.from_context(context=context)
action_engine = ActionEngine.from_context(context=context, driver=selenium_driver)
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/docs")
agent.run("What is this week's top model?")
