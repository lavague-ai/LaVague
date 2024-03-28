from .action_engine import (
    BaseActionEngine,
    LocalActionEngine,
    extract_first_python_code,
)
from .driver import AbstractDriver
from .defaults import (
    default_get_driver,
    DefaultEmbedder,
    DefaultLLM,
)
from .prompts import DEFAULT_PROMPT

from typing import Tuple, Callable
import importlib.util
from pathlib import Path


def import_from_path(path):
    # Convert the path to a Python module path
    module_name = Path(path).stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_action_engine(
    path: str,
) -> Tuple[BaseActionEngine, Callable[[], AbstractDriver]]:
    config_module = import_from_path(path)
    get_driver = getattr(config_module, "get_driver", default_get_driver)
    llm = getattr(config_module, "LLM", DefaultLLM)()
    embedder = getattr(config_module, "Embedder", DefaultEmbedder)()

    prompt_template = getattr(config_module, "prompt_template", DEFAULT_PROMPT)
    cleaning_function = getattr(
        config_module, "cleaning_function", extract_first_python_code
    )

    action_engine = LocalActionEngine(llm, embedder, prompt_template, cleaning_function)

    return action_engine, get_driver


def load_instructions(path):
    with open(path, "r") as file:
        instructions = file.readlines()

        base_url = instructions[0].strip()
        instructions = [instruction.strip() for instruction in instructions[1:]]

    return base_url, instructions
