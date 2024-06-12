from lavague.core.evaluator import LLMEvaluator
from lavague.contexts.openai import OpenaiContext
from lavague.contexts.gemini import GeminiContext
import pandas as pd

llm_evaluator = LLMEvaluator()
retrieved_data_opsm = pd.read_csv("results_retriever1.csv")
llm_evaluator.evaluate(retrieved_data_opsm)
llm_evaluator.evaluate()