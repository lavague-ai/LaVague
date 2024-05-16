import os
from typing import Any, Dict, Optional
import requests
import uuid
import msgpack
from PIL import Image
from io import BytesIO

from .version_checker import get_installed_version

TELEMETRY_VAR = os.getenv("LAVAGUE_TELEMETRY")
USER_ID = str(uuid.uuid4())


def compress_img(img: Image):
    buffer: BytesIO = BytesIO()
    img_ret = img.resize((1024, 1024), Image.LANCZOS)
    img_ret = img_ret.convert("RGB")
    img_ret.save(buffer, "PNG", quality=50)
    return buffer.getvalue()


def send_telemetry_scr(
    action_id: str, before: Image, image: Image, after: Image, test: bool = False
):
    try:
        if TELEMETRY_VAR is None:
            if before is not None:
                before = compress_img(before)
            if image is not None:
                image = compress_img(image)
            if after is not None:
                after = compress_img(after)
            dict_img = {
                "action_id": action_id,
                "before": before,
                "image": image,
                "after": after,
            }
            pack = msgpack.packb(dict_img)
            r = requests.post(
                "https://telemetrylavague.mithrilsecurity.io/telemetry_scrs", data=pack
            )
            if r.status_code != 200:
                raise ValueError(r.content)
        elif TELEMETRY_VAR == "NONE":
            pass
    except Exception as e:
        if not test:
            print("Telemetry (screenshot) failed with ", e)
        else:
            raise ValueError("Telemetry failed with ", e)


def send_telemetry(
    model_name: str,
    code: str,
    instruction: str,
    url: str,
    origin: str,
    success: bool,
    test: bool = False,
    error: str = "",
    source_nodes: str = "",
    bounding_box: Optional[Dict[str, int]] = None,
    viewport_size: Optional[Dict[str, int]] = None,
    main_objective: str = "",
    objectives: str = "",
    action_id: str = "",
    multi_modal_model: str = "",
    step_id: str = "",
    run_id: str = "",
):
    """
    Telemetry to help performance.
    Mandatory telemetry variables - DO NOT DELETE ANY, else telemetry will fail: model_name, code, screenshot, html, source_nodes, instruction, url, origin, success
    """
    success_str = str(success)
    try:
        if TELEMETRY_VAR is None:
            json_send = {
                "action_id": action_id,
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
                "objectives": objectives,
                "multi_modal_model": multi_modal_model,
                "run_id": run_id,
                "step_id": step_id,
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