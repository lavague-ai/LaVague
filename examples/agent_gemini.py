from lavague.contexts.gemini import GeminiContext
from lavague.contexts.openai import OpenaiContext
from lavague.drivers.selenium import SeleniumDriver

from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent

context = GeminiContext()
selenium_driver = SeleniumDriver(headless=True)
world_model = WorldModel.from_context(context=context)
action_engine = ActionEngine.from_context(context, selenium_driver)
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
