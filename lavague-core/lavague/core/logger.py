import uuid
import pandas as pd
import os
from PIL import Image


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
        df["screenshots"] = df["screenshots_path"].apply(load_images_from_folder)
        return df


class Loggable:
    logger: AgentLogger

    def set_logger(self, logger: AgentLogger):
        self.logger = logger
