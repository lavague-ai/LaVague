"""
Tree search Web Agent demo.
"""

from lavague.core import  WorldModel, ActionEngine
from lavague.core.agents import TreeSearchWebAgent
from lavague.drivers.selenium import SeleniumDriver


# Initialize the components
selenium_driver = SeleniumDriver(headless=False)
world_model = WorldModel()
action_engine = ActionEngine(selenium_driver)

# Add argument parser to check if the argument --tree-search is passed
agent = TreeSearchWebAgent(
    world_model=world_model,
    action_engine=action_engine,
    n_steps=10,
    max_depth=5,
    branching_factor=5,
    sample_size=5
)

# Run the agent on a single example
agent.get("https://www.ankorstore.com")
agent.run("What's the cheapest red candle ?", step_by_step=True)
