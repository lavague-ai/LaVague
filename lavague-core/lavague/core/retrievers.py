from __future__ import annotations
from typing import List, Optional, Tuple
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup, NavigableString
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import Document, VectorStoreIndex, QueryBundle
from llama_index.core.schema import NodeWithScore, TextNode
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llama_index.core.node_parser import LangchainNodeParser
from llama_index.core.embeddings import BaseEmbedding
from lavague.core.extractors import extract_xpaths_from_html
from lavague.core.base_driver import BaseDriver, PossibleInteractionsByXpath
from lavague.core.utilities.format_utils import clean_html
import re
import ast


def get_default_retriever(
    driver: BaseDriver, embedding: Optional[BaseEmbedding] = None
) -> BaseHtmlRetriever:
    return RetrieversPipeline(
        InteractiveXPathRetriever(driver),
        FromXPathNodesExpansionRetriever(),
        SemanticRetriever(embedding=embedding),
    )


class BaseHtmlRetriever(ABC):
    @abstractmethod
    def retrieve(
        self, query: QueryBundle, html_nodes: List[str], viewport_only=True
    ) -> List[str]:
        """
        This method must be implemented by the child retriever
        """
        pass


class RetrieversPipeline(BaseHtmlRetriever):
    """Executor for retrievers pipeline"""

    retrievers: Tuple[BaseHtmlRetriever]

    def __init__(self, *retrievers: BaseHtmlRetriever):
        self.retrievers = retrievers

    def retrieve(
        self, query: QueryBundle, html_nodes: List[str], viewport_only=True
    ) -> List[str]:
        for retriever in self.retrievers:
            html_nodes = retriever.retrieve(query, html_nodes, viewport_only)
        return html_nodes


class UniqueXPathRetriever(BaseHtmlRetriever):
    """Retriever that removes rendudancy when elements have the same bounding box"""

    def __init__(self, driver: BaseDriver) -> None:
        self.driver = driver

    def retrieve(
        self, query: QueryBundle, html_nodes: List[str], viewport_only=True
    ) -> List[str]:
        html = merge_html_chunks(html_nodes)
        xpaths = extract_xpaths_from_html(html)

        js_function = """
        function getUniqueElementsWithXPaths(xpaths) {
            const uniqueElements = [];
            const boundingBoxes = new Set();

            xpaths.forEach(xpath => {
                const elements = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                for (let i = 0; i < elements.snapshotLength; i++) {
                    const element = elements.snapshotItem(i);
                    const rect = element.getBoundingClientRect();
                    const boundingBox = `${rect.x},${rect.y},${rect.width},${rect.height}`;

                    if (!boundingBoxes.has(boundingBox)) {
                        boundingBoxes.add(boundingBox);
                        const clonedElement = element.cloneNode(true);
                        clonedElement.setAttribute('xpath', xpath);
                        uniqueElements.push(clonedElement.outerHTML);
                        break;  // We only need one unique element per XPath
                    }
                }
            });

            return uniqueElements;
        }
        return getUniqueElementsWithXPaths(arguments[0]);
        """

        html_chunks = self.driver.execute_script(js_function, xpaths)

        return html_chunks


class BM25HtmlRetriever(BaseHtmlRetriever):
    """Mainly for benchmarks, do not use it as the performances are not up to par with the other retrievers"""

    def __init__(self, top_k=3) -> None:
        self.top_k = top_k

    def retrieve(
        self, query: QueryBundle, html_chunks: List[str], viewport_only=True
    ) -> List[str]:
        html = clean_html(merge_html_chunks(html_chunks))
        cleaned_html = clean_html(html)

        splitter = LangchainNodeParser(
            lc_splitter=RecursiveCharacterTextSplitter.from_language(
                language="html",
            )
        )
        nodes = splitter.get_nodes_from_documents([Document(text=cleaned_html)])

        retriever = BM25Retriever.from_defaults(
            nodes=nodes, similarity_top_k=self.top_k
        )
        nodes = retriever.retrieve(query)
        return get_nodes_text(nodes)


