from abc import ABC, abstractmethod
from copy import deepcopy
from difflib import SequenceMatcher

from anytree import Node
import heapq
from io import BytesIO
import logging
import os
import shutil
from typing import Annotated, Any, Optional

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

from lavague.core.utilities.profiling import (
    ChartGenerator,
    time_profiler,
    start_new_step,
    clear_profiling_data,
)

logging_print = logging.getLogger(__name__)
logging_print.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(format)
logging_print.addHandler(ch)
logging_print.propagate = False


class BaseAgent(ABC):
    @abstractmethod
    def run_step(self, instruction: str) -> ActionResult:
        pass


class WebAgent(BaseAgent):
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
                start_new_step()
                with time_profiler("Run step", full_step_profiling=True):
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

    def get_summary(self):
        from lavague.core.utilities.profiling import agent_events, agent_steps

        chart_generator = ChartGenerator(
            agent_events=agent_events, agent_steps=agent_steps
        )
        plot = chart_generator.plot_waterfall()
        table = chart_generator.get_summary_df()

        clear_profiling_data()

        return plot, table


Action = Annotated[tuple[str, str], "Engine name and instruction"]


class State(Node):
    """
    State class for tree search.
    """

    def __init__(self, url, parent = None):

        super().__init__(name=url, parent=parent)

        self.url = self.name
        self.score = None
        self.observations = None

        # the children node inherits his parent's memory
        if parent is None:
            self.memory = ShortTermMemory()
        else:
            self.memory = deepcopy(parent.memory)

        self.result = ActionResult(
            instruction=None,
            code="",
            success=False,
            output=None,
            total_estimated_tokens=0,
            total_estimated_cost=0.0,
        )

    def __gt__(self, other):
        """Comparison method for states.

        Used to sort states in the priority queue when they have the same score.
        """
        return (self.score, self.depth, self.url) > (other.score, other.depth, other.url)

    def __repr__(self):
        return f"State(depth={self.depth}, url={self.url}, score={self.score})"


