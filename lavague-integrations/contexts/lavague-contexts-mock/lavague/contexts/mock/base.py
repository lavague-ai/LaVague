from lavague.core.context import Context
from llama_index.core.multi_modal_llms import MultiModalLLM
from typing import Optional
from llama_index.core.base.llms.base import BaseLLM
from .mock_llm import MockLLM
from .mock_mm_llm import MockMultiModalLLM
from .mock_embedding import MockEmbedding


class MockContext(Context):
    def __init__(
        self,
        llm_fallback: Optional[BaseLLM] = None,
        mm_llm_fallback: Optional[MultiModalLLM] = None,
        yml_prompts_file: str = "prompts.yml",
    ) -> Context:
        return super().__init__(
            MockLLM(
                fallback=llm_fallback,
                yml_prompts_file=yml_prompts_file,
            ),
            MockMultiModalLLM(
                fallback=mm_llm_fallback,
                yml_prompts_file=yml_prompts_file,
            ),
            MockEmbedding(embed_dim=1),
        )
