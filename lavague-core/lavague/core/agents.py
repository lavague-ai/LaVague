from typing import Dict
from lavague.core.base_driver import BaseDriver
from lavague.core.utilities.telemetry import send_telemetry
from lavague.core.action_engine import ActionEngine
from lavague.core.python_engine import PythonEngine
from lavague.core.world_model import WorldModel
from lavague.core.navigation import NavigationControl
from lavague.core.utilities.format_utils import (
    extract_next_engine,
    extract_world_model_instruction,
)
from lavague.core.logger import AgentLogger
from lavague.core.memory import ShortTermMemory
from lavague.core.action_engine import BaseActionEngine
from lavague.core.utilities.format_utils import extract_code_block

class WebAgent:
    """
    Web agent class, for now only works with selenium.
    """

    def __init__(
        self,
        world_model: WorldModel,
        action_engine: ActionEngine,
        python_engine: PythonEngine,
        n_steps: int = 10,
    ):
        self.driver: BaseDriver = action_engine.driver
        self.action_engine: ActionEngine = action_engine
        self.world_model: WorldModel = world_model
        self.navigation_control: NavigationControl = NavigationControl(self.driver)
        self.st_memory = ShortTermMemory()
        self.python_engine: PythonEngine = python_engine

        self.n_steps = n_steps
        
        self.logger: AgentLogger = AgentLogger()
        
        self.action_engine.set_logger(self.logger)
        self.python_engine.set_logger(self.logger)
        self.navigation_control.set_logger(self.logger)
        self.world_model.set_logger(self.logger)
        self.st_memory.set_logger(self.logger)
        
    def get(self, url):
        self.driver.goto(url)

    def run(self, objective: str, user_data=None, display: bool = False):
        driver: BaseDriver = self.driver
        logger = self.logger
        n_steps = self.n_steps
        
        st_memory = self.st_memory
        world_model = self.world_model
        navigation_control = self.navigation_control
        python_engine = self.python_engine
        action_engine = self.action_engine
        
        engines: Dict[str, BaseActionEngine] = {
            "Navigation Engine": action_engine,
            "Python Engine": python_engine,
            "Navigation Controls": navigation_control,
        }
        
        obs = driver.get_obs()

        logger.new_run()
        for _ in range(n_steps):
            current_state, past = st_memory.get_state()
            
            world_model_output = world_model.get_instruction(objective, current_state, past, obs)
            print(world_model_output)
            next_engine_name = extract_next_engine(world_model_output)
            instruction = extract_world_model_instruction(world_model_output)

            if next_engine_name == "STOP":
                output = extract_code_block(instruction)
                print("Objective reached. Stopping...")
                logger.add_log(obs)
                logger.end_step()
                break
            
            next_engine = engines[next_engine_name]
            success, output = next_engine.execute_instruction(instruction)
            
            st_memory.update_state(instruction, next_engine_name, 
                                    success, output)    
            
            logger.add_log(obs)
            logger.end_step()
            
            obs = driver.get_obs()
        
        send_telemetry(logger.return_pandas())
        return output