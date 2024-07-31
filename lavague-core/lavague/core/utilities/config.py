import os


def is_flag_true(flag_name: str) -> bool:
    return os.getenv(flag_name, "").lower() in ("true", "1", "y", "yes")
