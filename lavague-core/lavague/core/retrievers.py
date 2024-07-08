from __future__ import annotations
from typing import List
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import Document
from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llama_index.core.node_parser import LangchainNodeParser
from lavague.core.base_driver import BaseDriver
from lavague.core.utilities.format_utils import clean_html
import re


class BaseHtmlRetriever(ABC):
    def __init__(self, driver: BaseDriver, top_k: int = 3):
        self.driver = driver
        self.top_k = top_k

    @abstractmethod
    def retrieve_html(self, query: QueryBundle) -> List[NodeWithScore]:
        """
        This method should be implemented by the user
        """
        pass


class BM25HtmlRetriever(BaseHtmlRetriever):
    """Mainly for benchmarks, do not use it as the performances are not up to par with the other retrievers"""

    def retrieve_html(self, query: QueryBundle) -> List[NodeWithScore]:
        text_list = [clean_html(self.driver.get_html())]
        documents = [Document(text=t) for t in text_list]

        splitter = LangchainNodeParser(
            lc_splitter=RecursiveCharacterTextSplitter.from_language(
                language="html",
            )
        )
        nodes = splitter.get_nodes_from_documents(documents)
        retriever = BM25Retriever.from_defaults(
            nodes=nodes, similarity_top_k=self.top_k
        )
        return retriever.retrieve(query)


class OpsmSplitRetriever(BaseHtmlRetriever):
    def __init__(
        self,
        driver: BaseDriver,
        top_k: int = 5,
    ):
        super().__init__(driver, top_k)

    def _generate_xpath(self, element, path=""):  # used to generate dict nodes
        """Recursive function to generate the xpath of an element"""
        if element.parent is None:
            return path
        else:
            siblings = [
                sib for sib in element.parent.children if sib.name == element.name
            ]
            if len(siblings) > 1:
                count = siblings.index(element) + 1
                if count == 1:
                    path = f"/{element.name}{path}"
                else:
                    path = f"/{element.name}[{count}]{path}"
            else:
                path = f"/{element.name}{path}"
            return self._generate_xpath(element.parent, path)

    def _add_xpath_attributes(self, html_content, xpath_prefix=""):
        soup = BeautifulSoup(html_content, "html.parser")
        for element in soup.find_all(True):
            element["xpath"] = xpath_prefix + self._generate_xpath(element)
        for iframe_tag in soup.find_all("iframe"):
            frame_xpath = self._generate_xpath(iframe_tag)
            try:
                self.driver.resolve_xpath(frame_xpath)
            except Exception as e:
                continue
            frame_soup_str = self._add_xpath_attributes(
                self.driver.get_html(), xpath_prefix + frame_xpath
            )
            iframe_tag.replace_with(frame_soup_str)
            self.driver.driver.switch_to.parent_frame()
        return str(soup)

    def _get_interactable_nodes(self, html):
        documents = [Document(text=html)]
        splitter = LangchainNodeParser(
            lc_splitter=RecursiveCharacterTextSplitter.from_language(
                language="html",
            )
        )
        nodes = splitter.get_nodes_from_documents(documents)
        pattern = re.compile(r'xpath="([^"]+)"')
        possible_interactions = self.driver.get_possible_interactions()
        compatibles = []
        for node in nodes:
            xpaths = re.findall(pattern, node.text)
            for xpath in xpaths:
                if xpath in possible_interactions:
                    compatibles.append(node)
                    break
        return compatibles if len(compatibles) > 0 else nodes

    def retrieve_html(self, query: QueryBundle) -> List[NodeWithScore]:
        html = self._add_xpath_attributes(self.driver.get_html())
        nodes = self._get_interactable_nodes(html)
        retriever = BM25Retriever.from_defaults(
            nodes=nodes, similarity_top_k=self.top_k
        )
        results = retriever.retrieve(query)
        return results
