from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine

# Don't forget to export OPENAI_API_KEY

selenium_driver = SeleniumDriver("https://news.ycombinator.com")
action_engine = ActionEngine(selenium_driver)
action = action_engine.navigation_engine.get_action(
    "Enter hop inside the search bar and then press enter"
)
print(action)
