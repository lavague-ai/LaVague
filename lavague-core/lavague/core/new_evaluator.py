from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure
from lavague.core.retrievers import BaseHtmlRetriever
from lavague.drivers.selenium import SeleniumDriver
from tqdm import tqdm
from datetime import datetime
import yaml
import traceback

class Evaluator(ABC):
    @abstractmethod
    def evaluate(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def compare(self, results: Dict[str, pd.DataFrame]) -> Figure:
        pass

def parse_action(action: str) -> dict:
    action = yaml.safe_load(action)
    try:
        action = action[0]["actions"][0]["action"]
        _ = action["args"]["xpath"]
        _ = action["name"]
        return action
    except:
        return None

class RetrieverEvalutor(Evaluator):
    def evaluate(
        self,
        retriever: BaseHtmlRetriever,
        dataset: pd.DataFrame,
        retriever_name: str = "",
    ) -> pd.DataFrame:
        result_filename = (retriever_name if retriever_name else type(retriever).__name__) + "_evaluation_" + datetime.now().strftime("%Y-%m-%d_%H-%M") + ".csv"
        results = dataset.loc[dataset["is_verified"]].copy()
        results.insert(len(results.columns), "recall", None)
        results.insert(len(results.columns), "output_size", None)
        results.insert(len(results.columns), "retrieval_time", None)
        results.to_csv(result_filename, index=False)

        driver = SeleniumDriver()
        try:
            for i, row in tqdm(results.iterrows()):
                action = parse_action(row["action"])
                if not action:
                    print(f"row {i} is verified, but action is invalid, resuming")
                    print("action:", row["action"])
                    continue
                t_begin = datetime.now()
                nodes = retriever.retrieve(row["instruction"], row["preaction_html_source"])
                t_end = datetime.now()
                print(nodes)
                nodes = "\n".join(nodes)
                results.at[i, "recall"] = 1 if action["args"]["xpath"] in nodes else 0
                results.at[i, "output_size"] = len(nodes)
                results.at[i, "retrieval_time"] = pd.Timedelta(t_end - t_begin)
            print("Evaluation terminated succesfully.")
        except:
            traceback.print_exc()
            print(f"Evaluation stopped at row {i} because an exception was caught.")
        finally:
            results.to_csv(result_filename, index=False)
            print(f"Results are saved to {result_filename}.")
            return results


    def compare(
        self,
        results: Dict[str, pd.DataFrame],
        metrics: list = ["recall", "output_size", "retrieval_time"],
    ) -> Figure:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        df = pd.DataFrame()
        for metric in metrics:
            if metric in metrics:
                df[metric] = [
                    dfr[metric].mean()
                    for dfr in results.values()
                ]
        df["name"] = list(results.keys())

        count = 0
        for metric in metrics:
            if metric in metrics:
                plot = sns.barplot(data=df, x="name", y=metric, ax=axes[count])
                count += 1
                if metric == "time":
                    plot.set(xlabel="", ylabel="time (secs)")
                else:
                    plot.set(xlabel="")
        return fig
