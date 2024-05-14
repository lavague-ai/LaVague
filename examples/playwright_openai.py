from lavague.drivers.playwright import PlaywrightDriver
from lavague.contexts.openai import OpenaiContext
from lavague.core import ActionEngine

# Don't forget to export OPENAI_API_KEY

playwright_driver = PlaywrightDriver("https://news.ycombinator.com")
openai_context = OpenaiContext.from_defaults()
action_engine = ActionEngine.from_context(playwright_driver, openai_context)
action = action_engine.get_action(
    "Enter hop inside the search bar and then press enter"
)
print(action)
