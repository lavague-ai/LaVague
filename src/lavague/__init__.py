import os
import warnings

def telemetry_warning():
    telemetry_var = os.getenv("TELEMETRY_VAR") 
    if telemetry_var != "NONE":
        warning_message = (
            "\033[93mTelemetry is turned on. To turn off telemetry, set your TELEMETRY_VAR to 'NONE'\033[0m"
        )
        warnings.warn(warning_message, UserWarning)

def exec_warning():
    warning_message = (
        "\033[93mSecurity warning: This package executes LLM-generated code.\033[0m"
    )
    warnings.warn(warning_message, UserWarning)

telemetry_warning()
exec_warning()
