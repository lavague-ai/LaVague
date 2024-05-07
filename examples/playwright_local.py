from lavague.drivers.playwright import PlaywrightDriver
from lavague.contexts.huggingface import HuggingfaceContext
from lavague.core import ActionEngine

playwright_driver = PlaywrightDriver("https://news.ycombinator.com")
openai_context = HuggingfaceContext.from_defaults()
action_engine = ActionEngine.from_context(playwright_driver, openai_context)
action = action_engine.get_action("Enter hop inside the search bar and then press enter")
print(action)
