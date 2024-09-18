from lavague.utilities.version_checker import check_latest_version

from lavague.agent import WebAgent
from lavague.trajectory import Trajectory

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
