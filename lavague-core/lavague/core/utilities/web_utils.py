from IPython.display import display, clear_output
from PIL.PngImagePlugin import PngImageFile
from PIL import Image
import base64
from lavague.core.utilities.format_utils import (
    return_assigned_variables,
    keep_assignments,
)
from io import BytesIO
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def display_screenshot(img: PngImageFile):
    clear_output()
    if img.mode == "RGBA":
        img = img.convert("RGB")

    try:
        __IPYTHON__
        display(img)
    except:
        img.show()


def get_highlighted_element(driver: WebDriver, generated_code):
    # TODO: Make code function with abstract driver
    # Extract the assignments from the generated code
    assignment_code = keep_assignments(generated_code)

    # We add imports to the code to be executed
    code = f"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
{assignment_code}""".strip()

    local_scope = {"driver": driver}

    exec(code, local_scope, local_scope)

    # We extract pairs of variables assigned during execution with their name and pointer
    variable_names = return_assigned_variables(generated_code)

    elements = {}

    for variable_name in variable_names:
        var = local_scope[variable_name]
        if type(var) == WebElement:
            elements[variable_name] = var

    if len(elements) == 0:
        raise ValueError(f"No element found.")

    outputs = []
    for element_name, element in elements.items():
        local_scope = {"driver": driver, element_name: element}

        code = f"""
element = {element_name}
driver.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, "border: 2px solid red;")
driver.execute_script("arguments[0].scrollIntoView({{block: 'center'}});", element)
screenshot = driver.get_screenshot_as_png()

x1 = element.location['x']
y1 = element.location['y']

x2 = x1 + element.size['width']
y2 = y1 + element.size['height']

viewport_width = driver.execute_script("return window.innerWidth;")
viewport_height = driver.execute_script("return window.innerHeight;")
"""
        exec(code, globals(), local_scope)
        bounding_box = {
            "x1": local_scope["x1"],
            "y1": local_scope["y1"],
            "x2": local_scope["x2"],
            "y2": local_scope["y2"],
        }
        viewport_size = {
            "width": local_scope["viewport_width"],
            "height": local_scope["viewport_height"],
        }
        screenshot = local_scope["screenshot"]
        screenshot = BytesIO(screenshot)
        screenshot = Image.open(screenshot)
        output = {
            "screenshot": screenshot,
            "bounding_box": bounding_box,
            "viewport_size": viewport_size,
        }
        outputs.append(output)
    return outputs
