from abc import ABC, abstractmethod
from lavague.core.retrievers import BaseHtmlRetriever
from lavague.drivers.selenium import SeleniumDriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
import pandas as pd
from tqdm import tqdm
from time import time
from typing import List
from evaluate.visualization import radar_plot
from llama_index.core.llms import LLM
from lavague.core.context import get_default_context
from lavague.core.navigation import Rephraser
from bs4 import BeautifulSoup
import uuid
import os
from llama_index.core import QueryBundle
from matplotlib.figure import Figure

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
    chrome_options.add_argument('--proxy-server=127.0.0.1:9999')

    return webdriver.Chrome(options=chrome_options)

class SeleniumDriverForEval(SeleniumDriver):
    def check_visibility(self, xpath: str) -> bool:
        return True


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, dataset: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def compare(self, results: List[pd.DataFrame]) -> Figure:
        pass

    def _load_html(self, html: str, driver: SeleniumDriver):
        """Loads a specific HTML content into the browser."""
        file_path = f"tmp_{uuid.uuid4()}.html"

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(html)

        abs_file_path = os.path.abspath(file_path)

        # Use the file:/// protocol to load the local HTML file
        driver.get(f"file:///{abs_file_path}")

        os.remove(abs_file_path)

    def _extract_backend_node_ids(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        return set([tag['backend_node_id'] for tag in soup.find_all(attrs={"backend_node_id": True})])

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
    
    def rephrase_dataset(self, dataset: pd.DataFrame, csv_out_name: str, llm: LLM = None) -> pd.DataFrame:
        assert not os.path.isfile(csv_out_name)
        if llm is None:
            llm = get_default_context().llm
        rephraser = Rephraser(llm)
        for i, row in tqdm(dataset.iterrows()):
            rephrase_list = rephraser.rephrase_query(row["query"])
            dataset.at[i, "retriever_query"] = rephrase_list[0]['query']
            dataset.at[i, "llm_query"] = rephrase_list[0]['action']
        dataset.to_csv(csv_out_name)
        return dataset

    def evaluate(self, retriever: BaseHtmlRetriever, rephrased_dataset: pd.DataFrame, csv_out_name: str) -> pd.DataFrame:
        assert not os.path.isfile(csv_out_name)
        retriever.driver = self.driver
        retrieved_dataset = rephrased_dataset.copy()
        retrieved_dataset["html_id"] = self._gen_html_ids(rephrased_dataset)
        retrieved_dataset["recall_retriever"] = pd.Series(dtype='float')
        retrieved_dataset["precision_retriever"] = pd.Series(dtype='float')
        retrieved_dataset["source_nodes"] = pd.Series(dtype='str')
        retrieved_dataset["retrieval_time"] = pd.Series(dtype='float')
        try:
            for i, row in tqdm(retrieved_dataset.iterrows()):
                self._load_html(row["html_id"], self.driver)
                element = self.driver.driver.find_element(By.XPATH, row["xpath"])
                ground_truth_outer_html = self.driver.execute_script("return arguments[0].outerHTML", element)
                start_time = time()
                results = retriever.retrieve_html(QueryBundle(row["retriever_query"]))
                duration = time() - start_time
                source_nodes = [node.text for node in results]
                context_str = "\n".join(source_nodes)
                recall_retriever, precision_retriever = self._intersection_backend_node_id(ground_truth_outer_html, context_str)
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

    def compare(self, results: List[pd.DataFrame]):
        data = []
        for df in results.values():
            data.append(df[['recall_retriever', 'precision_retriever', 'retrieval_time']].mean(axis=0).to_dict())
        return radar_plot(data, results.keys(), invert_range=["retrieval_time"], config={"theta_tick_lbls_pad": 10})


    def _gen_html_ids(self, df: pd.DataFrame):
        def add_ids_to_tags(html_string):
            soup = BeautifulSoup(html_string, 'html.parser')
            node_id = 1
            for tag in soup.find_all(True):  # The True argument here finds all tags
                tag['backend_node_id'] = str(node_id)
                node_id += 1
            return str(soup)

        return df['html'].apply(lambda x: add_ids_to_tags(x))

class LLMEvaluator(Evaluator):
    def __init__(self):
        self.driver = SeleniumDriverForEval(get_selenium_driver=init_driver)

    def evaluate(self, llm: LLM, retrieved_dataset: pd.DataFrame, csv_out_name: str) -> pd.DataFrame:
        llm_dataset = retrieved_dataset.copy()
        llm_dataset['recall_llm'] = pd.Series(dtype='float')
        llm_dataset['precision_llm'] = pd.Series(dtype='float')
        llm_dataset['execution_error'] = pd.Series(dtype='str')
        llm_dataset['target_outer_html'] = pd.Series(dtype='str')
        llm_dataset['generated_code'] = pd.Series(dtype='str')
