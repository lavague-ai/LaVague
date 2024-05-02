import os
import requests
import uuid

from .version_checker import get_installed_version

TELEMETRY_VAR = os.getenv("LAVAGUE_TELEMETRY")
USER_ID = str(uuid.uuid4())


def send_telemetry(
    model_name: str,
    code: str,
    screenshot: bytes,
    html: str,
    instruction: str,
    url: str,
    origin: str,
    success: bool,
    test: bool = False,
    error: str = "",
    source_nodes: str = "",
):
    """
    Telemetry to help performance.
    Mandatory telemetry variables - DO NOT DELETE ANY, else telemetry will fail: model_name, code, screenshot, html, source_nodes, instruction, url, origin, success
    """
    success_str = str(success)
    try:
        if TELEMETRY_VAR == "HIGH":
            r = requests.post(
                "https://telemetrylavague.mithrilsecurity.io/send_data",
                json={
                    "version": get_installed_version("lavague"),
                    "code_produced": code,
                    "llm": model_name,
                    "screenshot": screenshot.decode("utf-8"),
                    "url": url,
                    "html_code": html,
                    "query": instruction,
                    "user_id": USER_ID,
                    "origin": origin,
                    "success": success_str,
                    "source_nodes": source_nodes,
                    "error_msg": error,
                    "test": test,
                },
            )
            if r.status_code != 200:
                raise ValueError(r.content)
        elif TELEMETRY_VAR is None or TELEMETRY_VAR == "LOW":
            r = requests.post(
                "https://telemetrylavague.mithrilsecurity.io/telemetry",
                json={
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
                },
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
