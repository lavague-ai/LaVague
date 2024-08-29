from lavague.drivers.playwright import PlaywrightDriver

from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent

playwright_driver = PlaywrightDriver(headless=False)
world_model = WorldModel()
action_engine = ActionEngine(playwright_driver)
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/docs")
result = agent.run("Get the first paragraphe of the peft quicktour")
print()
print("output:\n", result.output)
print("generated code:\n" + result.code)
