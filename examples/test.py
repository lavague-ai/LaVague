from lavague.integrations.contexts.playwright import PlaywrightContext
from lavague import ActionEngine

selenium_context = PlaywrightContext.from_defaults()
action_engine = ActionEngine.from_context(selenium_context)
action = action_engine.get_action("Enter hop inside the search bar and then press enter", "https://news.ycombinator.com")
print(action)

# from lavague.integrations.drivers.selenium import SeleniumDriver

# driver = SeleniumDriver()
# driver.goto("https://huggingface.co")

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.keys import Keys
# import os.path

# chrome_options = Options()
# chrome_options.add_argument("--headless")  # Ensure GUI is off
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--window-size=1600,900")

# homedir = os.path.expanduser("~")

# # Paths to the chromedriver files
# path_linux = f"{homedir}/chromedriver-linux64/chromedriver"
# path_testing = f"{homedir}/chromedriver-testing/chromedriver"
# path_mac = (
#     "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
# )

# # To avoid breaking change kept legacy linux64 path
# if os.path.exists(path_linux):
#     chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
#     webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")
# elif os.path.exists(path_testing):
#     if os.path.exists(f"{homedir}/chrome-testing/{path_mac}"):
#         chrome_options.binary_location = f"{homedir}/chrome-testing/{path_mac}"
#     # Can add support here for other chrome binaries with else if statements
#     webdriver_service = Service(f"{homedir}/chromedriver-testing/chromedriver")
# else:
#     raise FileNotFoundError("Neither chromedriver file exists.")

# driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
# driver.get("https://news.ycombinator.com/")