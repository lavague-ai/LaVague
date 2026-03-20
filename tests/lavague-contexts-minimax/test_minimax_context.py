"""Unit tests for MiniMax context integration."""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestMiniMaxEmbedding:
    """Tests for MiniMaxEmbedding class."""

    def _make_embedding(self, api_key="test-key"):
        from lavague.contexts.minimax.base import MiniMaxEmbedding

        return MiniMaxEmbedding(api_key=api_key)

    def test_init_defaults(self):
        emb = self._make_embedding()
        assert emb.model_name == "embo-01"
        assert emb._api_key == "test-key"
        assert emb._api_base == "https://api.minimax.io/v1"

    def test_init_custom_model(self):
        from lavague.contexts.minimax.base import MiniMaxEmbedding

        emb = MiniMaxEmbedding(api_key="k", model_name="custom-model")
        assert emb.model_name == "custom-model"

    def test_init_custom_api_base(self):
        from lavague.contexts.minimax.base import MiniMaxEmbedding

        emb = MiniMaxEmbedding(api_key="k", api_base="https://custom.api/v1")
        assert emb._api_base == "https://custom.api/v1"

    @patch("lavague.contexts.minimax.base.requests.post")
    def test_get_text_embedding(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "vectors": [[0.1, 0.2, 0.3]],
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        emb = self._make_embedding()
        result = emb._get_text_embedding("hello")

        assert result == [0.1, 0.2, 0.3]
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["type"] == "db"
        assert call_kwargs[1]["json"]["texts"] == ["hello"]
        assert call_kwargs[1]["json"]["model"] == "embo-01"

    @patch("lavague.contexts.minimax.base.requests.post")
    def test_get_query_embedding(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "vectors": [[0.4, 0.5, 0.6]],
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        emb = self._make_embedding()
        result = emb._get_query_embedding("search query")

        assert result == [0.4, 0.5, 0.6]
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["type"] == "query"

    @patch("lavague.contexts.minimax.base.requests.post")
    def test_get_text_embeddings_batch(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "vectors": [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        emb = self._make_embedding()
        result = emb._get_text_embeddings(["a", "b", "c"])

        assert len(result) == 3
        assert result[0] == [0.1, 0.2]
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["texts"] == ["a", "b", "c"]

    @patch("lavague.contexts.minimax.base.requests.post")
    def test_api_url_construction(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "vectors": [[0.1]],
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        emb = self._make_embedding()
        emb._get_text_embedding("test")

        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.minimax.io/v1/embeddings"

    @patch("lavague.contexts.minimax.base.requests.post")
    def test_auth_header(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "vectors": [[0.1]],
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        emb = self._make_embedding(api_key="my-secret-key")
        emb._get_text_embedding("test")

        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["headers"]["Authorization"] == "Bearer my-secret-key"

    @patch("lavague.contexts.minimax.base.requests.post")
    def test_api_error_raises(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_resp

        emb = self._make_embedding()
        with pytest.raises(Exception, match="API Error"):
            emb._get_text_embedding("test")

    @patch("lavague.contexts.minimax.base.requests.post")
    def test_api_body_error_raises(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "vectors": None,
            "base_resp": {"status_code": 1004, "status_msg": "invalid api key"},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        emb = self._make_embedding()
        with pytest.raises(RuntimeError, match="invalid api key"):
            emb._get_text_embedding("test")

    @patch("lavague.contexts.minimax.base.time.sleep")
    @patch("lavague.contexts.minimax.base.requests.post")
    def test_rate_limit_retry(self, mock_post, mock_sleep):
        rate_resp = MagicMock()
        rate_resp.json.return_value = {
            "vectors": None,
            "base_resp": {"status_code": 1002, "status_msg": "rate limit exceeded"},
        }
        rate_resp.raise_for_status = MagicMock()

        ok_resp = MagicMock()
        ok_resp.json.return_value = {
            "vectors": [[0.1, 0.2]],
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
        ok_resp.raise_for_status = MagicMock()

        mock_post.side_effect = [rate_resp, ok_resp]

        emb = self._make_embedding()
        result = emb._get_text_embedding("test")

        assert result == [0.1, 0.2]
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(2)


class TestMiniMaxContext:
    """Tests for MiniMaxContext class."""

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_minimax_api_key_raises(self):
        from lavague.contexts.minimax.base import MiniMaxContext

        with pytest.raises(ValueError, match="MINIMAX_API_KEY is not set"):
            MiniMaxContext()

    @patch.dict(
        os.environ, {"MINIMAX_API_KEY": "mm-key"}, clear=True
    )
    def test_missing_openai_api_key_raises(self):
        from lavague.contexts.minimax.base import MiniMaxContext

        with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
            MiniMaxContext()

    @patch.dict(
        os.environ,
        {"MINIMAX_API_KEY": "mm-key", "OPENAI_API_KEY": "oai-key"},
        clear=True,
    )
    def test_context_creation_from_env(self):
        from lavague.contexts.minimax.base import MiniMaxContext

        ctx = MiniMaxContext()
        assert ctx.llm is not None
        assert ctx.mm_llm is not None
        assert ctx.embedding is not None
        assert ctx.extraction_llm is not None

    def test_context_creation_explicit_keys(self):
        from lavague.contexts.minimax.base import MiniMaxContext

        ctx = MiniMaxContext(api_key="mm-key", openai_api_key="oai-key")
        assert ctx.llm is not None
        assert ctx.mm_llm is not None
        assert ctx.embedding is not None

    def test_default_model(self):
        from lavague.contexts.minimax.base import MiniMaxContext

        ctx = MiniMaxContext(api_key="mm-key", openai_api_key="oai-key")
        assert ctx.llm.model == "MiniMax-M2.7"

    def test_custom_model(self):
        from lavague.contexts.minimax.base import MiniMaxContext

        ctx = MiniMaxContext(
            api_key="mm-key",
            openai_api_key="oai-key",
            llm="MiniMax-M2.5-highspeed",
        )
        assert ctx.llm.model == "MiniMax-M2.5-highspeed"

    def test_extraction_llm_higher_max_tokens(self):
        from lavague.contexts.minimax.base import MiniMaxContext

        ctx = MiniMaxContext(api_key="mm-key", openai_api_key="oai-key")
        assert ctx.extraction_llm.max_tokens == 4096
        assert ctx.llm.max_tokens == 512  # DEFAULT_MAX_TOKENS

    def test_llm_api_base(self):
        from lavague.contexts.minimax.base import MiniMaxContext

        ctx = MiniMaxContext(api_key="mm-key", openai_api_key="oai-key")
        assert ctx.llm.api_base == "https://api.minimax.io/v1"

    def test_embedding_is_minimax(self):
        from lavague.contexts.minimax.base import MiniMaxContext, MiniMaxEmbedding

        ctx = MiniMaxContext(api_key="mm-key", openai_api_key="oai-key")
        assert isinstance(ctx.embedding, MiniMaxEmbedding)
        assert ctx.embedding.model_name == "embo-01"

    def test_mm_llm_is_openai(self):
        from lavague.contexts.minimax.base import MiniMaxContext

        ctx = MiniMaxContext(api_key="mm-key", openai_api_key="oai-key")
        assert ctx.mm_llm.model == "gpt-4o"

    def test_import_from_package(self):
        from lavague.contexts.minimax import MiniMaxContext

        assert MiniMaxContext is not None


class TestMiniMaxConstants:
    """Tests for module-level constants."""

    def test_api_base_url(self):
        from lavague.contexts.minimax.base import MINIMAX_API_BASE

        assert MINIMAX_API_BASE == "https://api.minimax.io/v1"
