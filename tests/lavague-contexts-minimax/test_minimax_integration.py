"""Integration tests for MiniMax context (requires MINIMAX_API_KEY)."""

import os
import pytest

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
pytestmark = pytest.mark.skipif(
    not MINIMAX_API_KEY, reason="MINIMAX_API_KEY not set"
)


class TestMiniMaxEmbeddingIntegration:
    """Integration tests for MiniMaxEmbedding against the real API."""

    def _make_embedding(self):
        from lavague.contexts.minimax.base import MiniMaxEmbedding

        return MiniMaxEmbedding(api_key=MINIMAX_API_KEY)

    def test_single_text_embedding(self):
        emb = self._make_embedding()
        result = emb._get_text_embedding("Hello, world!")
        assert isinstance(result, list)
        assert len(result) == 1536  # embo-01 produces 1536-dim vectors
        assert all(isinstance(v, float) for v in result)

    def test_query_embedding(self):
        emb = self._make_embedding()
        result = emb._get_query_embedding("What is machine learning?")
        assert isinstance(result, list)
        assert len(result) == 1536

    def test_batch_embeddings(self):
        emb = self._make_embedding()
        result = emb._get_text_embeddings(["Hello", "World", "Test"])
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(len(v) == 1536 for v in result)


class TestMiniMaxLLMIntegration:
    """Integration tests for MiniMax LLM via OpenAILike."""

    def _make_llm(self):
        from llama_index.llms.openai_like import OpenAILike

        return OpenAILike(
            api_key=MINIMAX_API_KEY,
            api_base="https://api.minimax.io/v1",
            model="MiniMax-M2.7",
            max_tokens=64,
            temperature=0.0,
            is_chat_model=True,
        )

    def test_complete(self):
        llm = self._make_llm()
        response = llm.complete("Say hello in one word.")
        assert response.text
        assert len(response.text) > 0

    def test_chat(self):
        from llama_index.core.llms import ChatMessage, MessageRole

        llm = self._make_llm()
        messages = [
            ChatMessage(role=MessageRole.USER, content="Say hello in one word."),
        ]
        response = llm.chat(messages)
        assert response.message.content
        assert len(response.message.content) > 0
