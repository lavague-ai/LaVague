from __future__ import annotations
from typing import List
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup, NavigableString
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import Document
from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore, TextNode
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llama_index.core.node_parser import LangchainNodeParser
from lavague.core.base_driver import BaseDriver, PossibleInteractionsByXpath
from lavague.core.utilities.format_utils import clean_html
import re
import ast


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
        group_by: int = 10,
        rank_fields: List[str] = ["element", "placeholder", "text", "name"],
    ):
        super().__init__(driver, top_k)
        self.group_by = group_by
        self.rank_fields = rank_fields

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
                path = f"/{element.name}[{count}]{path}"
            else:
                path = f"/{element.name}{path}"
            return self._generate_xpath(element.parent, path)

    def _add_xpath_attributes(self, html_content):
        """
        Add an 'xpath' attribute to each element in the HTML content with its computed XPath.
        """
        soup = BeautifulSoup(html_content, "lxml")
        for element in soup.find_all(True):
            xpath = self._generate_xpath(element)
            element["xpath"] = xpath
        return str(soup)

    def _create_nodes_dict(
        self, html, only_body=True, max_length=200
    ):  # used to generate dict nodes
        """Create a list of xpaths and a list of dict of attributes of all elements in the html"""
        soup = BeautifulSoup(html, "html.parser")
        if only_body:
            root = soup.body
        else:
            root = soup.html
        element_attributes_list = []
        stack = [root]  # stack to keep track of elements and their paths
        while stack:
            element = stack.pop()
            if element.name is not None:
                element_attrs = dict(element.attrs)
                direct_text_content = "".join(
                    [
                        str(content).strip()
                        for content in element.contents
                        if isinstance(content, NavigableString) and content.strip()
                    ]
                )
                if direct_text_content:
                    element_attrs["text"] = direct_text_content
                    element_attrs["element"] = element.name
                    for key in element_attrs:
                        if len(element_attrs[key]) > max_length:
                            element_attrs[key] = element_attrs[key][:max_length]
                    element_attributes_list.append(element_attrs)
                elif element_attrs != {}:
                    element_attrs["element"] = element.name
                    for key in element_attrs:
                        if len(element_attrs[key]) > max_length:
                            element_attrs[key] = element_attrs[key][:max_length]
                    element_attributes_list.append(element_attrs)
                for child in element.children:
                    if child.name is not None:
                        stack.append(child)
        return element_attributes_list

    def _chunk_dicts(self, dicts, chunk_size=10):
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

        grouped_chunks = []
        for chunk in chunks(dicts, chunk_size):
            all_keys = set(key for d in chunk for key in d.keys())
            grouped = {key: [] for key in all_keys}
            for d in chunk:
                for key in all_keys:
                    grouped[key].append(d.get(key, ""))
            grouped_chunks.append(grouped)
        return grouped_chunks

    def _unchunk_dicts(self, grouped_chunks):
        flat_list = []
        for group in grouped_chunks:
            max_length = max(len(v) for v in group.values())
            for i in range(max_length):
                new_dict = {}
                for key, values in group.items():
                    if i < len(values):
                        if values[i] != "":
                            new_dict[key] = values[i]
                if new_dict:
                    flat_list.append(new_dict)
        return flat_list

    def _clean_attributes(self, attributes_list):  # used to generate dict nodes
        if self.rank_fields:
            self.rank_fields.append("xpath")
            attributes_list = [
                {k: v for k, v in d.items() if k in self.rank_fields}
                for d in attributes_list
            ]
        attributes_list = [
            d
            for d in attributes_list
            if (
                not (
                    (len(list(d.keys())) == 2)
                    and (("element" in list(d.keys())) and "xpath" in list(d.keys()))
                )
            )
            or d == {}
        ]
        return attributes_list

    def _get_results(self, query, html):  # used to generate and retrieve dict nodes
        """Return the top_k elements of the html that are the most relevant to the query as Node objects with xpath in their metadata"""
        attributes_list = self._create_nodes_dict(html)
        # cleaning the attributes_list
        attributes_list = self._clean_attributes(attributes_list)
        # retrieving the top_k results

        list_of_results = []
        attributes_list = self._chunk_dicts(attributes_list, self.group_by)
        l = len(attributes_list)
        # grouping the attributes_list in groups of 1000 to avoid memory errors
        list_of_grouped_results = []
        for j in range(0, l, 1000):
            nodes = []
            attr = attributes_list[j : j + 1000]
            for d in attr:
                xpath = d.pop("xpath")
                nodes.append(TextNode(text=str(d), metadata={"xpath": xpath}))
            retriever = BM25Retriever.from_defaults(
                nodes=nodes, similarity_top_k=self.top_k
            )
            results = retriever.retrieve(query)
            list_of_grouped_results += results
        nodes = []
        for grouped_results in list_of_grouped_results:
            xpaths = grouped_results.metadata["xpath"]
            ds = self._unchunk_dicts([ast.literal_eval(grouped_results.text)])
            assert len(xpaths) == len(ds)
            for xpath, d in zip(xpaths, ds):
                nodes.append(TextNode(text=str(d), metadata={"xpath": xpath}))
        l2 = len(nodes)
        for j in range(0, l2, 1000):
            retriever = BM25Retriever.from_defaults(
                nodes=nodes[j : j + 1000], similarity_top_k=self.top_k
            )
            results = retriever.retrieve(query)
            list_of_results += results
        list_of_results = sorted(list_of_results, key=lambda x: x.score, reverse=True)
        results = list_of_results[: self.top_k]
        results_dict = [ast.literal_eval(r.text) for r in results]
        for i in range(len(results_dict)):
            results_dict[i]["xpath"] = results[i].metadata["xpath"]
        scores = [r.score for r in results]
        return results_dict, scores

    def _match_element(self, attributes, element_specs):
        i = 0
        for spec in element_specs:
            if attributes.get("xpath") == spec["xpath"]:
                return i
            i += 1
        return None

    def _return_nodes_with_xpath(self, nodes, results_dict, score):
        returned_nodes = []
        for node in nodes:
            split_html = node.text
            soup = BeautifulSoup(split_html, "html.parser")
            for element in soup.descendants:
                if not isinstance(element, NavigableString):
                    indice = self._match_element(element.attrs, results_dict)
                    if indice is not None:
                        node.metadata["score"] = score[indice]
                        returned_nodes.append(node)
                        break
        return returned_nodes

    def retrieve_html(self, query: QueryBundle) -> List[NodeWithScore]:
        html = self._add_xpath_attributes(self.driver.get_html())
        text_list = [html]
        documents = [Document(text=t) for t in text_list]
        splitter = LangchainNodeParser(
            lc_splitter=RecursiveCharacterTextSplitter.from_language(
                language="html",
            )
        )
        nodes = splitter.get_nodes_from_documents(documents)
        results_dict, score = self._get_results(query.query_str, html)
        for r in results_dict:
            if not self.driver.check_visibility(r["xpath"]):
                i = results_dict.index(r)
                results_dict.remove(r)
                score.pop(i)
        results_nodes = self._return_nodes_with_xpath(nodes, results_dict, score)
        results = [
            NodeWithScore(node=node, score=node.metadata["score"])
            for node in results_nodes
        ]
        return results


