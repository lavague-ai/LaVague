from lavague.core.action_builder import ActionBuilderStore
from lavague.core import ActionEngine
from lavague.drivers.selenium import SeleniumDriver

store = ActionBuilderStore(ActionEngine(SeleniumDriver("https://news.ycombinator.com")))
store.get_action("ActionEngine", "Enter hop inside the search bar and then press enter")
