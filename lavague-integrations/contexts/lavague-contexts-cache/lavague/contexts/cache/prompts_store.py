from typing import Dict, Optional, List, TypeVar, Generic
from abc import ABC, abstractmethod
import yaml
import hashlib

T = TypeVar("T")


class PromptsStore(ABC, Generic[T]):
    """Utility class to map prompts with static outputs"""

    record_new_prompts: bool = True
    is_cache_disabled = False
    hash_prompt = True

    @abstractmethod
    def _get_for_prompt(self, prompt: str) -> T:
        pass

    @abstractmethod
    def _add_prompt(self, prompt: str, output: T):
        pass

    def get_for_prompt(self, prompt: str) -> T:
        if self.is_cache_disabled:
            return None
        return self._get_for_prompt(self._to_prompt_key(prompt))

    def add_prompt(self, prompt: str, output: T) -> bool:
        if self.is_cache_disabled:
            return False

        print("add prompt", prompt)
        self._add_prompt(self._to_prompt_key(prompt), output)
        return True

    def _to_prompt_key(self, prompt: str) -> str:
        if self.hash_prompt:
            return hashlib.sha256(str.encode(prompt)).hexdigest()
        return prompt


class YamlPromptsStore(PromptsStore[str]):
    prompts: Dict[str, str] = None
    yml_prompts_file: Optional[str]

    def __init__(
        self,
        prompts: Optional[Dict[str, any]] = None,
        yml_prompts_file: Optional[str] = None,
    ) -> None:
        self.prompts = prompts or {}
        self.yml_prompts_file = yml_prompts_file
        if yml_prompts_file is not None:
            self.add_from_yml_file(yml_prompts_file)
        super().__init__()

    def add_from_yml_file(self, file: str):
        try:
            with open(file) as stream:
                prompts = yaml.safe_load(stream)
                if prompts is not None:
                    self.add_from_yml(prompts)
        except IOError:
            pass
        return self

    def add_from_yml(self, config_list: List[Dict[str, any]]):
        for c in config_list:
            self.prompts[c["prompt"]] = c["output"]
        return self

    def _get_for_prompt(self, prompt: str) -> str:
        return self.prompts.get(prompt)

    def _add_prompt(self, prompt: str, output: str):
        self.prompts[prompt] = output

        if self.record_new_prompts and self.yml_prompts_file is not None:
            with open(self.yml_prompts_file, "a") as outfile:
                outfile.write("\n")
                yaml.dump(
                    [{"prompt": prompt, "output": output}], outfile, sort_keys=False
                )


class VectorStrPromptStore(PromptsStore[List[float]]):
    store: PromptsStore[str]
    dim_separator: str

    def __init__(
        self,
        store: Optional[PromptsStore[str]] = None,
        yml_prompts_file: Optional[str] = None,
        dim_separator: str = " ",
    ) -> None:
        self.store = store or YamlPromptsStore(yml_prompts_file=yml_prompts_file)
        self.dim_separator = dim_separator

    def _get_for_prompt(self, prompt: str) -> List[float]:
        str_value = self.store.get_for_prompt(prompt)
        if str_value is None:
            return None

        return list(map(float, str_value.split(self.dim_separator)))

    def _add_prompt(self, prompt: str, output: List[float]):
        str_value = self.dim_separator.join(list(map(str, output)))
        self.store.add_prompt(prompt, str_value)
