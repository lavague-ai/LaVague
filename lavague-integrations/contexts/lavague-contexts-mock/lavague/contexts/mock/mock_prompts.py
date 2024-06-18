import logging
from typing import Dict, Optional, List
import yaml
from enum import Enum
from re import match

logging_print = logging.getLogger(__name__)
logging_print.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(format)
logging_print.addHandler(ch)
logging_print.propagate = False


class MockPromptConfigType(Enum):
    """Type of prompt comparison performed"""

    TEXT = "text"
    REGEX = "regex"


class MockPromptConfig:
    """Map prompt input with static output"""

    prompt: str
    output: str
    type: str

    def __init__(
        self,
        prompt: str,
        output: str,
        type: MockPromptConfigType = MockPromptConfigType.TEXT,
    ) -> None:
        self.prompt = prompt
        self.output = output
        self.type = type

    def matches_prompt(self, prompt: str) -> bool:
        if self.type == MockPromptConfigType.TEXT:
            return self.prompt == prompt
        elif self.type == MockPromptConfigType.REGEX:
            return match(self.prompt, prompt) is not None


class MockPrompts:
    """Utility class to map prompts with static outputs"""

    prompts_config: List[MockPromptConfig] = []
    yml_prompts_file: Optional[str]
    yml_record_new_prompts: bool = True

    def __init__(
        self,
        prompts: Optional[Dict[str, any]] = None,
        yml_prompts_file: Optional[str] = None,
    ) -> None:
        self.yml_prompts_file = yml_prompts_file
        if prompts is not None:
            for prompt in prompts:
                self.prompts_config.append(MockPromptConfig(prompt, prompts[prompt]))
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
            config = MockPromptConfig(
                c["prompt"],
                c["output"],
                MockPromptConfigType.TEXT
                if "type" not in c
                else MockPromptConfigType(c["type"]),
            )
            self.prompts_config.append(config)
        return self

    def get_for_prompt(self, prompt: str) -> str:
        for config in self.prompts_config:
            if config.matches_prompt(prompt):
                return config.output

    def add_prompt(self, prompt: str, output: str):
        logging_print.info(f"New mock prompt: {prompt}")
        self.prompts_config.append(MockPromptConfig(prompt, output))
        if self.yml_record_new_prompts and self.yml_prompts_file is not None:
            with open(self.yml_prompts_file, "a") as outfile:
                outfile.write("\n")
                yaml.dump(
                    [{"prompt": prompt, "output": output}], outfile, sort_keys=False
                )
