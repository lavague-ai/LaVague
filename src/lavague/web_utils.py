from .format_utils import keep_assignments, return_assigned_variables
from selenium.webdriver.remote.webelement import WebElement
from IPython.display import display, clear_output
from PIL import Image
from PIL.PngImagePlugin import PngImageFile
import base64

def resize_driver(driver, width, targeted_height):
    """Resize the Selenium driver viewport to a targeted height and width.
    This is due to Selenium only being able to set window size and not viewport size.
    """
    driver.set_window_size(width, targeted_height)
    
    viewport_height = driver.execute_script("return window.innerHeight;")

    height_difference = targeted_height - viewport_height
    driver.set_window_size(width, targeted_height + height_difference)


# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def display_screenshot(img: PngImageFile):
    clear_output()
    if img.mode == 'RGBA':
        img = img.convert('RGB')

    # Display the image directly in the notebook
    display(img)

def get_highlighted_element(generated_code, driver):

    # Extract the assignments from the generated code
    assignment_code = keep_assignments(generated_code)

    # We add imports to the code to be executed
    code = f"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
{assignment_code}
    """.strip()

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

        local_scope = {"driver": driver, 
            element_name: element}
        
        code = f"""
element = {element_name}
driver.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, "border: 2px solid red;")
driver.execute_script("arguments[0].scrollIntoView({{block: 'center'}});", element)
driver.save_screenshot("screenshot.png")

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
            "y2": local_scope["y2"]
        }
        viewport_size = {
            "width": local_scope["viewport_width"],
            "height": local_scope["viewport_height"]
        }
        image = Image.open("screenshot.png")
        output = {
            "image": image,
            "bounding_box": bounding_box,
            "viewport_size": viewport_size
        }
        outputs.append(output)
    return outputs