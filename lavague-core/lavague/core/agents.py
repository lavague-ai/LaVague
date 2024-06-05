import logging
import os
import shutil
from lavague.core.action_engine import ActionEngine
from lavague.core.world_model import WorldModel
from lavague.core.utilities.format_utils import (
    extract_next_engine,
    extract_world_model_instruction,
)
from lavague.core.logger import AgentLogger
from lavague.core.memory import ShortTermMemory
from lavague.core.base_driver import BaseDriver
from lavague.core.base_engine import ActionResult
from lavague.core.utilities.telemetry import send_telemetry

logging_print = logging.getLogger(__name__)
logging_print.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(format)
logging_print.addHandler(ch)
logging_print.propagate = False


class WebAgent:
    """
    Web agent class, for now only works with selenium.
    """

    def __init__(
        self,
        world_model: WorldModel,
        action_engine: ActionEngine,
        n_steps: int = 10,
        clean_screenshot_folder: bool = True,
    ):
        self.driver: BaseDriver = action_engine.driver
        self.action_engine: ActionEngine = action_engine
        self.world_model: WorldModel = world_model
        self.st_memory = ShortTermMemory()

        self.n_steps = n_steps

        self.clean_screenshot_folder = clean_screenshot_folder

        self.logger: AgentLogger = AgentLogger()

        self.action_engine.set_logger_all(self.logger)
        self.world_model.set_logger(self.logger)
        self.st_memory.set_logger(self.logger)

        self.result = ActionResult(
            instruction=None,
            code=self.driver.code_for_init(),
            success=False,
            output=None,
        )

    def get(self, url):
        self.driver.get(url)
        self.result.code += self.driver.code_for_get(url) + "\n"

    def run(
        self, objective: str, user_data=None, display: bool = False
    ) -> ActionResult:
        self.action_engine.set_display(display)
        action_result: ActionResult

        st_memory = self.st_memory
        world_model = self.world_model

        if user_data:
            self.st_memory.set_user_data(user_data)

        if self.clean_screenshot_folder:
            try:
                if os.path.isdir("screenshots"):
                    shutil.rmtree("screenshots")
                logging_print.info("Screenshot folder cleared")
            except:
                pass

        obs = self.driver.get_obs()

        self.logger.new_run()
        for _ in range(self.n_steps):
            current_state, past = st_memory.get_state()

            world_model_output = world_model.get_instruction(
                objective, current_state, past, obs
            )
            logging_print.info(world_model_output)
            next_engine_name = extract_next_engine(world_model_output)
            instruction = extract_world_model_instruction(world_model_output)

            if next_engine_name == "COMPLETE" or next_engine_name == "SUCCESS":
                self.result.success = True
                logging_print.info("Objective reached. Stopping...")
                self.logger.add_log(obs)
                self.logger.end_step()
                break

            action_result = self.action_engine.dispatch_instruction(
                next_engine_name, instruction
            )
            if action_result.success:
                self.result.code += action_result.code
                self.result.output = action_result.output
            st_memory.update_state(
                instruction,
                next_engine_name,
                action_result.success,
                action_result.output,
            )

            self.logger.add_log(obs)
            self.logger.end_step()

            obs = self.driver.get_obs()
        send_telemetry(self.logger.return_pandas())
        return self.result