class TreeSearchWebAgent(WebAgent):
    """
    Web agent implementing Tree Search algorithm.
    """

    def __init__(
        self,
        world_model: WorldModel,
        action_engine: ActionEngine,
        token_counter: Optional[TokenCounter] = None,
        n_steps: int = 5,
        max_depth: int = 5,
        branching_factor: int = 5,
        sample_size: int = 10,
        clean_screenshot_folder: bool = True,
        logger: AgentLogger = None,
    ):

        super().__init__(
            world_model,
            action_engine,
            token_counter,
            n_steps,
            clean_screenshot_folder,
            logger,
        )

        # memory will be carried by states rather than agent so we reset it
        self.st_memory = None

        # search hyperparameters
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.sample_size = sample_size

        # search data structures
        self._queue = []
        self._visited = set()
        self._best: State | None = None

    def _update_observations(self, state: State):
        """Updates the state with new observations."""

        state.observations = self.driver.get_obs()

    def _init_queue(self) -> None:
        """Initializes the priority queue with the initial state."""

        self._update_queue(0.0, State(url=self.driver.get_url()))

    def _update_queue(self, score: float, state: State) -> None:
        """Updates the priority queue with a new state."""

        # score is negated to use the priority queue as a max-heap
        heapq.heappush(self._queue, (-score, state))

    def _get_next_state_from_queue(self) -> State:
        """Gets the next state to explore."""

        # score is negated to use the priority queue as a max-heap
        _, state = heapq.heappop(self._queue)
        logging.info(f"Current queue: {[s for _, s in self._queue]}")
        logging_print.info(f"Exploring state: {state}")

        return state

    def _update_best(self, candidate: State) -> None:
        """Updates the best state found so far."""

        if self._best is None or candidate.score > self._best.score:
            self._best = candidate
            logging_print.info(f"New best state found: {self._best.url}")

    def _score(self, objective: str, state: State) -> None:
        """State scoring function.

        Obtained by sampling completions from the model
        and averaging the scores.
        """

        def score(text: str) -> float:
            if text.lower() == "yes":
                return 1.0
            elif text.lower() == "no":
                return 0.0
            return 0.5

        # get completions from the LLM
        current_state, past = state.memory.get_state()
        obs = state.observations
        world_model_outputs = self.world_model.get_scores(
            objective, current_state, past, obs, temperature=1.0, top_p=0.95, n=self.sample_size,
        )

        # final score is the mean of the samples
        scores = [score(o) for o in world_model_outputs]
        score = sum(scores) / self.sample_size

        state.score = score
        logging_print.info(f"Score is: {state.score} (samples: {scores}) for URL {state.url}")

    def _backtrack(self, state: State):
        """Backtracks to the input state."""

        logging_print.info(f"Backtracking to {state.url}")

        # NOTE: backtracking based on URL is a huge simplification and won't work with all websites (e.g. SPAs)
        self.get(state.url)
        self._visited.add(state.url)

    def _remove_duplicates(self, actions: list[Action]) -> list[Action]:
        """Removes duplicate actions from the list.

        Based on the similarity of the instructions.
        """

        def remove_duplicates(strings: list[str], threshold=0.80) -> list[str]:
            """Removes duplicates from a list of strings  using a similarity threshold."""
            unique_strings = []
            for s in strings:
                if not any(SequenceMatcher(None, s, u).ratio() > threshold for u in unique_strings):
                    unique_strings.append(s)
            return unique_strings

        # first group them by engine
        action_groups = {}
        for action in actions:
            engine_name = action[0]
            action_groups.setdefault(engine_name, [])
            action_groups[engine_name].append(action[1])

        # then remove duplicates instructions
        unique_actions = []
        for engine, instructions in action_groups.items():
            unique_instructions = remove_duplicates(instructions)
            unique_actions.extend([(engine, i) for i in unique_instructions])

        return unique_actions

    def _sample_children_actions(self, objective: str, state: State, n: int) -> list[Action]:
        """Samples children actions from the world model."""

        current_state, past = state.memory.get_state()
        obs = state.observations
        world_model_outputs = self.world_model.get_instructions(
            objective, current_state, past, obs, temperature=1.0, top_p=0.95, n=n,
        )

        logging_print.info(f"\n{'='*80}\n".join(world_model_outputs))

        next_engine_names = [extract_next_engine(o) for o in world_model_outputs]
        instructions = [extract_world_model_instruction(o) for o in world_model_outputs]
        actions = [(n, i) for n, i in zip(next_engine_names, instructions)]

        # remove duplicates
        actions = self._remove_duplicates(actions)

        logging_print.info("Actions sampled: \n" + "\n".join([str(a) for a in actions]))

        return actions

    @staticmethod
    def _reached_objective(action: Action) -> bool:
        engine_name = action[0]
        return engine_name == "COMPLETE" or engine_name == "SUCCESS"

    def _update_successful_result(self, action: Action, state: State) -> None:
        self.result.success = True
        self.result.output = action[1]
        logging_print.info("Objective reached. Stopping...")
        self.logger.add_log(state.observations)

        self.process_token_usage()
        self.logger.end_step()

    def _perform_action(self, action: Action, state: State) -> ActionResult:
        next_engine_name, instruction = action
        action_result = self.action_engine.dispatch_instruction(
            next_engine_name, instruction
        )

        logging_print.info(
            f"Performed action: [{next_engine_name}] <{instruction}> and reached URL: {self.driver.get_url()}"
        )

        if action_result.success:
            logging_print.info(f"Performed action successfully")
            self.result.code += action_result.code
            self.result.output = action_result.output
        else:
            logging_print.info(f"Failed to perform action")
        state.memory.update_state(
            instruction,
            next_engine_name,
            action_result.success,
            action_result.output,
        )
        self.logger.add_log(state.observations)

        self.process_token_usage()
        self.logger.end_step()

        return action_result

    def run(
        self,
        objective: str,
        user_data=None,
        display: bool = False,
        log_to_db: bool = is_flag_true("LAVAGUE_LOG_TO_DB"),
        step_by_step=False,
    ) -> ActionResult:
        # we need to initialize the queue at the beginning of each run
        self._init_queue()
        return super().run(objective, user_data, display, log_to_db, step_by_step)

    def run_step(self, objective: str) -> Optional[ActionResult]:

        # go to most urgent state
        state = self._get_next_state_from_queue()
        self._backtrack(state)
        self._update_observations(state)

        # score it and update best result
        self._score(objective, state)
        self._update_best(state)

        # explore children states
        if state.depth < self.max_depth:

            actions = self._sample_children_actions(objective, state, n=self.branching_factor)

            for action in actions:

                # check if we reached the objective
                if self._reached_objective(action):
                    self._update_successful_result(action, state)
                    return self.result

                # otherwise get child state
                self._backtrack(state)
                action_result = self._perform_action(action, state)

                if action_result.success:
                    child = State(url=self.driver.get_url(), parent=state)
                    self._update_queue(state.score, child)
