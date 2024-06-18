from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.llms import MockLLM as LlamaMockLLM
from llama_index.core.base.llms.types import CompletionResponse
from llama_index.core.types import PydanticProgramMode
from typing import Any, Dict, Optional
from .mock_prompts import MockPrompts


class MockLLM(LlamaMockLLM, MockPrompts):
    fallback: Optional[BaseLLM]
    yml_prompts_file: Optional[str]

    def __init__(
        self,
        prompts: Dict[str, str] = None,
        pydantic_program_mode: PydanticProgramMode = PydanticProgramMode.DEFAULT,
        fallback: Optional[BaseLLM] = None,
        yml_prompts_file: Optional[str] = None,
    ) -> None:
        LlamaMockLLM.__init__(
            self,
            pydantic_program_mode=pydantic_program_mode,
        )
        MockPrompts.__init__(
            self,
            prompts=prompts,
            yml_prompts_file=yml_prompts_file,
        )
        self.fallback = fallback

    def complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponse:
        text = self.get_for_prompt(prompt)
        if text is None:
            if self.fallback is None:
                text = "(!) Missing LLM mock answer"
            else:
                text = self.fallback.complete(prompt, formatted, **kwargs).text
            self.add_prompt(prompt, text)
        return CompletionResponse(text=text)
