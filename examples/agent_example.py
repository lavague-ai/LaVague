from lavague.core import WorldModel, ActionEngine, PythonEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver

selenium_driver = SeleniumDriver(headless=False)
world_model = WorldModel()
action_engine = ActionEngine(selenium_driver)
python_engine = PythonEngine()
agent = WebAgent(world_model, action_engine, python_engine)
agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
