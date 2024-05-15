from lavague.core.action_engine import ActionEngine
from lavague.core.context import Context, get_default_context
from lavague.core.extractors import PythonFromMarkdownExtractor
from lavague.core.prompt_templates import DefaultPromptTemplate
from lavague.core.retrievers import OpsmSplitRetriever
from lavague.core.world_model import WorldModel
from lavague.core.agents import WebAgent

import os
import warnings


def telemetry_warning():
    telemetry_var = os.getenv("TELEMETRY_VAR")
    if telemetry_var != "NONE":
        warning_message = "\033[93mTelemetry is turned on. To turn off telemetry, set your TELEMETRY_VAR to 'NONE'\033[0m"
        warnings.warn(warning_message, UserWarning)


def exec_warning():
    warning_message = "\033[93mSecurity warning: This package executes LLM-generated code. Consider using this package in a sandboxed environment.\033[0m"
    warnings.warn(warning_message, UserWarning)


telemetry_warning()
exec_warning()
