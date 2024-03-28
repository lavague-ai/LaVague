import os
import requests
import uuid

TELEMETRY_VAR = os.getenv("LAVAGUE_TELEMETRY")
USER_ID = str(uuid.uuid4())


def send_telemetry(
    model_name, code, screenshot, html, source_nodes, instruction, url, origin, success
):
    try:
        if TELEMETRY_VAR is None:
            r = requests.post(
                "https://telemetrylavague.mithrilsecurity.io/telemetry",
                json={"llm": model_name, "user_id": USER_ID, "origin": origin},
            )
    except Exception as e:
        pass
