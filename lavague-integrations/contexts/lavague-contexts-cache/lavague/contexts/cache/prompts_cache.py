from typing import Dict, Optional, List
import yaml
from enum import Enum
from re import match


class PromptCacheConfigType(Enum):
    """Type of prompt comparison performed"""

    TEXT = "text"
    REGEX = "regex"


class PromptCacheConfig:
    """Map prompt input with static output"""

    prompt: str
    output: str
    type: str

    def __init__(
        self,
        prompt: str,
        output: str,
        type: PromptCacheConfigType = PromptCacheConfigType.TEXT,
    ) -> None:
        self.prompt = prompt
        self.output = output
        self.type = type

    def matches_prompt(self, prompt: str) -> bool:
        if self.type == PromptCacheConfigType.TEXT:
            return self.prompt == prompt
        elif self.type == PromptCacheConfigType.REGEX:
            return match(self.prompt, prompt) is not None


class PromptsCache:
    """Utility class to map prompts with static outputs"""

    prompts_config: List[PromptCacheConfig] = []
    yml_prompts_file: Optional[str]
    yml_record_new_prompts: bool = True
    is_cache_disabled = False

    def __init__(
        self,
        prompts: Optional[Dict[str, any]] = None,
        yml_prompts_file: Optional[str] = None,
    ) -> None:
        self.yml_prompts_file = yml_prompts_file
        if prompts is not None:
            for prompt in prompts:
                self.prompts_config.append(PromptCacheConfig(prompt, prompts[prompt]))
        if yml_prompts_file is not None:
            self.add_from_yml_file(yml_prompts_file)

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
            config = PromptCacheConfig(
                c["prompt"],
                c["output"],
                PromptCacheConfigType.TEXT
                if "type" not in c
                else PromptCacheConfigType(c["type"]),
            )
            self.prompts_config.append(config)
        return self

    def get_for_prompt(self, prompt: str) -> str:
        if self.is_cache_disabled:
            return None
        for config in self.prompts_config:
            if config.matches_prompt(prompt):
                return config.output

    def add_prompt(self, prompt: str, output: str) -> bool:
        if self.is_cache_disabled:
            return False

        self.prompts_config.append(PromptCacheConfig(prompt, output))
        if self.yml_record_new_prompts and self.yml_prompts_file is not None:
            with open(self.yml_prompts_file, "a") as outfile:
                outfile.write("\n")
                yaml.dump(
                    [{"prompt": prompt, "output": output}], outfile, sort_keys=False
                )
        return True
