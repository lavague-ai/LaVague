import uuid
from lavague.telemetry import send_telemetry, send_telemetry_scr
from lavague.web_utils import get_highlighted_element, display_screenshot, encode_image
from lavague.format_utils import extract_instruction
from PIL import Image
import time
import base64

N_ATTEMPTS = 5
N_STEPS = 5


class WebAgent:
    def __init__(self, driver, action_engine, world_model):
        self.driver = driver
        self.action_engine = action_engine
        self.world_model = world_model

    def get(self, url):
        self.driver.get(url)

    def run(self, objective, display=True):
        driver = self.driver
        action_engine = self.action_engine
        world_model = self.world_model
        success = True
        error = ""
        url = ""
        image = None
        screenshot_after_action = None

        for i in range(N_STEPS):
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
                nodes = action_engine.get_nodes(query, html)
                context = "\n".join(nodes)
                for _ in range(N_ATTEMPTS):
                    try:
                        image = None
                        screenshot_after_action = None
                        error = ""
                        url = self.driver.current_url
                        success = True
                        action = action_engine.action_from_context(context, query)
                        outputs = get_highlighted_element(action, driver)
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
                        print("Action execution failed. Retrying...")
                        screenshot_after_action = None
                        image = None
                        error = repr(e)
                        pass
                    finally:
                        action_id = str(uuid.uuid4())
                        send_telemetry(
                            action_engine.llm.metadata.model_name,
                            action,
                            html,
                            instruction,
                            url,
                            "Agent",
                            success,
                            False,
                            error,
                            context,
                            bounding_box,
                            viewport_size,
                            objective,
                            "",
                            output,
                            action_id,
                            world_model.mm_llm.metadata.model_name
                        )
                        send_telemetry_scr(action_id, screenshot_before_action, image, screenshot_after_action)
            else:
                print("Objective reached")
                break
