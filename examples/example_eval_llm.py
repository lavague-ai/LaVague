from lavague.core.evaluator import LLMEvaluator
from lavague.contexts.openai import OpenaiContext
from lavague.contexts.gemini import GeminiContext
from lavague.core.navigation import NavigationEngine
from lavague.drivers.selenium import SeleniumDriver
import pandas as pd

llm_evaluator = LLMEvaluator()
# openai_engine = NavigationEngine.from_context(OpenaiContext(), SeleniumDriver())
# gemini_engine = NavigationEngine.from_context(GeminiContext(), SeleniumDriver())
# retrieved_data_opsm = pd.read_csv("results_retriever1.csv")
# df1 = llm_evaluator.evaluate(openai_engine, retrieved_data_opsm, "openai_results.csv")
# df2 = llm_evaluator.evaluate(gemini_engine, retrieved_data_opsm, "gemini_results.csv")
# print(df1.head())
# print(df2.head())

df1 = pd.read_csv("openai_results.csv")
df2 = pd.read_csv("gemini_results.csv")
plot = llm_evaluator.compare({
    "openai": df1,
    "gemini": df2,
})
plot.legend()
plot.show()
input()