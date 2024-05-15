from lavague.core import WebAgent, WorldModel, ActionEngine
from lavague.drivers.selenium import SeleniumDriver

selenium_driver = SeleniumDriver()
world_model = WorldModel.from_hub("hf_example")
action_engine = ActionEngine(selenium_driver)
agent = WebAgent(action_engine, world_model)
agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")