class InteractiveXPathRetriever(BaseHtmlRetriever):
    def __init__(self, driver: BaseDriver):
        self.driver = driver

    def retrieve(
        self, query: QueryBundle, html_chunks: List[str], viewport_only=True
    ) -> List[str]:
        html = merge_html_chunks(html_chunks)
        possible_interactions = self.driver.get_possible_interactions(
            in_viewport=viewport_only
        )
        html = self.get_html_with_xpath(html, possible_interactions)
        return [html]

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

    def get_html_with_xpath(
        self,
        html_content,
        filter_by_possible_interactions: Optional[PossibleInteractionsByXpath],
        xpath_prefix="",
    ):
        soup = BeautifulSoup(html_content, "html.parser")
        for element in soup.find_all(True):
            xpath = xpath_prefix + self._generate_xpath(element)
            if (
                filter_by_possible_interactions is None
                or xpath in filter_by_possible_interactions
            ):
                element["xpath"] = xpath
        for iframe_tag in soup.find_all("iframe"):
            frame_xpath = self._generate_xpath(iframe_tag)
            try:
                self.driver.switch_frame(frame_xpath)
            except Exception:
                continue
            frame_soup_str = self.get_html_with_xpath(
                self.driver.get_html(),
                filter_by_possible_interactions,
                xpath_prefix + frame_xpath,
            )
            iframe_tag.replace_with(frame_soup_str)
            self.driver.switch_parent_frame()
        return str(soup)


class OpsmSplitRetriever(BaseHtmlRetriever):
    def __init__(
        self,
        driver: BaseDriver,
        top_k: int = 5,
        group_by: int = 10,
        rank_fields: List[str] = ["element", "placeholder", "text", "name"],
    ):
        self.driver = driver
        self.top_k = top_k
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

    def retrieve(
        self, query: QueryBundle, html_nodes: List[str], viewport_only=True
    ) -> List[str]:
        html = self._add_xpath_attributes(merge_html_chunks(html_nodes))
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
        return get_nodes_text(results)


class XPathedChunkRetriever(BaseHtmlRetriever):
    def retrieve(
        self, query: QueryBundle, html_chunks: List[str], viewport_only=True
    ) -> List[str]:
        pattern = re.compile(r'xpath="([^"]+)"')
        interactive_chunks = []
        for chunk in html_chunks:
            match = re.search(pattern, chunk)
            if match:
                interactive_chunks.append(chunk)
        return interactive_chunks


class FromXPathNodesExpansionRetriever(BaseHtmlRetriever):
    """
    Retriever with expansion of HTML context around interactive elements (`chunk_size` in characters),
    then semantic contraction up to `top_k` results (number of chunks).
    Expansion is symmetrical so every step will add previous and next sibling.
    If no more sibling is present, then context is extended to parent node.
    When interactive chunks intersect, they are merged together.
    """

    def __init__(
        self,
        chunk_size: int = 750,
    ):
        self.chunk_size = chunk_size

    def get_included_xpaths(self, element) -> List[str]:
        if isinstance(element, NavigableString):
            return []
        xpaths = [e["xpath"] for e in element.find_all(attrs={"xpath": True})]
        if "xpath" in element.attrs:
            xpaths.append(element["xpath"])
        return xpaths

    def get_expanded_chunks(self, html_chunks: List[str]) -> List[str]:
        html = merge_html_chunks(html_chunks)
        soup = BeautifulSoup(html, "html.parser")
        elements = soup.find_all(attrs={"xpath": True})
        chunks = []
        processed_xpaths = set()

        def include_html(sibling) -> Optional[str]:
            sibling_xpaths = self.get_included_xpaths(sibling)
            if processed_xpaths.isdisjoint(sibling_xpaths):
                processed_xpaths.update(sibling_xpaths)
                return str(sibling)

        # For each marked element
        for element in elements:
            xpath = element["xpath"]
            if xpath in processed_xpaths:
                continue

            chunk = str(element)
            processed_xpaths.update(self.get_included_xpaths(element))
            expanding = len(chunk) < self.chunk_size

            # Expand to siblings, then parent until we reach the chunk size
            while expanding:
                previous_size = len(chunk)
                previous_sibling = element.previous_sibling
                next_sibling = element.next_sibling

                # Add siblings to the chunk, from the closest to the farthest ones
                while len(chunk) < self.chunk_size and (
                    previous_sibling or next_sibling
                ):
                    if previous_sibling:
                        add_html = include_html(previous_sibling)
                        if add_html:
                            chunk += add_html
                            previous_sibling = previous_sibling.previous_sibling
                        else:
                            previous_sibling = None
                    if next_sibling:
                        add_html = include_html(next_sibling)
                        if add_html:
                            chunk = chunk + add_html
                            next_sibling = next_sibling.next_sibling
                        else:
                            next_sibling = None

                # Move to parent if no more siblings can be added
                if len(chunk) < self.chunk_size and element.parent:
                    element = element.parent
                    chunk = str(element)
                    parent_xpaths = set(self.get_included_xpaths(element))
                    processed_xpaths.update(parent_xpaths)

                    # Remove previous chunks that are now included in the parent
                    chunks = [c for c in chunks if c not in chunk]

                expanding = len(chunk) < self.chunk_size and len(chunk) > previous_size

            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def retrieve(
        self, query: QueryBundle, html_chunks: List[str], viewport_only=True
    ) -> List[str]:
        results = self.get_expanded_chunks(html_chunks)
        return results


