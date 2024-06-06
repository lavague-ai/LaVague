from io import BytesIO
import logging
import os
import shutil
from typing import Any, List, Optional
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
from PIL import Image

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

        self.output = ""

        self.clean_screenshot_folder = clean_screenshot_folder

        self.logger: AgentLogger = AgentLogger()

        self.action_engine.set_logger_all(self.logger)
        self.world_model.set_logger(self.logger)
        self.st_memory.set_logger(self.logger)

        if self.clean_screenshot_folder:
            try:
                if os.path.isdir("screenshots"):
                    shutil.rmtree("screenshots")
                logging_print.info("Screenshot folder cleared")
            except:
                pass

        self.result = ActionResult(
            instruction=None,
            code=self.driver.code_for_init(),
            success=False,
            output=None,
        )

    def get(self, url):
        self.driver.get(url)
        self.result.code += self.driver.code_for_get(url) + "\n"

    def demo(
        self,
        objective: str = "",
        user_data=None,
        instructions: Optional[List[str]] = None,
    ):
        try:
            from lavague.gradio import GradioAgentDemo

            grad = GradioAgentDemo(objective, instructions, self, user_data)
            grad.launch()
        except ImportError:
            raise ImportError(
                "`lavague-gradio` package not found, "
                "please run `pip install lavague-contexts-gradio`"
            )

    def _run_demo(
        self,
        objective: str,
        user_data=None,
        display: bool = False,
        objective_obj: Any = None,
        url_input: Any = None,
        instructions_history: Any = None,
        history: Any = None,
    ):
        """Internal run method for the gradio demo. Do not use directly. Use run instead."""
        from lavague.gradio import image_queue

        driver: BaseDriver = self.driver
        logger = self.logger
        n_steps = self.n_steps
        self.action_engine.set_display_all(display)
        output = ""
        success = True

        st_memory = self.st_memory
        world_model = self.world_model

        if user_data:
            self.st_memory.set_user_data(user_data)

        obs = driver.get_obs()

        logger.new_run()
        for curr_step in range(n_steps):
            current_state, past = st_memory.get_state()

            world_model_output = world_model.get_instruction(
                objective, current_state, past, obs
            )
            logging_print.info(world_model_output)
            next_engine_name = extract_next_engine(world_model_output)
            instruction = extract_world_model_instruction(world_model_output)

            img = self.driver.get_screenshot_as_png()
            img = BytesIO(img)
            img = Image.open(img)
            image_queue.put(img)

            if instruction.find("[NONE]") == -1:
                history[-1] = (
                    history[-1][0],
                    f"⏳ Step {curr_step + 1}:\n{instruction}...",
                )

            yield objective_obj, url_input, instructions_history, history, output

            if next_engine_name == "COMPLETE" or next_engine_name == "SUCCESS":
                output = instruction
                logging_print.info("Objective reached. Stopping...")

                logger.add_log(obs)
                logger.end_step()
                break

            action_result = self.action_engine.dispatch_instruction(
                next_engine_name, instruction
            )

            success = action_result.success
            output = action_result.output

            st_memory.update_state(
                instruction,
                next_engine_name,
                action_result.success,
                action_result.output,
            )

            img = self.driver.get_screenshot_as_png()
            img = BytesIO(img)
            img = Image.open(img)
            image_queue.put(img)

            logger.add_log(obs)
            logger.end_step()

            obs = driver.get_obs()
            url_input = self.action_engine.driver.get_url()
            if success:
                history[-1] = (
                    history[-1][0],
                    f"✅ Step {curr_step + 1}:\n{instruction}",
                )
            else:
                history[-1] = (
                    history[-1][0],
                    f"❌ Step {curr_step + 1}:\n{instruction}",
                )
            history.append((None, None))
            history[-1] = (history[-1][0], "⏳ ...")
            yield objective_obj, url_input, instructions_history, history, output
        send_telemetry(logger.return_pandas())
        url_input = self.action_engine.driver.get_url()
        if output is not None:
            if len(output) > 0 and output.strip() != "[NONE]":
                history[-1] = (history[-1][0], output)
            elif len(output) == 0 or output.strip() == "[NONE]":
                if success:
                    history[-1] = (history[-1][0], "🌊 Objective reached")
                else:
                    history[-1] = (history[-1][0], "❌ Failed to reach objective")
            else:
                if success:
                    history[-1] = (history[-1][0], "🌊 Objective reached")
                else:
                    history[-1] = (history[-1][0], "❌ Failed to reach objective")

        yield objective_obj, url_input, instructions_history, history, output

    def run(
        self, objective: str, user_data=None, display: bool = False
    ) -> ActionResult:
        self.action_engine.set_display_all(display)
        action_result: ActionResult

        st_memory = self.st_memory
        world_model = self.world_model

        if user_data:
            self.st_memory.set_user_data(user_data)

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