class IxpathRetriever(BaseHtmlRetriever):
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
            tag = element.name
            if tag in ["svg", "path", "circle", "g"]:
                tag = f"*[local-name() = '{tag}']"
            if len(siblings) > 1:
                count = siblings.index(element) + 1
                if count == 1:
                    path = f"/{tag}{path}"
                else:
                    path = f"/{tag}[{count}]{path}"
            else:
                path = f"/{tag}{path}"
            return self._generate_xpath(element.parent, path)

    def _add_xpath_attributes(
        self,
        html_content,
        possible_interactions: PossibleInteractionsByXpath,
        xpath_prefix="",
    ):
        soup = BeautifulSoup(html_content, "html.parser")
        for element in soup.find_all(True):
            xpath = xpath_prefix + self._generate_xpath(element)
            if xpath in possible_interactions:
                # we only mark interactive elements
                element["xpath"] = xpath
        for iframe_tag in soup.find_all("iframe"):
            frame_xpath = self._generate_xpath(iframe_tag)
            try:
                self.driver.switch_frame(frame_xpath)
            except Exception:
                continue
            frame_soup_str = self._add_xpath_attributes(
                self.driver.get_html(),
                possible_interactions,
                xpath_prefix + frame_xpath,
            )
            iframe_tag.replace_with(frame_soup_str)
            self.driver.switch_parent_frame()
        return str(soup)

    def _get_interactable_nodes(
        self, html: str, possible_interactions: PossibleInteractionsByXpath
    ):
        documents = [Document(text=html)]
        splitter = LangchainNodeParser(
            lc_splitter=RecursiveCharacterTextSplitter.from_language(
                language="html",
            )
        )
        nodes = splitter.get_nodes_from_documents(documents)
        pattern = re.compile(r'xpath="([^"]+)"')
        compatibles = []
        for node in nodes:
            xpaths = re.findall(pattern, node.text)
            for xpath in xpaths:
                if xpath in possible_interactions:
                    compatibles.append(node)
                    break
        return compatibles if len(compatibles) > 0 else nodes

    def retrieve_html(self, query: QueryBundle) -> List[NodeWithScore]:
        possible_interactions = self.driver.get_possible_interactions()
        html = self._add_xpath_attributes(self.driver.get_html(), possible_interactions)
        nodes = self._get_interactable_nodes(html, possible_interactions)
        retriever = BM25Retriever.from_defaults(
            nodes=nodes, similarity_top_k=self.top_k
        )
        results = retriever.retrieve(query)
        return results