class SemanticRetriever(BaseHtmlRetriever):
    """
    Semantic retriever up to `top_k` results (number of chunks)
    """

    def __init__(
        self,
        embedding: Optional[BaseEmbedding],
        top_k: int = 10,
        xpathed_only=True,
    ):
        self.top_k = top_k
        self.xpathed_only = xpathed_only
        self.embedding = embedding

    def retrieve(
        self, query: QueryBundle, html_chunks: List[str], viewport_only=True
    ) -> List[str]:
        splitter = LangchainNodeParser(
            lc_splitter=RecursiveCharacterTextSplitter.from_language(
                language="html",
            )
        )
        nodes = splitter.get_nodes_from_documents(
            [Document(text=merge_html_chunks(html_chunks))]
        )

        if self.xpathed_only:
            nodes = filter_for_xpathed_nodes(nodes)

        index = VectorStoreIndex(nodes=nodes, embed_model=self.embedding)
        query_engine = index.as_retriever(similarity_top_k=self.top_k)

        retrieved_nodes = query_engine.retrieve(query)
        return get_nodes_text(retrieved_nodes)


class SyntaxicRetriever(BaseHtmlRetriever):
    """
    Syntaxic retriever up to `top_k` results (number of chunks)
    """

    def __init__(
        self,
        top_k: int = 5,
        xpathed_only=True,
    ):
        self.top_k = top_k
        self.xpathed_only = xpathed_only

    def retrieve(
        self, query: QueryBundle, html_chunks: List[str], viewport_only=True
    ) -> List[str]:
        documents = [Document(text=merge_html_chunks(html_chunks))]
        splitter = LangchainNodeParser(
            lc_splitter=RecursiveCharacterTextSplitter.from_language(
                language="html",
            )
        )
        nodes = splitter.get_nodes_from_documents(documents)
        if self.xpathed_only:
            nodes = filter_for_xpathed_nodes(nodes)

        retriever = BM25Retriever.from_defaults(
            nodes=nodes, similarity_top_k=self.top_k
        )
        results = retriever.retrieve(query)
        return get_nodes_text(results)


def filter_for_xpathed_nodes(nodes: List):
    pattern = re.compile(r'xpath="([^"]+)"')
    compatibles = []
    for node in nodes:
        match = re.search(pattern, node.text)
        if match:
            compatibles.append(node)
    return compatibles if len(compatibles) > 0 else nodes


def get_nodes_text(nodes: List[NodeWithScore]) -> List[str]:
    return [n.text for n in nodes]


def merge_html_chunks(html_chunks: List[str], separator="\n") -> str:
    return separator.join(html_chunks)
