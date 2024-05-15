from IPython.display import display, clear_output
from PIL.PngImagePlugin import PngImageFile
import base64


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
