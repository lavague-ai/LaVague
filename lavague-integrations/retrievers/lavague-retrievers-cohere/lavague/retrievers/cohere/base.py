from typing import Optional
from lavague.core.retrievers import OpsmSplitRetriever
import cohere


class CohereRetriever(OpsmSplitRetriever):
    """This retriever uses cohere as a backend, which means it will not use the provided embedding model (which can be None)"""

    def __init__(
        self,
        cohere_model: str = "rerank-english-v3.0",
        cohere_api_key: Optional[str] = None,
        top_k: int = 5,
        rank_fields=["element", "placeholder", "text", "name"],
    ):
        self.cohere_model = cohere_model
        self.cohere_session = cohere.Client(cohere_api_key)
        super().__init__(top_k=top_k, rank_fields=rank_fields)

    def _get_results(self, _embedding, query, html):
        attributes_list = self._create_nodes_dict(html)
        l = len(attributes_list)
        list_of_results = []
        for j in range(0, l, 1000):
            attr = attributes_list[j : j + 1000]
            results = self.cohere_session.rerank(
                model=self.cohere_model,
                query=query,
                documents=attr,
                top_n=self.top_k,
                return_documents=True,
                rank_fields=self.rank_fields,
            )
            results = [r.dict() for r in results.results]
            for r in results:
                r["index"] += j
            list_of_results += results
        list_of_results = sorted(
            list_of_results, key=lambda x: x["relevance_score"], reverse=True
        )
        results = list_of_results[: self.top_k]
        results_dict = [r["document"] for r in results]
        score = [r["relevance_score"] for r in results]
        return results_dict, score
