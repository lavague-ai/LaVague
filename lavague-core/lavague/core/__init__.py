from lavague.core.python_engine import PythonEngine
from lavague.core.context import Context, get_default_context
from lavague.core.extractors import (
    PythonFromMarkdownExtractor,
    JsonFromMarkdownExtractor,
)
from lavague.core.retrievers import OpsmSplitRetriever
from lavague.core.world_model import WorldModel
from lavague.core.utilities.version_checker import check_latest_version
from lavague.core.action_engine import ActionEngine
from lavague.core.agents import WebAgent

import os
import warnings


def telemetry_warning():
    telemetry_var = os.getenv("LAVAGUE_TELEMETRY")
    if telemetry_var != "NONE":
        warning_message = "\033[93mTelemetry is turned on. To turn off telemetry, set your LAVAGUE_TELEMETRY to 'NONE'\033[0m"
        warnings.warn(warning_message, UserWarning)


telemetry_warning()
try:
    check_latest_version()
except:
    pass
