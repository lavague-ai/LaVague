import logging
import os
from typing import Any, Dict
from pandas import DataFrame
import uuid
import msgpack
import numpy as np
import requests

from .version_checker import get_installed_version

TELEMETRY_VAR = os.getenv("LAVAGUE_TELEMETRY")
UNIQUE_ID = os.getenv("LAVAGUE_UNIQUE_USER_ID")
USER_ID = str(uuid.uuid4())

if UNIQUE_ID is not None:
    UNIQUE_ID = UNIQUE_ID[:256]

logging_print = logging.getLogger(__name__)
logging_print.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(format)
logging_print.addHandler(ch)
logging_print.propagate = False


def send_telemetry(logger_telemetry: DataFrame, test: bool = False):
    try:
        if TELEMETRY_VAR is None:
            logger_telemetry = logger_telemetry.drop("screenshots", axis=1)
            logger_telemetry = logger_telemetry.drop("screenshots_path", axis=1)
            logger_telemetry = logger_telemetry.drop("html", axis=1)
            logger_telemetry = logger_telemetry.replace({np.nan: None})

            for index, row in logger_telemetry.iterrows():
                logger_telemetry.at[index, "unique_user_id"] = UNIQUE_ID
                logger_telemetry.at[index, "user_id"] = USER_ID
                logger_telemetry.at[index, "version"] = get_installed_version(
                    "lavague-core"
                )

                if "engine_log" in row:
                    t = row["engine_log"]
                    if t is not None:
                        if isinstance(t, list):
                            for t_obj in t:
                                if "vision_data" in t_obj:
                                    vision = t_obj["vision_data"]
                                    for i in range(len(vision)):
                                        if "screenshot" in vision[i]:
                                            del vision[i]["screenshot"]
                            logger_telemetry.at[index, "engine_log"] = t
                        else:
                            if "vision_data" in t:
                                vision = t["vision_data"]
                                for i in range(len(vision)):
                                    if "screenshot" in vision[i]:
                                        del vision[i]["screenshot"]
                                logger_telemetry.at[index, "engine_log"] = t

            dic = logger_telemetry.to_dict("records")
            pack = msgpack.packb(dic)

            r = requests.post(
                "https://telemetrylavague.mithrilsecurity.io/telemetry_new", data=pack
            )
            if r.status_code != 200:
                raise ValueError(r.content)
            else:
                logging_print.debug("Telemetry sent successfully")
        elif TELEMETRY_VAR == "NONE":
            pass
    except Exception as e:
        if not test:
            logging_print.warning(f"Telemetry failed with {e}")
        else:
            raise ValueError("Telemetry failed with ", e)
