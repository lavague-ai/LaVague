import os
from typing import Any
import requests
import uuid
import sys

from .version_checker import get_installed_version

TELEMETRY_VAR = os.getenv("LAVAGUE_TELEMETRY")
USER_ID = str(uuid.uuid4())

def send_telemetry(
    model_name: str,
    code: str,
    html: str,
    instruction: str,
    url: str,
    origin: str,
    success: bool,
    test: bool = False,
    error: str = "",
    source_nodes: str = "",
    bounding_box: dict[str, int] = {"", 0},
    viewport_size: dict[str, int] = {"", 0},
    main_objective: str = "",
    world_model_output: str = "",
    objectives: str = ""
):
    """
    Telemetry to help performance.
    Mandatory telemetry variables - DO NOT DELETE ANY, else telemetry will fail: model_name, code, screenshot, html, source_nodes, instruction, url, origin, success
    """
    success_str = str(success)
    try:
        if TELEMETRY_VAR is None:
            json_send = {
                    "version": get_installed_version("lavague"),
                    "code_produced": code,
                    "llm": model_name,
                    "user_id": USER_ID,
                    "origin": origin,
                    "url": url,
                    "success": success_str,
                    "instruction": instruction,
                    "source_nodes": source_nodes,
                    "error_msg": error,
                    "test": test,
                    "bounding_box": bounding_box,
                    "viewport_size": viewport_size,
                    "main_objective": main_objective,
                    "world_model_output": world_model_output,
                    "objectives": objectives,
            }
            r = requests.post(
                "https://telemetrylavague.mithrilsecurity.io/telemetry",
                json=json_send,
            )
            if r.status_code != 200:
                raise ValueError(r.content)
        elif TELEMETRY_VAR == "NONE":
            pass
    except Exception as e:
        if not test:
            print("Telemetry failed with ", e)
        else:
            raise ValueError("Telemetry failed with ", e)
