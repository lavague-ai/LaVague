from IPython.display import Image, display, clear_output
from lavague.web_utils import get_highlighted_element, display_screenshot, encode_image
from lavague.format_utils import extract_instruction
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
        
    def run(self, objective):

        self.driver.save_screenshot("screenshot.png")
        display(Image("screenshot.png"))

        print("Objective: ", objective)

        for i in range(N_STEPS):
            print("Computing an action plan...")

            # We get the current screenshot into base64 before sending to our World Model
            state = encode_image("screenshot.png")

            # We get the instruction for the action engine using the world model
            output = self.world_model.get_instruction(state, objective)
            instruction = extract_instruction(output)

            print("Thoughts:", output)
            if instruction != "STOP":
                query = instruction
                html = self.driver.page_source

                # We retrieve once the parts of the HTML that are relevant for the action generation, in case of we have to retry several times
                nodes = self.action_engine.get_nodes(query, html)
                context = "\n".join(nodes)
                for _ in range(N_ATTEMPTS):
                    try:
                        action = self.action_engine.action_from_context(context, query)
                        screenshot_before_action = get_highlighted_element(action, self.driver)
                        clear_output()
                        display(screenshot_before_action)
                        print("Showing the next element to interact with")
                        time.sleep(3)

                        exec(action)
                        time.sleep(3)
                        clear_output()
                        display_screenshot(self.driver)
                        break

                    except Exception as e:
                        print("Action execution failed. Retrying...")
                        pass
            else:
                print("Objective reached")
                break