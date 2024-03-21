import os
import requests
import uuid

TELEMETRY_VAR = os.getenv("LAVAGUE_TELEMETRY")
USER_ID = str(uuid.uuid4())

def send_telemetry(model_name, code, screenshot, html, source_nodes, instruction, url, origin):
    try:
        if TELEMETRY_VAR == "HIGH":
            r = requests.post('https://telemetrylavague.mithrilsecurity.io/send_data', json={"code_produced": code, "llm": model_name, "screenshot": screenshot.decode("utf-8"), "url": url, "html_code": html, "query": instruction, "nodes": source_nodes, "user_id": USER_ID, "origin": origin})
        elif TELEMETRY_VAR is None:
            r = requests.post('https://telemetrylavague.mithrilsecurity.io/telemetry', json={"llm": model_name, "user_id": USER_ID, "origin": origin})
    except:
        pass