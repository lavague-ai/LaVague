from abc import ABC, abstractmethod
from lavague.core.retrievers import BaseHtmlRetriever
from lavague.drivers.selenium import SeleniumDriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import pandas as pd
from tqdm import tqdm
from time import time
from typing import Dict
from lavague.core.navigation import NavigationEngine
from lavague.core.context import get_default_context
from lavague.core.navigation import Rephraser
from bs4 import BeautifulSoup
import uuid
from llama_index.core.llms import LLM
import os
from llama_index.core import QueryBundle
from matplotlib.figure import Figure
import re
from lavague.core.utilities.format_utils import (
    keep_assignments,
    return_assigned_variables,
)
import matplotlib.pyplot as plt
import seaborn as sns
import json


def init_driver() -> WebDriver:
    # these imports are necessary as they will be pasted to the output
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--proxy-server=127.0.0.1:9999")

    return webdriver.Chrome(options=chrome_options)


class SeleniumDriverForEval(SeleniumDriver):
    def check_visibility(self, xpath: str) -> bool:
        return True


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, dataset: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def compare(self, results: Dict[str, pd.DataFrame], metrics: list) -> Figure:
        pass

    def _load_html(self, html: str, driver: SeleniumDriver):
        """Loads a specific HTML content into the browser."""
        file_path = f"tmp_{uuid.uuid4()}.html"

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html)

        abs_file_path = os.path.abspath(file_path)

        # Use the file:/// protocol to load the local HTML file
        driver.get(f"file:///{abs_file_path}")

        os.remove(abs_file_path)

    def _extract_backend_node_ids(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        return set(
            [
                tag["backend_node_id"]
                for tag in soup.find_all(attrs={"backend_node_id": True})
            ]
        )

    def _intersection_score(self, set1, set2):
        intersection_set = set1 & set2
        intersection_len = len(intersection_set)
        ratio1 = intersection_len / max(len(set1), 1)
        ratio2 = intersection_len / max(len(set2), 1)
        return max(ratio1, ratio2), min(ratio1, ratio2)

    def _intersection_backend_node_id(self, ground_truth_outer_html, context_str):
        ground_truth_ids = self._extract_backend_node_ids(ground_truth_outer_html)
        context_ids = self._extract_backend_node_ids(context_str)
        recall, precision = self._intersection_score(ground_truth_ids, context_ids)
        return recall, precision


class RetrieverEvaluator(Evaluator):
    def __init__(self):
        self.driver = SeleniumDriverForEval(get_selenium_driver=init_driver)

    def rephrase_dataset(
        self, dataset: pd.DataFrame, csv_out_name: str, llm: LLM = None
    ) -> pd.DataFrame:
        if os.path.isfile(csv_out_name):
            raise ValueError(f"{csv_out_name} already exists")
        if llm is None:
            llm = get_default_context().llm
        rephraser = Rephraser(llm)
        for i, row in tqdm(dataset.iterrows()):
            rephrase_list = rephraser.rephrase_query(row["query"])
            dataset.at[i, "retriever_query"] = rephrase_list[0]["query"]
            dataset.at[i, "llm_query"] = rephrase_list[0]["action"]
        dataset.to_csv(csv_out_name)
        return dataset

    def evaluate(
        self,
        retriever: BaseHtmlRetriever,
        rephrased_dataset: pd.DataFrame,
        csv_out_name: str,
    ) -> pd.DataFrame:
        if os.path.isfile(csv_out_name):
            raise ValueError(f"{csv_out_name} already exists")
        retriever.driver = self.driver
        retrieved_dataset = rephrased_dataset.copy()
        retrieved_dataset["html_id"] = self._gen_html_ids(rephrased_dataset)
        retrieved_dataset["recall_retriever"] = pd.Series(dtype="float")
        retrieved_dataset["precision_retriever"] = pd.Series(dtype="float")
        retrieved_dataset["source_nodes"] = pd.Series(dtype="str")
        retrieved_dataset["retrieval_time"] = pd.Series(dtype="float")
        try:
            for i, row in tqdm(retrieved_dataset.iterrows()):
                self._load_html(row["html_id"], self.driver)
                element = self.driver.driver.find_element(By.XPATH, row["xpath"])
                ground_truth_outer_html = self.driver.execute_script(
                    "return arguments[0].outerHTML", element
                )
                start_time = time()
                results = retriever.retrieve_html(QueryBundle(row["retriever_query"]))
                duration = time() - start_time
                source_nodes = [node.text for node in results]
                context_str = "\n".join(source_nodes)
                (
                    recall_retriever,
                    precision_retriever,
                ) = self._intersection_backend_node_id(
                    ground_truth_outer_html, context_str
                )
                new_row = {
                    "recall_retriever": recall_retriever,
                    "precision_retriever": precision_retriever,
                    "source_nodes": context_str,
                    "retrieval_time": duration,
                }
                retrieved_dataset.loc[i, new_row.keys()] = new_row.values()
        except Exception as e:
            retrieved_dataset.to_csv(csv_out_name)
            raise e
        retrieved_dataset.to_csv(csv_out_name)
        return retrieved_dataset

    def compare(
        self,
        results: Dict[str, pd.DataFrame],
        metrics: list = ["precision", "recall", "time"],
    ) -> Figure:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        df = pd.DataFrame()
        metricMap = {
            "precision": "precision_retriever",
            "recall": "recall_retriever",
            "time": "retrieval_time",
        }
        for metric in metrics:
            if metric in metricMap.keys():
                df[metric] = [
                    dfr[metricMap[metric]].mean()
                    for dfr in results.values()
                    if metricMap[metric] in dfr.columns
                ]
        df["name"] = list(results.keys())

        count = 0
        for metric in metrics:
            if metric in metricMap.keys():
                plot = sns.barplot(data=df, x="name", y=metric, ax=axes[count])
                count += 1
                if metric == "time":
                    plot.set(xlabel="", ylabel="time (secs)")
                else:
                    plot.set(xlabel="")
        return fig

    def _gen_html_ids(self, df: pd.DataFrame):
        def add_ids_to_tags(html_string):
            soup = BeautifulSoup(html_string, "html.parser")
            node_id = 1
            for tag in soup.find_all(True):  # The True argument here finds all tags
                tag["backend_node_id"] = str(node_id)
                node_id += 1
            return str(soup)

        return df["html"].apply(lambda x: add_ids_to_tags(x))


class LLMEvaluator(Evaluator):
    def __init__(self):
        self.driver = SeleniumDriverForEval(get_selenium_driver=init_driver)

    def evaluate(
        self,
        navigation_engine: NavigationEngine,
        retrieved_dataset: pd.DataFrame,
        csv_out_name: str,
        max_retry: int = 1,
        safe_mode: bool = True,
    ) -> pd.DataFrame:
        if os.path.isfile(csv_out_name):
            raise ValueError(f"{csv_out_name} already exists")
        llm_dataset = retrieved_dataset.copy()
        llm_dataset["recall_llm"] = pd.Series(dtype="float")
        llm_dataset["precision_llm"] = pd.Series(dtype="float")
        llm_dataset["execution_error"] = pd.Series(dtype="str")
        llm_dataset["target_outer_html"] = pd.Series(dtype="str")
        llm_dataset["generated_code"] = pd.Series(dtype="str")
        llm_dataset["retry"] = pd.Series(dtype="int")
        llm_dataset["code_generation_time"] = pd.Series(dtype="float")
        try:
            for i, row in tqdm(llm_dataset.iterrows()):
                self._load_html(row["html_id"], self.driver)
                element = self.driver.driver.find_element(By.XPATH, row["xpath"])
                ground_truth_outer_html = self.driver.execute_script(
                    "return arguments[0].outerHTML;", element
                )
                decontaminated_context_str = re.sub(
                    r' backend_node_id="\d+"', "", row["source_nodes"]
                )
                generated_code = target_outer_html = execution_error = ""
                recall_llm = precision_llm = 0.0
                for retry in range(max_retry):
                    start_time = time()
                    generated_code = navigation_engine.get_action_from_context(
                        decontaminated_context_str, row["llm_query"]
                    )
                    duration = time() - start_time
                    try:
                        if safe_mode == False:
                            local_scope = {"driver": self.driver.get_driver()}
                            assignment_code = keep_assignments(generated_code)
                            self.driver.exec_code(assignment_code, locals=local_scope)
                            # Assign the variable to the target_element variable which will be used afterwards to compute score
                            variables = return_assigned_variables(assignment_code)
                            target_element = None
                            for v in variables:
                                if type(local_scope[v]) == WebElement:
                                    target_element = local_scope[v]
                                    break
                        else:
                            data = json.loads(generated_code)
                            for item in data:
                                action_name = item["action"]["name"]
                                if action_name != "fail":
                                    xpath = item["action"]["args"]["xpath"]
                                    target_element = self.driver.driver.find_element(
                                        By.XPATH, xpath
                                    )
                                    break

                        target_outer_html = self.driver.execute_script(
                            "return arguments[0].outerHTML;", target_element
                        )
                        recall_llm, precision_llm = self._intersection_backend_node_id(
                            ground_truth_outer_html, target_outer_html
                        )
                        break
                    except Exception as e:
                        execution_error = str(e)
                new_row = {
                    "recall_llm": recall_llm,
                    "precision_llm": precision_llm,
                    "execution_error": execution_error,
                    "target_outer_html": target_outer_html,
                    "generated_code": generated_code,
                    "retry": retry,
                    "code_generation_time": duration,
                }
                llm_dataset.loc[i, new_row.keys()] = new_row.values()
        except Exception as e:
            llm_dataset.to_csv(csv_out_name)
            raise e
        llm_dataset.to_csv(csv_out_name)
        return llm_dataset

    def compare(
        self,
        results: Dict[str, pd.DataFrame],
        metrics: list = ["precision", "recall", "time"],
    ) -> Figure:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        df = pd.DataFrame()
        metricMap = {
            "precision": "precision_retriever",
            "recall": "recall_retriever",
            "time": "retrieval_time",
        }
        for metric in metrics:
            if metric in metricMap.keys():
                df[metric] = [
                    dfr[metricMap[metric]].mean()
                    for dfr in results.values()
                    if metricMap[metric] in dfr.columns
                ]
        df["name"] = list(results.keys())

        count = 0
        for metric in metrics:
            if metric in metricMap.keys():
                plot = sns.barplot(data=df, x="name", y=metric, ax=axes[count])
                count += 1
                if metric == "time":
                    plot.set(xlabel="", ylabel="time (secs)")
                else:
                    plot.set(xlabel="")
        return fig
