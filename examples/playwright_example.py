from lavague.drivers.playwright import PlaywrightDriver
from lavague.core import ActionEngine

# Don't forget to export OPENAI_API_KEY

playwright_driver = PlaywrightDriver("https://news.ycombinator.com")
action_engine = ActionEngine(playwright_driver)
action = action_engine.navigation_engine.get_action(
    "Enter hop inside the search bar and then press enter"
)
print(action)
