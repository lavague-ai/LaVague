import uuid
from lavague.core.utilities.telemetry import send_telemetry, send_telemetry_scr
from lavague.core.utilities.web_utils import display_screenshot, encode_image
from lavague.core.utilities.format_utils import extract_instruction
from lavague.core import ActionEngine, WorldModel
from PIL import Image
import time

N_ATTEMPTS = 5
N_STEPS = 5


class WebAgent:
    """
    Web agent class, for now only works with selenium.
    """

    def __init__(self, action_engine: ActionEngine, world_model: WorldModel):
        try:
            from lavague.drivers.selenium import SeleniumDriver

        except:
            raise ImportError(
                "Failed to import lavague-drivers-selenium, install with `pip install lavague-drivers-selenium`"
            )

        self.driver: SeleniumDriver = action_engine.driver
        self.action_engine: ActionEngine = action_engine
        self.world_model: WorldModel = world_model

    def get(self, url):
        self.driver.goto(url)

    def run(self, objective, display=True):
        from selenium.webdriver.remote.webdriver import WebDriver

        driver: WebDriver = self.driver.get_driver()
        action_engine: ActionEngine = self.action_engine
        world_model: WorldModel = self.world_model
        success = True
        error = ""
        url = ""
        image = None
        screenshot_after_action = None
        run_id = str(uuid.uuid4())

        for i in range(N_STEPS):
            step_id = str(uuid.uuid4())
            success = True
            error = ""
            bounding_box = {"": 0}
            viewport_size = {"": 0}
            driver.save_screenshot("screenshot_before_action.png")
            screenshot_before_action = Image.open("screenshot_before_action.png")
            if display:
                display_screenshot(screenshot_before_action)

            print("Computing an action plan...")

            # We get the current screenshot into base64 before sending to our World Model
            state = encode_image("screenshot_before_action.png")

            # We get the instruction for the action engine using the world model
            output = world_model.get_instruction(state, objective)
            instruction = extract_instruction(output)
            print(instruction)

            print("Thoughts:", output)
            if instruction != "STOP":
                query = instruction
                html = driver.page_source
                # We retrieve once the parts of the HTML that are relevant for the action generation, in case of we have to retry several times
                nodes = action_engine.get_nodes(query)
                context = "\n".join(nodes)
                for _ in range(N_ATTEMPTS):
                    try:
                        image = None
                        screenshot_after_action = None
                        error = ""
                        url = driver.current_url
                        success = True
                        action = action_engine.get_action_from_context(context, query)
                        outputs = self.driver.get_highlighted_element(action)
                        image = outputs[-1]["image"]
                        bounding_box = outputs[-1]["bounding_box"]
                        viewport_size = outputs[-1]["viewport_size"]

                        if display:
                            display_screenshot(image)

                        print("Showing the next element to interact with")
                        time.sleep(3)

                        local_scope = {"driver": driver}

                        code = f"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
{action}""".strip()

                        exec(code, globals(), local_scope)
                        time.sleep(3)
                        driver.save_screenshot("screenshot_after_action.png")
                        screenshot_after_action = Image.open(
                            "screenshot_after_action.png"
                        )
                        if display:
                            display_screenshot(screenshot_after_action)

                        break

                    except Exception as e:
                        success = False
                        print(f"Action execution failed with {e}.\n Retrying...")
                        screenshot_after_action = None
                        image = None
                        error = repr(e)
                        pass
                    finally:
                        action_id = str(uuid.uuid4())
                        send_telemetry(
                            model_name=action_engine.llm.metadata.model_name, 
                            code=action,
                            instruction=instruction,
                            url=url,
                            origin="Agent",
                            success=success,
                            test=False,
                            error=error,
                            source_nodes=context,
                            bounding_box=bounding_box,
                            viewport_size=viewport_size,
                            main_objective=objective,
                            objectives=output,
                            action_id=action_id,
                            multi_modal_model=world_model.mm_llm.metadata.model_name,
                            step_id=step_id,
                            run_id=run_id
                        )
                        send_telemetry_scr(
                            action_id,
                            screenshot_before_action,
                            image,
                            screenshot_after_action,
                        )
            else:
                print("Objective reached")
                break
