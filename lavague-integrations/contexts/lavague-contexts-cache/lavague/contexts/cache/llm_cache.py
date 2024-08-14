from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.llms import MockLLM as LlamaMockLLM
from llama_index.core.base.llms.types import CompletionResponse
from typing import Any, Dict, Optional
from lavague.contexts.cache.prompts_store import PromptsStore, YamlPromptsStore


class LLMCache(LlamaMockLLM):
    fallback: Optional[BaseLLM]
    store: PromptsStore[str] = None

    def __init__(
        self,
        prompts: Dict[str, str] = None,
        fallback: Optional[BaseLLM] = None,
        store: Optional[PromptsStore[str]] = None,
        yml_prompts_file: Optional[str] = "llm_prompts.yml",
    ) -> None:
        super().__init__()
        self.store = store or YamlPromptsStore(
            prompts=prompts,
            yml_prompts_file=yml_prompts_file,
        )
        self.fallback = fallback

    def complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponse:
        text = self.store.get_for_prompt(prompt)
        if text is None:
            if self.fallback is None:
                text = "(!) Missing LLM answer"
            else:
                text = self.fallback.complete(prompt, formatted, **kwargs).text
            self.store.add_prompt(prompt, text)
        return CompletionResponse(text=text)
