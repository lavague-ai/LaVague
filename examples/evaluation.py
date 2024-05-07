from lavague.integrations.drivers.playwright import PlaywrightDriver
from lavague.integrations.contexts.apis.openai_api import OpenaiContext
from lavague import Evaluator

# Don't forget to export OPENAI_API_KEY

selenium_driver = PlaywrightDriver("https://news.ycombinator.com")
openai_context = OpenaiContext.from_defaults()
evaluator = Evaluator.from_context(selenium_driver, openai_context)
evaluator.eval_retriever() # ...