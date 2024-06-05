from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.playwright import PlaywrightDriver

playwright_driver = PlaywrightDriver()
world_model = WorldModel()
action_engine = ActionEngine(playwright_driver)
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
