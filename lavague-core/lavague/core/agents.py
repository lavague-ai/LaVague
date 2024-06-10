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
        logger: AgentLogger = None,
    ):
        self.driver: BaseDriver = action_engine.driver
        self.action_engine: ActionEngine = action_engine
        self.world_model: WorldModel = world_model
        self.st_memory = ShortTermMemory()

        self.n_steps = n_steps

        self.output = ""

        self.clean_screenshot_folder = clean_screenshot_folder

        if logger is None:
            self.logger: AgentLogger = AgentLogger()
        else:
            self.logger = logger

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
        screenshot_ratio: float = 1,
    ):
        try:
            from lavague.gradio import GradioAgentDemo

            grad = GradioAgentDemo(objective, None, self, user_data, screenshot_ratio)
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
        image_display: Any = None,
        instructions_history: Any = None,
        history: Any = None,
        screenshot_ratio: float = 1,
    ):
        """Internal run method for the gradio demo. Do not use directly. Use run instead."""

        from selenium.webdriver.support.ui import WebDriverWait

        driver: BaseDriver = self.driver
        logger = self.logger
        n_steps = self.n_steps
        self.action_engine.set_display_all(display)
        output = None
        success = True

        try:
            if os.path.isdir("screenshots"):
                shutil.rmtree("screenshots")
            logging_print.info("Screenshot folder cleared")
        except:
            pass

        self.st_memory = ShortTermMemory()
        st_memory = self.st_memory
        world_model = self.world_model

        if user_data:
            st_memory.set_user_data(user_data)

        obs = driver.get_obs()

        logger.clear_logs()

        WebDriverWait(self.driver.get_driver(), 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        for curr_step in range(n_steps):
            current_state, past = st_memory.get_state()

            world_model_output = world_model.get_instruction(
                objective, current_state, past, obs
            )
            logging_print.info(world_model_output)
            next_engine_name = extract_next_engine(world_model_output)
            instruction = extract_world_model_instruction(world_model_output)

            self.action_engine.screenshot_ratio = screenshot_ratio
            img = self.driver.get_screenshot_as_png()
            img = BytesIO(img)
            img = Image.open(img)
            if screenshot_ratio != 1:
                img = img.resize(
                    (
                        int(img.width / screenshot_ratio),
                        int(img.height / screenshot_ratio),
                    )
                )
            image_display = img

            self.action_engine.curr_step = curr_step + 1
            self.action_engine.curr_instruction = instruction

            if instruction.find("[NONE]") == -1 and next_engine_name != "COMPLETE":
                history[-1] = (
                    history[-1][0],
                    f"⏳ Step {curr_step + 1}:\n{instruction}",
                )

            yield (
                objective_obj,
                url_input,
                image_display,
                instructions_history,
                history,
                output,
            )

            if next_engine_name == "COMPLETE" or next_engine_name == "SUCCESS":
                output = instruction
                logging_print.info("Objective reached. Stopping...")

                logger.add_log(obs)
                logger.end_step()
                break

            yield from self.action_engine.dispatch_instruction_gradio(
                next_engine_name, instruction
            )

            success = self.action_engine.ret.success
            output = self.action_engine.ret.output

            st_memory.update_state(
                instruction,
                next_engine_name,
                success,
                output,
            )

            logger.add_log(obs)
            logger.end_step()

            obs = driver.get_obs()
            if next_engine_name != "Navigation Engine":
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
            url_input = self.action_engine.driver.get_url()
            history[-1] = (history[-1][0], "⏳ Thinking of next steps...")
            img = self.driver.get_screenshot_as_png()
            img = BytesIO(img)
            img = Image.open(img)
            if screenshot_ratio != 1:
                img = img.resize(
                    (
                        int(img.width / screenshot_ratio),
                        int(img.height / screenshot_ratio),
                    )
                )
            image_display = img
            yield (
                objective_obj,
                url_input,
                image_display,
                instructions_history,
                history,
                output,
            )
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

        yield (
            objective_obj,
            url_input,
            image_display,
            instructions_history,
            history,
            output,
        )

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
                self.result.output = instruction
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
