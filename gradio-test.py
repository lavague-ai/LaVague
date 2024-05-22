# from llama_index.embeddings.gemini import GeminiEmbedding
# from llama_index.llms.gemini import Gemini
from lavague.contexts.openai import OpenaiContext
from lavague.core import WebAgent, WorldModel, ActionEngine
from lavague.drivers.selenium import SeleniumDriver
from lavague.gradio import GradioAgentDemo

context = OpenaiContext()
# context.llm = Gemini(model_name="models/gemini-1.5-flash-latest")
# context.embedding =  GeminiEmbedding(model_name="models/text-embedding-004")
selenium_driver = SeleniumDriver()

world_model = WorldModel.from_hub("hf_example")
action_engine = ActionEngine(selenium_driver, context)

demo = GradioAgentDemo(action_engine, world_model)
demo.launch()