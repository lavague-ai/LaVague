from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.openai import OpenaiContext
from lavague.core import ActionEngine

# Don't forget to export OPENAI_API_KEY

selenium_driver = SeleniumDriver("https://news.ycombinator.com")
openai_context = OpenaiContext.from_defaults()
action_engine = ActionEngine.from_context(selenium_driver, openai_context)
