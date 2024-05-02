from lavague.integrations.drivers.playwright import PlaywrightDriver
from lavague.integrations.contexts.apis.openai_api import OpenaiContext
from lavague import ActionEngine

# Don't forget to export OPENAI_API_KEY

selenium_driver = PlaywrightDriver("https://news.ycombinator.com")
openai_context = OpenaiContext.from_defaults()
action_engine = ActionEngine.from_context(selenium_driver, openai_context)
action = action_engine.get_action("Enter hop inside the search bar and then press enter")
print(action)
