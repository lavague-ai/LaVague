import uuid
import pandas as pd

class AgentLogger:
    def __init__(self):
        self.logs = []
        
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
        return pd.DataFrame(self.logs)