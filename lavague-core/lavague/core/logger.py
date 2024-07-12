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
        self.ensure_connection()

    def ensure_connection(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                print("Connected to SQLite")
        except sqlite3.Error as error:
            print("Error occurred while connecting to SQLite -", error)

    def create_or_alter_table(self, df_logs: DataFrame):
        columns = df_logs.columns
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                # check if the table exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='Logs'"
                )
                table_exists = cursor.fetchone() is not None

                if not table_exists:
                    # create the table with all columns as TEXT
                    create_query = f"CREATE TABLE Logs ({', '.join([f'{col} TEXT' for col in columns])})"
                    cursor.execute(create_query)
                else:
                    # get existing columns
                    cursor.execute("PRAGMA table_info(Logs)")
                    existing_columns = set(row[1] for row in cursor.fetchall())

                    # add new columns
                    for col in columns:
                        if col not in existing_columns:
                            alter_query = f"ALTER TABLE Logs ADD COLUMN {col} TEXT"
                            cursor.execute(alter_query)

                conn.commit()
                print("Table created or altered successfully")
        except sqlite3.Error as error:
            print("Error occurred while creating or altering table -", error)

    def insert_logs(self, agent) -> None:
        if agent:
            df_logs = agent.logger.return_pandas()
            try:
                self.create_or_alter_table(df_logs)

                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()

                    columns = ", ".join(df_logs.columns)
                    placeholders = ", ".join(["?" for _ in df_logs.columns])
                    insert_query = (
                        f"INSERT INTO Logs ({columns}) VALUES ({placeholders})"
                    )

                    data_to_insert = self.format_df_logs_to_sqlite3_types(df_logs)
                    cursor.executemany(insert_query, data_to_insert)

                    conn.commit()
                    print("Log insert complete")
            except sqlite3.Error as error:
                print("Error occurred while inserting logs -", error)

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
