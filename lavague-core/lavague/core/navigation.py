import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class NavigationControl:
    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver

    def scroll_one_viewport(self, direction: Keys):
        viewport_height = self.driver.execute_script("return window.innerHeight")

        body = self.driver.find_element(By.TAG_NAME, "body")
        num_scrolls = (
            viewport_height // 50
        )  # Assuming each arrow key press scrolls 50 pixels
        for _ in range(num_scrolls):
            body.send_keys(direction)
            time.sleep(0.05)

    def execute_instruction(self, instruction):
        if "SCROLL_DOWN" in instruction:
            self.scroll_one_viewport(Keys.ARROW_DOWN)
        elif "SCROLL_UP" in instruction:
            self.scroll_one_viewport(Keys.ARROW_UP)
        elif "WAIT" in instruction:
            time.sleep(2)
        else:
            raise ValueError(f"Unknown instruction: {instruction}")
