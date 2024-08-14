from io import BytesIO
import logging
import os
import shutil
from typing import Any, Optional

from lavague.core.action_engine import ActionEngine
from lavague.core.world_model import WorldModel
from lavague.core.utilities.format_utils import (
    extract_before_next_engine,
    extract_next_engine,
    extract_world_model_instruction,
    replace_hyphens,
)
from lavague.core.logger import AgentLogger, LocalDBLogger
from lavague.core.memory import ShortTermMemory
from lavague.core.base_driver import BaseDriver
from lavague.core.base_engine import ActionResult
from lavague.core.utilities.telemetry import send_telemetry
from PIL import Image
from IPython.display import display, HTML, Code
from lavague.core.token_counter import TokenCounter
from lavague.core.utilities.config import is_flag_true

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
        token_counter: Optional[TokenCounter] = None,
        n_steps: int = 10,
        clean_screenshot_folder: bool = True,
        logger: AgentLogger = None,
    ):
        self.driver: BaseDriver = action_engine.driver
        self.action_engine: ActionEngine = action_engine
        self.world_model: WorldModel = world_model
        self.st_memory = ShortTermMemory()
        self.token_counter = token_counter
        self.interrupted = False

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
            total_estimated_tokens=0,
            total_estimated_cost=0.0,
        )

    def get(self, url):
        self.driver.get(url)
        self.driver.wait_for_idle()
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
                "please run `pip install lavague-gradio`"
            )

    def _finish_step(
        self,
        next_engine_name: str,
        history: any,
        success,
        curr_step: int,
        instruction: str,
        world_model_output: str,
    ):
        from gradio import ChatMessage

        if next_engine_name != "Navigation Engine":
            if success:
                history[-1] = ChatMessage(
                    role="assistant",
                    content=f"{world_model_output}",
                    metadata={"title": f"✅ Step {curr_step + 1} - {instruction}"},
                )
            else:
                history[-1] = ChatMessage(
                    role="assistant",
                    content=f"{world_model_output}",
                    metadata={"title": f"❌ Step {curr_step + 1} - {instruction}"},
                )
            history.append(
                ChatMessage(role="assistant", content="⏳ Thinking of next steps...")
            )
        else:
            history[-1] = ChatMessage(
                role="assistant", content=f"⏳ Thinking of next steps..."
            )
        return history

    def _add_step(
        self,
        instruction: str,
        next_engine_name: str,
        history: any,
        world_model_output: str,
        curr_step: int,
        curr_instruction: str,
    ):
        from gradio import ChatMessage

        if instruction.find("[NONE]") == -1 and next_engine_name != "COMPLETE":
            history[-1] = ChatMessage(
                role="assistant",
                content=f"{world_model_output}",
                metadata={"title": f"⏳ Step {curr_step + 1} - {curr_instruction}"},
            )
        return history

    def _check_result(self, history: any, output: str, success: bool, curr_step: int):
        from gradio import ChatMessage

        if output is not None:
            if len(output) > 0 and output.strip() != "[NONE]":
                history[-1] = ChatMessage(
                    role="assistant", content=output, metadata={"title": f"🌊 Output"}
                )
            elif len(output) == 0 or output.strip() == "[NONE]":
                if success:
                    history[-1] = ChatMessage(
                        role="assistant",
                        content=f"The objective was successfully executed after {curr_step} step(s).",
                        metadata={"title": f"🌊 Objective reached"},
                    )
                else:
                    history[-1] = ChatMessage(
                        role="assistant",
                        content=f"The objective was not successfully executed after {curr_step} step(s).",
                        metadata={"title": f"❌ Failed to reach objective"},
                    )
            else:
                if success:
                    history[-1] = ChatMessage(
                        role="assistant",
                        content=f"The objective was successfully executed after {curr_step} step(s).",
                        metadata={"title": f"🌊 Objective reached"},
                    )
                else:
                    history[-1] = ChatMessage(
                        role="assistant",
                        content=f"The objective was not successfully executed after {curr_step} step(s).",
                        metadata={"title": f"❌ Failed to reach objective"},
                    )

        return history

    def _run_demo(
        self,
        objective: str,
        user_data=None,
        display: bool = False,
        objective_obj: Any = None,
        url_input: Any = None,
        image_display: Any = None,
        history: Any = None,
        screenshot_ratio: float = 1,
    ):
        """Internal run method for the gradio demo. Do not use directly. Use run instead."""

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
        for curr_step in range(n_steps):
            current_state, past = st_memory.get_state()

            world_model_output = world_model.get_instruction(
                objective, current_state, past, obs
            )
            self.action_engine.world_model_output = replace_hyphens(
                extract_before_next_engine(world_model_output)
            )
            logging_print.info(world_model_output)
            next_engine_name = extract_next_engine(world_model_output)
            instruction = extract_world_model_instruction(world_model_output)

            self.action_engine.screenshot_ratio = screenshot_ratio
            image_display = self._get_screenshot(screenshot_ratio)

            self.action_engine.curr_step = curr_step + 1
            self.action_engine.curr_instruction = instruction

            history = self._add_step(
                instruction,
                next_engine_name,
                history,
                self.action_engine.world_model_output,
                curr_step,
                self.action_engine.curr_instruction,
            )
            yield (
                objective_obj,
                url_input,
                image_display,
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
            history = self._finish_step(
                next_engine_name,
                history,
                success,
                curr_step,
                instruction,
                self.action_engine.world_model_output,
            )
            url_input = self.action_engine.driver.get_url()
            image_display = self._get_screenshot(screenshot_ratio)
            yield (
                objective_obj,
                url_input,
                image_display,
                history,
                output,
            )
        send_telemetry(logger.return_pandas(), origin="gradio")
        url_input = self.action_engine.driver.get_url()
        history = self._check_result(history, output, success, curr_step)
        yield (
            objective_obj,
            url_input,
            image_display,
            history,
            output,
        )

    def _get_screenshot(self, screenshot_ratio):
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
        return img

    def _run_step_gradio(
        self,
        objective: str,
        curr_step: int,
        objective_obj: Any = None,
        url_input: Any = None,
        image_display: Any = None,
        history: Any = None,
        screenshot_ratio: float = 1,
    ):
        """Internal run method for the gradio demo. Do not use directly. Use run_step instead."""
        output = None
        self.action_engine.set_display_all(False)
        obs = self.driver.get_obs()
        current_state, past = self.st_memory.get_state()
        url_input = self.driver.get_url()

        world_model_output = self.world_model.get_instruction(
            objective, current_state, past, obs
        )
        self.action_engine.world_model_output = replace_hyphens(
            extract_before_next_engine(world_model_output)
        )
        logging_print.info(world_model_output)
        next_engine_name = extract_next_engine(world_model_output)
        instruction = extract_world_model_instruction(world_model_output)

        self.action_engine.screenshot_ratio = screenshot_ratio
        image_display = self._get_screenshot(screenshot_ratio)

        self.action_engine.curr_step = curr_step + 1
        self.action_engine.curr_instruction = instruction

        history = self._add_step(
            instruction,
            next_engine_name,
            history,
            self.action_engine.world_model_output,
            curr_step,
            instruction,
        )

        yield (
            objective_obj,
            url_input,
            image_display,
            history,
            output,
        )

        if next_engine_name == "COMPLETE" or next_engine_name == "SUCCESS":
            output = self.result.output
            self.result.success = True
            self.result.output = instruction
            logging_print.info("Objective reached. Stopping...")
            url_input = self.action_engine.driver.get_url()
            self.logger.add_log(obs)

            yield (
                objective_obj,
                url_input,
                image_display,
                history,
                output,
            )

            self.process_token_usage()
            self.logger.end_step()
            return

        yield from self.action_engine.dispatch_instruction_gradio(
            next_engine_name, instruction
        )

        success = self.action_engine.ret.success

        output = self.result.output

        if self.action_engine.ret.success:
            self.result.code += self.action_engine.ret.code
            self.result.output = self.action_engine.ret.output
        self.st_memory.update_state(
            instruction,
            next_engine_name,
            self.action_engine.ret.success,
            self.action_engine.ret.output,
        )
        self.logger.add_log(obs)

        history = self._finish_step(
            next_engine_name,
            history,
            success,
            curr_step,
            instruction,
            self.action_engine.world_model_output,
        )
        url_input = self.driver.get_url()
        image_display = self._get_screenshot(screenshot_ratio)

        yield (
            objective_obj,
            url_input,
            image_display,
            history,
            output,
        )

        self.process_token_usage()
        self.logger.end_step()

    def run_step(self, objective: str) -> Optional[ActionResult]:
        obs = self.driver.get_obs()
        current_state, past = self.st_memory.get_state()

        world_model_output = self.world_model.get_instruction(
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

            self.process_token_usage()
            self.logger.end_step()
            return self.result

        action_result = self.action_engine.dispatch_instruction(
            next_engine_name, instruction
        )
        if action_result.success:
            self.result.code += action_result.code
            self.result.output = action_result.output
        self.st_memory.update_state(
            instruction,
            next_engine_name,
            action_result.success,
            action_result.output,
        )
        self.logger.add_log(obs)

        self.process_token_usage()
        self.logger.end_step()

    def prepare_run(self, display: bool = False, user_data=None):
        self.action_engine.set_display_all(display)
        if user_data:
            self.st_memory.set_user_data(user_data)
        self.logger.new_run()

    def run(
        self,
        objective: str,
        user_data=None,
        display: bool = False,
        log_to_db: bool = is_flag_true("LAVAGUE_LOG_TO_DB"),
        step_by_step=False,
    ) -> ActionResult:
        self.interrupted = False
        self.prepare_run(display=display, user_data=user_data)

        try:
            for _ in range(self.n_steps):
                result = self.run_step(objective)

                if result is not None:
                    break

                if step_by_step:
                    input("Press ENTER to continue")

        except KeyboardInterrupt:
            logging_print.warning("The agent was interrupted.")
            self.interrupted = True
            pass
        except Exception as e:
            logging_print.error(f"Error while running the agent: {e}")
            self.interrupted = True
            raise e
        finally:
            self.driver.destroy()
            origin = self.origin if hasattr(self, "origin") else "lavague"
            send_telemetry(self.logger.return_pandas(), origin=origin)
            if log_to_db:
                local_db_logger = LocalDBLogger()
                local_db_logger.insert_logs(self)
        return self.result

    def process_token_usage(self):
        if self.token_counter is not None:
            token_counts, token_costs = self.token_counter.process_token_usage(
                self.world_model, self.action_engine, result_to_update=self.result
            )
            self.logger.add_log(token_counts)
            self.logger.add_log(token_costs)

    def display_previous_nodes(self, steps: int) -> None:
        """prints out all nodes per each sub-instruction for given steps"""
        dflogs = self.logger.return_pandas()
        # check if dflogs are not null and not empty and engine_log is present in dflogs columns
        if (
            dflogs is not None
            and dflogs.empty is False
            and "engine_log" in dflogs.columns
        ):
            if steps > len(dflogs):
                print(
                    f"Previous steps: {len(dflogs)}\nrequested steps: {steps}\nshowing available steps"
                )
            steps = len(dflogs) if steps > len(dflogs) else steps
            for step in range(steps):
                print(f"Step: {step}")
                sub_ins = 0
                if isinstance(dflogs.at[step, "engine_log"], list):
                    for subinst in dflogs.at[step, "engine_log"]:
                        print(f"Sub-Instruction: {sub_ins}")
                        sub_ins += 1
                        x = 0
                        for node in subinst["retrieved_html"]:
                            print(f"Node {x}")
                            x = x + 1
                            display(HTML(node))  # Display node as visual element
                            display(Code(node, language="html"))  # Display code
        else:
            print(
                f"No previous nodes available. Please run the agent atleast once to view previous steps"
            )

    def display_all_nodes(self) -> None:
        """prints out all nodes per each sub-instruction"""
        dflogs = self.logger.return_pandas()
        # check if dflogs are not null and not empty and engine_log is present in dflogs columns
        if (
            dflogs is not None
            and dflogs.empty is False
            and "engine_log" in dflogs.columns
        ):
            print(f"Number of steps: {len(dflogs)}")
            steps = len(dflogs)
            for step in range(steps):
                print(f"Step: {step}")
                sub_ins = 0
                if isinstance(dflogs.at[step, "engine_log"], list):
                    for subinst in dflogs.at[step, "engine_log"]:
                        print(f"Sub-Instruction: {sub_ins}")
                        sub_ins += 1
                        x = 0
                        for node in subinst["retrieved_html"]:
                            print(f"Node: {x}")
                            x = x + 1
                            display(HTML(node))  # Display node as visual element
                            display(Code(node, language="html"))  # Display code
        else:
            print(
                f"No previous nodes available. Please run the agent atleast once to view previous steps"
            )

    def set_origin(self, origin: str):
        self.origin = origin
