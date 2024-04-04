from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By # needed by the generated code
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys # needed by the generated code
import os.path

chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensure GUI is off
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1600,900")

homedir = os.path.expanduser("~")
chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")

driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

driver.get("https://huggingface.co")

## Click on the Datasets item on the menu,
# between Models and Spaces

## Click on the search bar 'Filter by name', type 'The Stack', and press 'Enter'
## Scroll by 500 pixels