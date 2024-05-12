
from lavague.web_utils import get_highlighted_element, display_screenshot, encode_image
from lavague.format_utils import extract_instruction
from PIL import Image
import time

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
        action_engine= self.action_engine
        world_model = self.world_model

        for i in range(N_STEPS):
            driver.save_screenshot("screenshot_before_action.jpeg")
            screenshot_before_action = Image.open("screenshot_before_action.jpeg")
            if display:
                display_screenshot(screenshot_before_action)
            
            print("Computing an action plan...")

            # We get the current screenshot into base64 before sending to our World Model
            state = encode_image("screenshot_before_action.jpeg")

            # We get the instruction for the action engine using the world model
            output = world_model.get_instruction(state, objective)
            instruction = extract_instruction(output)

            print("Thoughts:", output)
            if instruction != "STOP":
                query = instruction
                html = driver.page_source

                # We retrieve once the parts of the HTML that are relevant for the action generation, in case of we have to retry several times
                nodes = action_engine.get_nodes(query, html)
                context = "\n".join(nodes)
                for _ in range(N_ATTEMPTS):
                    try:
                        action = action_engine.action_from_context(context, query)
                        screenshot_with_highlight = get_highlighted_element(action, driver)
                        if display:
                            display_screenshot(screenshot_with_highlight)
                        
                        print("Showing the next element to interact with")
                        time.sleep(3)

                        local_scope = {"driver": driver}
                        
                        code = f"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
{action}""".strip()

                        exec(code, globals(), local_scope)
                        time.sleep(3)
                        driver.save_screenshot("screenshot_after_action.jpeg")
                        screenshot_after_action = Image.open("screenshot_after_action.jpeg")
                        if display:
                            display_screenshot(screenshot_after_action)
                        break

                    except Exception as e:
                        
                        print("Action execution failed. Retrying...")
                        print("Error:", e)
                        pass
            else:
                print("Objective reached")
                break