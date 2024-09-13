import os
from typing import Optional

LAVAGUE_API_BASE_URL = "https://api.lavague.ai"


def is_flag_true(flag_name: str) -> bool:
    return os.getenv(flag_name, "").lower() in ("true", "1", "y", "yes")


def get_config(var_name: str, default: Optional[str] = None, required=True) -> str:
    value = os.getenv(var_name, default)
    if required and value is None:
        raise ValueError(f"Environment variable {var_name} is required")
    return value
