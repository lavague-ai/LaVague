import yaml
import time
from llama_index.core import SimpleDirectoryReader
from selenium.webdriver.remote.webdriver import WebDriver
from lavague.core.action_engine import ActionEngine
from lavague.core.python_engine import PythonEngine
from lavague.core.world_model import WorldModel
from lavague.core.navigation import NavigationControl
from lavague.drivers.selenium import SeleniumDriver
from lavague.core.utilities.format_utils import (
    extract_next_engine,
    extract_world_model_instruction,
)


class WebAgent:
    """
    Web agent class, for now only works with selenium.
    """

    def __init__(
        self,
        world_model: WorldModel,
        action_engine: ActionEngine,
        python_engine: PythonEngine,
        n_attempts: int = 5,
        n_steps: int = 10,
        time_between_actions: float = 1.5,
    ):
        driver = action_engine.driver

        self.driver: SeleniumDriver = driver
        self.action_engine: ActionEngine = action_engine
        self.world_model: WorldModel = world_model
        self.navigation_control: NavigationControl = NavigationControl(driver.driver)
        self.python_engine: PythonEngine = python_engine

        self.n_attempts = n_attempts
        self.n_steps = n_steps
        self.time_between_actions = time_between_actions

    def get(self, url):
        self.driver.goto(url)

    def run(self, objective: str, user_data=None, display_in_notebook: bool = False):
        world_model = self.world_model
        action_engine = self.action_engine
        driver: WebDriver = self.driver.driver
        python_engine = self.python_engine
        navigation_control = self.navigation_control

        n_steps = self.n_steps
        n_attempts = self.n_attempts
        time_between_actions = self.time_between_actions

        previous_instructions = "[NONE]"
        last_engine = "[NONE]"

        current_state = {
            "external_observations": {
                "vision": "[SCREEENSHOT]",
            },
            "internal_state": {
                "user_inputs": [],
                "agent_outputs": [],
            },
        }

        if user_data:
            current_state["internal_state"]["user_inputs"].append(user_data)

        # TO DO: Don't save on disk the screenshot but do it in memory
        driver.save_screenshot("screenshots/output.png")
        image_documents = SimpleDirectoryReader("./screenshots").load_data()

        for _ in range(n_steps):
            current_state_str = yaml.dump(current_state, default_flow_style=False)

            world_model_output = world_model.get_instruction(
                objective,
                previous_instructions,
                last_engine,
                current_state_str,
                image_documents,
            )

            print(world_model_output)

            next_engine = extract_next_engine(world_model_output)
            instruction = extract_world_model_instruction(world_model_output)

            if next_engine == "Navigation Engine":
                query = instruction
                nodes = action_engine.get_nodes(query)
                llm_context = "\n".join(nodes)

                success = False

                for _ in range(n_attempts):
                    try:
                        action = action_engine.get_action_from_context(
                            llm_context, query
                        )
                        action_code = f"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
                        {action}""".strip()

                        local_scope = {"driver": driver}
                        exec(action_code, local_scope, local_scope)

                        success = True
                        break
                    except Exception as e:
                        print(f"Action execution failed. Retrying...")
                        print("Error: ", e)
                        pass
                if not success:
                    instruction = "[FAILED] " + instruction
                time.sleep(time_between_actions)
                driver.save_screenshot("screenshots/output.png")
                image_documents = SimpleDirectoryReader("./screenshots").load_data()

            elif "Python Engine" in next_engine:
                state = {"html": driver.page_source}
                success = False

                for _ in range(n_attempts):
                    try:
                        python_code = python_engine.generate_code(instruction, state)
                        output = python_engine.execute_code(python_code, state)

                        if output:
                            current_state["internal_state"]["agent_outputs"].append(
                                output
                            )
                            success = True
                            break
                        else:
                            print("Empty output of Python engine")
                            print("Code generated by Python Engine: ", python_code)
                            print("Output generated by Python Engine: ", output)
                            pass
                    except Exception as e:
                        print(f"Python engine execution failed. Retrying...")
                        print("Error: ", e)
                        pass

                if not success:
                    instruction = "[FAILED] " + instruction

            elif "Navigation Controls" in next_engine:
                navigation_control.execute_instruction(instruction)
                driver.save_screenshot("screenshots/output.png")
                image_documents = SimpleDirectoryReader("./screenshots").load_data()

            elif next_engine == "STOP" or instruction == "STOP":
                print("Objective reached. Stopping...")
                break

            if previous_instructions == "[NONE]":
                previous_instructions = f"""
- {instruction}"""
            else:
                previous_instructions += f"""
- {instruction}"""

            last_engine = next_engine

        output = current_state["internal_state"]["agent_outputs"]
        return output
