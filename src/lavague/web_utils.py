from .format_utils import keep_assignments, return_assigned_variables
from selenium.webdriver.remote.webelement import WebElement
from IPython.display import display, clear_output
from PIL import Image
from PIL.PngImagePlugin import PngImageFile
import base64

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


def get_highlighted_element(generated_code, driver) -> PngImageFile:

    assignment_code = keep_assignments(generated_code)

    code = f"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
{assignment_code}
    """.strip()

    local_scope = {"driver": driver}

    exec(code, globals(), local_scope)

    variable_names = return_assigned_variables(generated_code)

    elements = []

    for variable_name in variable_names:
        var = local_scope[variable_name]
        if type(var) == WebElement:
            elements.append(var)

    first_element = elements[0]
    driver.execute_script("arguments[0].setAttribute('style', arguments[1]);", first_element, "border: 2px solid red;")
    driver.execute_script("arguments[0].scrollIntoView();", first_element)
    driver.save_screenshot("screenshot.png")
    image = Image.open("screenshot.png")
    driver.execute_script("arguments[0].setAttribute('style', '');", first_element)
    return image