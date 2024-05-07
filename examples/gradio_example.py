from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.openai import OpenaiContext
from lavague.core import ActionEngine
from lavague.gradio import GradioDemo

# Don't forget to export OPENAI_API_KEY

selenium_driver = SeleniumDriver("https://news.ycombinator.com")
openai_context = OpenaiContext.from_defaults()
action_engine = ActionEngine.from_context(selenium_driver, openai_context)
demo = GradioDemo(
    action_engine,
    instructions=["Click on search bar, then type 'lavague', then click enter"]
)
demo.launch()
