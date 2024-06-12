from lavague.core.evaluator import RetrieverEvaluator, LLMEvaluator
import pandas as pd

retriever_evaluator = RetrieverEvaluator()
retrieved_data_opsm = pd.read_csv("results_retriever1.csv")
retrieved_data_bm25 = pd.read_csv("results_retriever2.csv")
plot = retriever_evaluator.compare({
    "opsm": retrieved_data_opsm,
    "bm25": retrieved_data_bm25
})
plot.show()
plot.waitforbuttonpress()