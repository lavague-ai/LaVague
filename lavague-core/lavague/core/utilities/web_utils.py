from IPython.display import display, clear_output
from PIL.PngImagePlugin import PngImageFile
import base64
import os


def sort_files_by_creation(directory):
    def get_creation_time(item):
        item_path = os.path.join(directory, item)
        return os.path.getctime(item_path)

    items = os.listdir(directory)
    sorted_items = sorted(items, key=get_creation_time)
    return sorted_items


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
