from typing import Optional

from lavague.exporters.python import PythonExporter, exclude_from_export
from lavague.sdk.trajectory import TrajectoryData
from lavague.sdk.action.navigation import NavigationOutput
from lavague.sdk.action.extraction import ExtractionOutput

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

TIMEOUT = 10


class PythonSeleniumExporter(PythonExporter):
    def setup(self, trajectory: TrajectoryData):
        # Setup of the driver
        from selenium.webdriver.chrome.options import Options
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        chrome_options = Options()

        TIMEOUT = 10
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
        )
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-site-isolation-trials")

        viewport_size = trajectory.viewport_size
        width = viewport_size[0]
        height = viewport_size[1]

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(width, height)
        viewport_height = driver.execute_script("return window.innerHeight;")
        driver.set_window_size(width, 2 * height - viewport_height)
        driver.get(trajectory.start_url)

    def teardown(self, trajectory: TrajectoryData):
        # We destroy the driver
        with exclude_from_export():
            driver = self.get_driver()
        driver.quit()

    def get_driver(self) -> webdriver.Chrome:
        return getattr(self, "driver")

    def click(self, action_output: NavigationOutput) -> Optional[str]:
        with exclude_from_export():
            driver = self.get_driver()
        element = WebDriverWait(driver, TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, action_output.xpath))
        )
        element.click()

    def hover(self, action_output: NavigationOutput) -> Optional[str]:
        with exclude_from_export():
            driver = self.get_driver()
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, action_output.xpath))
        )
        ActionChains(driver).move_to_element(element).perform()

    def set_value(self, action_output: NavigationOutput) -> Optional[str]:
        with exclude_from_export():
            driver = self.get_driver()
        element = WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_element_located((By.XPATH, action_output.xpath))
        )
        element.send_keys(action_output.value)

    def set_value_and_enter(self, action_output: NavigationOutput) -> Optional[str]:
        with exclude_from_export():
            driver = self.get_driver()
        element = WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_element_located((By.XPATH, action_output.xpath))
        )
        element.send_keys(action_output.value + Keys.ENTER)

    def extract(self, action_output: ExtractionOutput) -> Optional[str]:
        with exclude_from_export():
            driver = self.get_driver()
        element = WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_element_located((By.XPATH, action_output.xpath))
        )
        element.text

    def scroll(self, action_output: NavigationOutput) -> Optional[str]:
        with exclude_from_export():
            driver = self.get_driver()

        viewport_height = driver.execute_script("return window.innerHeight")
        scroll_amount = int(viewport_height * 0.75)

        if action_output.value == "UP":
            scroll_amount = -scroll_amount

        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
