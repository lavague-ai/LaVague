import uuid
import pandas as pd
import os
from PIL import Image
import json


def load_images_from_folder(folder_path):
    images = []
    for filename in os.listdir(folder_path):
        if (
            filename.endswith(".png")
            or filename.endswith(".jpg")
            or filename.endswith(".jpeg")
        ):
            img_path = os.path.join(folder_path, filename)
            img = Image.open(img_path)
            images.append(img)
    return images


class AgentLogger:
    def __init__(self):
        self.logs = []

    def clear_logs(self):
        self.run_id = str(uuid.uuid4())
        self.logs = []
        self.current_row = {}
        self.current_step = 0

    def new_run(self):
        self.run_id = str(uuid.uuid4())
        self.current_row = {}
        self.current_step = 0

    def end_step(self):
        row = self.current_row
        row["run_id"] = self.run_id
        row["step"] = self.current_step
        self.logs.append(row)
        self.current_row = {}
        self.current_step += 1

    def add_log(self, log: dict):
        for k, v in log.items():
            self.current_row[k] = v

    def return_pandas(self) -> pd.DataFrame:
        df = pd.DataFrame(self.logs)
        # checks if "screenshots_path" in dataframe columns
        if "screenshots_path" in df.columns:
            df["screenshots"] = df["screenshots_path"].apply(load_images_from_folder)
        return df


class LocalLogger(AgentLogger):
    def __init__(self, log_file_path: str, ignore_keys: list[str] = None):
        self.log_file_path = log_file_path
        self.ignore_keys = ignore_keys
        if self.ignore_keys is None:
            self.ignore_keys = ["screenshots", "html"]
        super().__init__()
        with open(self.log_file_path, "w") as f:
            f.write("")

    def clear_logs(self):
        super().clear_logs()
        # Clear the log file
        with open(self.log_file_path, "w") as f:
            f.write("")

    def add_log(self, log: dict):
        super().add_log(log)
        # Write the log to the file
        with open(self.log_file_path, "a") as f:
            f.write(self.serialize_dict(log))
            f.write("\n")  # Ensure each log entry is on a new line

    # Custom function to serialize non-serializable objects
    def custom_serializer(self, obj):
        if isinstance(obj, dict):
            return {
                k: self.custom_serializer(v)
                for k, v in obj.items()
                if k not in self.ignore_keys
            }
        elif isinstance(obj, list):
            return [self.custom_serializer(v) for v in obj]
        try:
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            return None

    # Function to serialize dictionary with ignoring non-serializable properties
    def serialize_dict(self, input_dict):
        return json.dumps(self.custom_serializer(input_dict))


class Loggable:
    logger: AgentLogger

    def set_logger(self, logger: AgentLogger):
        self.logger = logger
