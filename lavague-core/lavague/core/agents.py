from io import BytesIO
import logging
import os
import shutil
from typing import Any, Optional, List, Tuple

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
            total_estimated_tokens=0,
            total_estimated_cost=0.0,
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

            # get and log token counts and costs
            token_counts, token_costs = self.process_token_usage()
            self.logger.add_log(token_counts)
            self.logger.add_log(token_costs)

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

        # get and log token counts and costs
        token_counts, token_costs = self.process_token_usage()
        self.logger.add_log(token_counts)
        self.logger.add_log(token_costs)

        self.logger.end_step()

    def run(
        self,
        objective: str,
        user_data=None,
        display: bool = False,
        log_to_db: bool = False,
        step_by_step=False,
    ) -> ActionResult:
        self.action_engine.set_display_all(display)
        try:
            if user_data:
                self.st_memory.set_user_data(user_data)

            self.logger.new_run()
            for _ in range(self.n_steps):
                result = self.run_step(objective)

                if result is not None:
                    break

                if step_by_step:
                    input("Press ENTER to continue")

        except KeyboardInterrupt:
            logging_print.warning("The agent was interrupted.")
            pass
        except Exception as e:
            logging_print.error(f"Error while running the agent: {e}")
            raise e
        finally:
            send_telemetry(self.logger.return_pandas())
            if log_to_db:
                local_db_logger = LocalDBLogger()
                local_db_logger.insert_logs(self)
        return self.result

    def process_token_usage(self) -> Tuple[dict, dict]:
        """Computes token counts and costs for the current step"""

        def deduplicate_events(events: List[Any]) -> List[Any]:
            """Helper function to deduplicate events if they are logged twice (temporary fix for #444)"""

            def are_events_equal(event1: Any, event2: Any) -> bool:
                """Helper function to compare two events by their attributes"""
                attributes_to_compare = [
                    "prompt",
                    "completion",
                    "completion_token_count",
                    "prompt_token_count",
                    "total_token_count",
                ]
                return all(
                    getattr(event1, attr) == getattr(event2, attr)
                    for attr in attributes_to_compare
                )

            deduplicated = []
            for event in events:
                print(getattr(event, "event_id"))
                if not any(
                    are_events_equal(existing_event, event)
                    for existing_event in deduplicated
                ):
                    deduplicated.append(event)
            return deduplicated

        def triage_events(events: List[Any]) -> Tuple[List[Any], List[Any]]:
            """Split events into world model and action engine events based on prompt start"""
            world_model_events = []
            other_events = []

            world_model_prompt_start = "You are an AI system specialized in high level reasoning. Your goal is to generate instructions for other specialized AIs to perform web actions to reach objectives given by humans."

            for event in events:
                if event.prompt.strip().startswith(world_model_prompt_start):
                    world_model_events.append(event)
                else:
                    other_events.append(event)

            return world_model_events, other_events

        def sum_token_counts(events: List[Any]) -> Tuple[int, int, int]:
            """Helper function to sum token counts for a list of events that belong together"""
            input_tokens = sum(event.prompt_token_count for event in events)
            output_tokens = sum(event.completion_token_count for event in events)
            total_tokens = sum(event.total_token_count for event in events)
            return input_tokens, output_tokens, total_tokens

        if (
            self.embedding_token_counter is not None
            and self.mm_llm_token_counter is not None
        ):
            # deduplicate and split llm events into world model and action engine events
            deduplicated_events = deduplicate_events(
                self.mm_llm_token_counter.llm_token_counts
            )
            world_model_events, action_engine_events = triage_events(
                deduplicated_events
            )

            # compute llm token counts
            WM_input_tokens, WM_output_tokens, WM_total_tokens = sum_token_counts(
                world_model_events
            )
            AE_input_tokens, AE_output_tokens, AE_total_tokens = sum_token_counts(
                action_engine_events
            )

            # compute embedding token counts
            embedding_total_tokens = (
                self.embedding_token_counter.total_embedding_token_count
            )

            total_step_tokens = (
                WM_total_tokens + AE_total_tokens + embedding_total_tokens
            )

            token_counts = {
                "world_model_input_tokens": WM_input_tokens,
                "world_model_output_tokens": WM_output_tokens,
                "action_engine_input_tokens": AE_input_tokens,
                "action_engine_output_tokens": AE_output_tokens,
                "total_world_model_tokens": WM_total_tokens,
                "total_action_engine_tokens": AE_total_tokens,
                "total_llm_tokens": WM_total_tokens + AE_total_tokens,
                "total_embedding_tokens": embedding_total_tokens,
                "total_step_tokens": total_step_tokens,
            }

            # compute llm and embedding token costs
            WM_input_cost, WM_output_cost, WM_total_cost = self.calculate_llm_pricing(
                WM_input_tokens, WM_output_tokens, self.world_model.mm_llm.model
            )
            AE_input_cost, AE_output_cost, AE_total_cost = self.calculate_llm_pricing(
                AE_input_tokens,
                AE_output_tokens,
                self.action_engine.navigation_engine.llm.model,
            )

            total_embedding_cost = self.calculate_embedding_pricing(
                embedding_total_tokens,
                self.action_engine.python_engine.embedding.model_name,
            )
            total_step_cost = WM_total_cost + AE_total_cost + total_embedding_cost

            token_costs = {
                "world_model_input_cost": WM_input_cost,
                "world_model_output_cost": WM_output_cost,
                "action_engine_input_cost": AE_input_cost,
                "action_engine_output_cost": AE_output_cost,
                "total_world_model_cost": WM_total_cost,
                "total_action_engine_cost": AE_total_cost,
                "total_llm_cost": WM_total_cost + AE_total_cost,
                "total_embedding_cost": total_embedding_cost,
                "total_step_cost": total_step_cost,
            }

            # update ActionEngine variables
            self.result.total_estimated_tokens += total_step_tokens
            self.result.total_estimated_cost += total_step_cost

            # reset counters
            self.mm_llm_token_counter.reset_counts()
            self.embedding_token_counter.reset_counts()
        else:
            # when token counters are not initialized, we return 0s
            token_counts = {
                "world_model_input_tokens": 0,
                "world_model_output_tokens": 0,
                "action_engine_input_tokens": 0,
                "action_engine_output_tokens": 0,
                "total_world_model_tokens": 0,
                "total_action_engine_tokens": 0,
                "total_llm_tokens": 0,
                "total_embedding_tokens": 0,
                "total_step_tokens": 0,
            }
            token_costs = {
                "world_model_input_cost": 0,
                "world_model_output_cost": 0,
                "action_engine_input_cost": 0,
                "action_engine_output_cost": 0,
                "total_world_model_cost": 0,
                "total_action_engine_cost": 0,
                "total_llm_cost": 0,
                "total_embedding_cost": 0,
                "total_step_cost": 0,
            }

        return token_counts, token_costs

    def calculate_llm_pricing(
        self, input_token_count: int, output_token_count: int, model: str
    ) -> Tuple[int, int, int]:
        """Computes token costs for LLM according to the pricing data available in pricing_config.yaml"""
        input_pricing = self.pricing_data.get(model, {model: {"input_tokens": 0}}).get(
            "input_tokens", 0
        )
        output_pricing = self.pricing_data.get(
            model, {model: {"output_tokens": 0}}
        ).get("output_tokens", 0)
        token_ratio = self.pricing_data.get(model, {model: {"token_ratio": 1}}).get(
            "token_ratio", 1
        )

        llm_input_token_cost = (input_token_count * input_pricing) / token_ratio
        llm_output_token_cost = (output_token_count * output_pricing) / token_ratio

        llm_cost = llm_input_token_cost + llm_output_token_cost

        return llm_input_token_cost, llm_output_token_cost, llm_cost

    def calculate_embedding_pricing(self, token_count: int, model: str) -> int:
        """Computes token costs for Embedding according to the pricing data available in pricing_config.yaml"""
        embedding_pricing = self.pricing_data.get(model, {model: {"tokens": 0}}).get(
            "tokens", 0
        )
        token_ratio = self.pricing_data.get(model, {model: {"token_ratio": 1}}).get(
            "token_ratio", 1
        )
        total_embedding_cost = (token_count * embedding_pricing) / token_ratio

        return total_embedding_cost

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
