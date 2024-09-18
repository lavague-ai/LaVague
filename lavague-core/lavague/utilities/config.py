import os
from typing import Optional

LAVAGUE_API_BASE_URL = "https://cloud.lavague.ai/api"


def is_flag_true(flag_name: str, default=False) -> bool:
    value = os.getenv(flag_name, "")
    if value == "":
        return default
    return value in ("true", "1", "y", "yes")


def get_config(var_name: str, default: Optional[str] = None) -> str:
    value = os.getenv(var_name, default)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is required")
    return value
