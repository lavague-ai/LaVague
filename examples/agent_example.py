from lavague.core import WebAgent, WorldModel, ActionEngine, PythonEngine
from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.openai import OpenaiContext
from lavague.contexts.gemini import GeminiContext


context = GeminiContext()
context.mm_llm = OpenaiContext().mm_llm
selenium_driver = SeleniumDriver()
world_model = WorldModel.from_context(context)
action_engine = ActionEngine.from_context(context, selenium_driver)
python_engine = PythonEngine.from_context(context)
agent = WebAgent(world_model, action_engine, python_engine)
agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
