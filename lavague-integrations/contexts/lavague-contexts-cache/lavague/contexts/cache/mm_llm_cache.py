from lavague.contexts.cache.prompts_store import PromptsStore, YamlPromptsStore
from llama_index.core.multi_modal_llms import MultiModalLLM, MultiModalLLMMetadata
from llama_index.core.schema import ImageDocument
from llama_index.core.base.llms.types import (
    CompletionResponse,
    CompletionResponseGen,
    ChatMessage,
    ChatResponse,
    ChatResponseGen,
    CompletionResponseAsyncGen,
    ChatResponseAsyncGen,
)
from typing import Optional, Dict, Sequence, Any
import imagehash
from PIL import Image


class MultiModalLLMCache(MultiModalLLM):
    fallback: Optional[MultiModalLLM]
    store: PromptsStore[str] = None

    def __init__(
        self,
        prompts: Dict[str, any] = None,
        fallback: Optional[MultiModalLLM] = None,
        store: Optional[PromptsStore[str]] = None,
        yml_prompts_file: Optional[str] = "mm_llm_prompts.yml",
    ):
        super().__init__()
        self.store = store or YamlPromptsStore(
            prompts=prompts,
            yml_prompts_file=yml_prompts_file,
        )
        self.fallback = fallback

    def metadata(self) -> MultiModalLLMMetadata:
        return MultiModalLLMMetadata()

    def get_image_hash(self, image: ImageDocument) -> str:
        hash = imagehash.average_hash(Image.open(image.metadata["file_path"]))
        return str(hash)

    def complete(
        self, prompt: str, image_documents: Sequence[ImageDocument], **kwargs: Any
    ) -> CompletionResponse:
        hashes = list(map(self.get_image_hash, image_documents))
        full_prompt = " ".join([*hashes, prompt])
        text = self.store.get_for_prompt(full_prompt)
        if text is None:
            if self.fallback is None:
                text = "(!) Missing Multimodal LLM answer"
            else:
                text = self.fallback.complete(
                    full_prompt, image_documents, **kwargs
                ).text
            self.store.add_prompt(full_prompt, text)
        return CompletionResponse(text=text)

    def stream_complete(
        self, prompt: str, image_documents: Sequence[ImageDocument], **kwargs: Any
    ) -> CompletionResponseGen:
        """Streaming completion endpoint for Multi-Modal LLM."""

    def chat(
        self,
        messages: Sequence[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        """Chat endpoint for Multi-Modal LLM."""

    def stream_chat(
        self,
        messages: Sequence[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponseGen:
        """Stream chat endpoint for Multi-Modal LLM."""

    async def acomplete(
        self, prompt: str, image_documents: Sequence[ImageDocument], **kwargs: Any
    ) -> CompletionResponse:
        """Async completion endpoint for Multi-Modal LLM."""

    async def astream_complete(
        self, prompt: str, image_documents: Sequence[ImageDocument], **kwargs: Any
    ) -> CompletionResponseAsyncGen:
        """Async streaming completion endpoint for Multi-Modal LLM."""

    async def achat(
        self,
        messages: Sequence[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        """Async chat endpoint for Multi-Modal LLM."""

    async def astream_chat(
        self,
        messages: Sequence[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponseAsyncGen:
        """Async streaming chat endpoint for Multi-Modal LLM."""
