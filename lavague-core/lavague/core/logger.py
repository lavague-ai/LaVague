import uuid
import pandas as pd
import os
from PIL import Image
import json
import sqlite3
import io
from pandas.core.frame import DataFrame


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


class LocalDBLogger(AgentLogger):
    def __init__(self, db_name: str = "lavague_logs.db"):
        self.db_name = db_name
        # on init connect to db and create table and close connection
        try:
            sqliteConnection = sqlite3.connect(db_name)
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")
            create_table = """
                CREATE TABLE IF NOT EXISTS Logs
                    (current_state TEXT,
                    past TEXT,
                    world_model_prompt TEXT,
                    world_model_output TEXT,
                    world_model_inference_time REAL,
                    engine TEXT,
                    instruction TEXT,
                    engine_log TEXT,
                    success TEXT,
                    output TEXT,
                    code TEXT,
                    html TEXT,
                    screenshots_path TEXT,
                    url TEXT,
                    date TEXT,
                    run_id TEXT,
                    step INTEGER,
                    screenshots TEXT)"""
            cursor.execute(create_table)
            cursor.close()
            print("Created table : Logs")
        except sqlite3.Error as error:
            print("Error occurred - ", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("sqlite connection is closed")

    def insert_logs(self, agent) -> None:
        if agent:
            df_logs = agent.logger.return_pandas()
            try:
                sqliteConnection = sqlite3.connect(self.db_name)
                cursor = sqliteConnection.cursor()
                print("Connected to SQLite")

                dataToInsert = self.format_df_logs_to_sqlite3_types(df_logs)

                cursor.executemany(
                    "INSERT INTO Logs VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    dataToInsert,
                )
                sqliteConnection.commit()
                cursor.close()
                print("Log insert complete")
            except sqlite3.Error as error:
                print("Error occurred - ", error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                    print("sqlite connection is closed")
        else:
            print("Please pass an appropriate agent!")

    def format_df_logs_to_sqlite3_types(self, df_logs: DataFrame) -> list:
        if df_logs is not None and isinstance(df_logs, DataFrame):
            data = []
            for index, r in df_logs.iterrows():
                t = []
                for col in df_logs:
                    i = r[col]
                    if col == "screenshots":
                        t.append(str(self.convertImgToBlob(i)))
                    elif type(i) == str or type(i) == float or type(i) == int:
                        t.append(i)
                    else:
                        t.append(str(i))
                data.append(t)
            return data
        else:
            print("Please pass a dataframe!")

    def convertImgToBlob(self, imageList: list) -> list:
        blobList = []
        image_bytes = io.BytesIO()
        for img in imageList:
            img.save(image_bytes, format="PNG")
            blobList.append(image_bytes)
        return blobList


class Loggable:
    logger: AgentLogger

    def set_logger(self, logger: AgentLogger):
        self.logger = logger
