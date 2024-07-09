from lavague.drivers.selenium import SeleniumDriver
from lavague.core import OpsmSplitRetriever
from llama_index.core import QueryBundle

selenium_driver = SeleniumDriver(headless=True)
selenium_driver.get("https://selectorshub.com/iframe-scenario/")
retriever = OpsmSplitRetriever(selenium_driver)
results = retriever.retrieve_html(QueryBundle("placeholder Destiny"))
print(results)
