from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure
from lavague.core.retrievers import BaseHtmlRetriever
from lavague.core.navigation import NavigationEngine
from lavague.drivers.selenium import SeleniumDriver
from tqdm import tqdm
from datetime import datetime
import yaml
from llama_index.core import QueryBundle
import traceback
import ast
from bs4 import BeautifulSoup
from tempfile import NamedTemporaryFile
import time


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self) -> pd.DataFrame:
        pass

    def compare(
        self,
        results: Dict[str, pd.DataFrame],
        metrics: list,
    ) -> Figure:
        fig, axes = plt.subplots(1, len(metrics), figsize=(5 * len(metrics), 5))

        df = pd.DataFrame()
        for metric in metrics:
            if metric in metrics:
                df[metric] = [dfr[metric].mean() for dfr in results.values()]
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


def parse_yaml(action):
    try:
        return yaml.safe_load(action)[0]["actions"][0]["action"]
    except:
        return None


def parse_viewport_size(vsize):
    vsize = ast.literal_eval(vsize)
    if type(vsize["width"]) is dict:
        return {
            "width": vsize["width"]["value"],
            "height": vsize["height"]["value"],
        }  # sometime viewport size is logged like this. idkw
    return vsize


def validate_action(action):
    try:
        _ = action["args"]["xpath"]
        _ = action["name"]
        return action["name"] != "fail"
    except:
        return False


def normalize_xpath(xpath: str):
    return xpath.replace("[1]", "")


def load_website_in_driver(driver, html, viewport_size, action):
    with NamedTemporaryFile(delete=False, mode="w", suffix=".html") as f:
        f.write(html)
    if viewport_size:
        driver.resize_driver(viewport_size["width"], viewport_size["height"])
    driver.get(f"file:{f.name}")
    driver.wait_for_idle()
    element = driver.resolve_xpath(action["args"]["xpath"])
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element
    )


FAIL_ACTION = {"args": {"xpath": "(string)"}, "name": "fail"}


class RetrieverEvaluator(Evaluator):
    def evaluate(
        self,
        retriever: BaseHtmlRetriever,
        dataset: pd.DataFrame,
        driver: SeleniumDriver = None,  # Optional, the driver passed to the retriever
        retriever_name: str = "",
        wait_for_scroll: int = 1,
    ) -> pd.DataFrame:
        result_filename = (
            (retriever_name if retriever_name else type(retriever).__name__)
            + "_evaluation_"
            + datetime.now().strftime("%Y-%m-%d_%H-%M")
            + ".csv"
        )
        results = dataset.loc[dataset["validated"]].copy()
        results.insert(len(results.columns), "result_nodes", None)
        results.insert(len(results.columns), "recall", None)
        results.insert(len(results.columns), "output_size", None)
        results.insert(len(results.columns), "time", None)
        results["dataset_index"] = results.index
        results.to_csv(result_filename, index=False)

        try:
            for i, row in tqdm(results.iterrows()):
                action = yaml.safe_load(row["action"])
                instruction = row["instruction"]
                try:
                    if driver:
                        driver.__init__()
                        viewport_size = parse_viewport_size(row["viewport_size"])
                        load_website_in_driver(
                            driver, row["html"], viewport_size, action
                        )
                        time.sleep(wait_for_scroll)
                    t_begin = datetime.now()
                    nodes = retriever.retrieve(
                        QueryBundle(query_str=instruction), [driver.get_html()]
                    )
                    t_end = datetime.now()
                except:
                    print("ERROR: ", i)
                    traceback.print_exc()
                    nodes = []
                if driver:
                    driver.destroy()
                nodes = "\n".join(nodes)
                results.at[i, "result_nodes"] = nodes
                results.at[i, "recall"] = (
                    1 if normalize_xpath(action["args"]["xpath"]) in nodes else 0
                )
                results.at[i, "output_size"] = len(nodes)
                results.at[i, "time"] = pd.Timedelta(t_end - t_begin).total_seconds()
            print("Evaluation terminated successfully.")
        except:
            traceback.print_exc()
            print(f"Evaluation stopped at row {i} because an exception was caught.")
        finally:
            results.to_csv(result_filename, index=False)
            print(f"Results are saved to {result_filename}")
            return results

    def compare(
        self,
        results: Dict[str, pd.DataFrame],
        metrics: list = ["recall", "output_size", "time"],
    ) -> Figure:
        return super().compare(results, metrics)


class NavigationEngineEvaluator(Evaluator):
    def evaluate(
        self,
        navigation_engine: NavigationEngine,
        dataset: pd.DataFrame,
        navigation_engine_name="",
    ) -> pd.DataFrame:
        result_filename = (
            (
                navigation_engine_name
                if navigation_engine_name
                else type(navigation_engine).__name__
            )
            + "_evaluation_"
            + datetime.now().strftime("%Y-%m-%d_%H-%M")
            + ".csv"
        )
        results = dataset.loc[dataset["validated"]].copy()
        results.insert(len(results.columns), "recall", None)
        results.insert(len(results.columns), "correct_action", None)
        results.insert(len(results.columns), "correct_xpath", None)
        results.insert(len(results.columns), "time", None)
        results["dataset_index"] = results.index
        results.to_csv(result_filename, index=False)

        try:
            for i, row in tqdm(results.iterrows()):
                action = yaml.safe_load(row["action"])
                viewport_size = parse_viewport_size(row["viewport_size"])
                instruction = row["instruction"]
                try:
                    load_website_in_driver(
                        navigation_engine.driver, row["html"], viewport_size, action
                    )
                    t_begin = datetime.now()
                    test_action = navigation_engine.execute_instruction(
                        instruction
                    ).code
                    test_action = parse_yaml(test_action)
                    if not validate_action(test_action):
                        test_action = FAIL_ACTION
                    t_end = datetime.now()
                except:
                    print("ERROR: ", i)
                    traceback.print_exc()
                    test_action = FAIL_ACTION
                results.at[i, "correct_action"] = action["name"] == test_action["name"]
                results.at[i, "correct_xpath"] = (
                    normalize_xpath(action["args"]["xpath"])
                    == test_action["args"]["xpath"]
                )
                results.at[i, "recall"] = (
                    results.at[i, "correct_action"] and results.at[i, "correct_xpath"]
                )
                results.at[i, "time"] = pd.Timedelta(t_end - t_begin).total_seconds()
            print("Evaluation terminated successfully.")
        except:
            traceback.print_exc()
            print(f"Evaluation stopped at row {i} because an exception was caught.")
        finally:
            results.to_csv(result_filename, index=False)
            print(f"Results are saved to {result_filename}")
            return results

    def compare(
        self,
        results: Dict[str, pd.DataFrame],
        metrics: list = ["recall", "correct_action", "correct_xpath", "time"],
    ) -> Figure:
        return super().compare(results, metrics)
