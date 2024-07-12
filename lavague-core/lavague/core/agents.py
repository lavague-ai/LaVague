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
from lavague.core.logger import AgentLogger, LocalDBLogger
from lavague.core.memory import ShortTermMemory
from lavague.core.base_driver import BaseDriver
from lavague.core.base_engine import ActionResult
from lavague.core.utilities.telemetry import send_telemetry
from PIL import Image
from IPython.display import display, HTML, Code
from threading import Thread
from lavague.core.utilities.unicode_animation import (
    lavague_unicode_animation,
    clear_animation,
)
from lavague.core.utilities.pricing_util import get_pricing_data

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
        token_counter: Optional[dict] = None,
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
            total_estimated_cost=0,
        )

        self.mm_llm_token_counter = (
            token_counter.get("llm_token_counter", None) if token_counter else None
        )
        self.embedding_token_counter = (
            token_counter.get("embedding_token_counter", None)
            if token_counter
            else None
        )
        self.pricing_data = get_pricing_data()

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
        self,
        objective: str,
        user_data=None,
        display: bool = False,
        log_to_db: bool = False,
    ) -> ActionResult:
        self.action_engine.set_display_all(display)
        action_result: ActionResult

        if os.getenv("DISABLE_LAVAGUE_ANIMATION") is None:
            Thread(target=lavague_unicode_animation, daemon=True).start()

        try:
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
                clear_animation()
                logging_print.info(world_model_output)
                next_engine_name = extract_next_engine(world_model_output)
                instruction = extract_world_model_instruction(world_model_output)

                if next_engine_name == "COMPLETE" or next_engine_name == "SUCCESS":
                    self.result.success = True
                    self.result.output = instruction
                    clear_animation()
                    logging_print.info("Objective reached. Stopping...")
                    self.logger.add_log(obs)
                    self.add_token_count_log()
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
                self.add_token_count_log()
                self.logger.end_step()

                obs = self.driver.get_obs()
        except KeyboardInterrupt:
            clear_animation()
            logging_print.warning("The agent was interrupted.")
            pass
        except Exception as e:
            clear_animation()
            logging_print.error(f"Error while running the agent: {e}")
            raise e
        finally:
            send_telemetry(self.logger.return_pandas())
            if log_to_db:
                local_db_logger = LocalDBLogger()
                local_db_logger.insert_logs(self)
            clear_animation()
        return self.result

    def add_token_count_log(self) -> None:
        if (
            self.embedding_token_counter is not None
            and self.mm_llm_token_counter is not None
        ):
            embedding_token_count_info_per_step = {
                "embedding_tokens": self.embedding_token_counter.total_embedding_token_count
            }
            llm_token_count_info_per_step = {
                "llm_prompt_tokens": self.mm_llm_token_counter.prompt_llm_token_count,
                "llm_completion_tokens": self.mm_llm_token_counter.completion_llm_token_count,
                "total_llm_tokens": self.mm_llm_token_counter.total_llm_token_count,
            }
            self.logger.add_log(embedding_token_count_info_per_step)
            self.logger.add_log(llm_token_count_info_per_step)
            self.calculate_pricing()
            self.embedding_token_counter.reset_counts()
            self.mm_llm_token_counter.reset_counts()
        else:
            embedding_token_count_info_per_step = {"embedding_tokens": 0}
            llm_token_count_info_per_step = {
                "llm_prompt_tokens": 0,
                "llm_completion_tokens": 0,
                "total_llm_tokens": 0,
            }
            cost_dict = {
                "embedding_tokens_cost": 0,
                "llm_prompt_tokens_cost": 0,
                "llm_completion_tokens": 0,
                "total_cost_per_step": 0,
            }
            self.logger.add_log(cost_dict)
            self.logger.add_log(embedding_token_count_info_per_step)
            self.logger.add_log(llm_token_count_info_per_step)

    def calculate_pricing(self):
        """calculates cost of each step and adds it to logs"""
        # returning dummy cost (0) for type safety
        embedding_token_cost = (
            self.embedding_token_counter.total_embedding_token_count / 1000000
        ) * self.pricing_data.get(
            "text-embedding-3-large", {"text-embedding-3-large": {"input_tokens": 0}}
        ).get("input_tokens")
        mm_llm_token_cost_input = (
            self.mm_llm_token_counter.prompt_llm_token_count / 1000000
        ) * self.pricing_data.get("gpt-4o", {"gpt-4o": {"input_tokens": 0}}).get(
            "input_tokens"
        )
        mm_llm_token_cost_output = (
            self.mm_llm_token_counter.completion_llm_token_count / 1000000
        ) * self.pricing_data.get("gpt-4o", {"gpt-4o": {"output_tokens": 0}}).get(
            "output_tokens"
        )

        total_cost_per_step = (
            embedding_token_cost + mm_llm_token_cost_input + mm_llm_token_cost_output
        )

        self.result.total_estimated_cost += total_cost_per_step

        cost_dict = {
            "embedding_tokens_cost": embedding_token_cost,
            "llm_prompt_tokens_cost": mm_llm_token_cost_input,
            "llm_completion_tokens_cost": mm_llm_token_cost_output,
            "total_cost_per_step": total_cost_per_step,
        }
        self.logger.add_log(cost_dict)

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
