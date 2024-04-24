from typing import Any, Tuple, Optional, Callable
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from ...driver import BaseDriver

class SeleniumDriver(BaseDriver):
    def __init__(self, get_selenium_driver: Optional[Callable[[], WebDriver]] = None):
        super().__init__(get_selenium_driver)

    def default_init_code(self) -> Any:
        # these imports are necessary as they will be pasted to the output
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        import os.path

        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ensure GUI is off
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1600,900")

        homedir = os.path.expanduser("~")

        # Paths to the chromedriver files
        path_linux = f"{homedir}/chromedriver-linux64/chromedriver"
        path_testing = f"{homedir}/chromedriver-testing/chromedriver"
        path_mac = (
            "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
        )

        # To avoid breaking change kept legacy linux64 path
        if os.path.exists(path_linux):
            chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
            webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")
        elif os.path.exists(path_testing):
            if os.path.exists(f"{homedir}/chrome-testing/{path_mac}"):
                chrome_options.binary_location = f"{homedir}/chrome-testing/{path_mac}"
            # Can add support here for other chrome binaries with else if statements
            webdriver_service = Service(f"{homedir}/chromedriver-testing/chromedriver")
        else:
            raise FileNotFoundError("Neither chromedriver file exists.")

        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        return driver

    def get_driver(self) -> WebDriver:
        return self.driver

    def get_url(self) -> str:
        return self.driver.current_url

    def go_to_url_code(self, url: str) -> str:
        return f'driver.get("{url}")'

    def goto(self, url: str) -> None:
        self.driver.get(url)

    def get_html(self) -> str:
        return self.driver.page_source

    def get_screenshot(self, filename: str) -> None:
        self.driver.save_screenshot(filename)

    def get_dummy_code(self) -> str:
        return 'driver.execute_script("window.scrollBy(0, 500)")'

    def destroy(self) -> None:
        self.driver.quit()

    def check_visibility(self, xpath: str) -> bool:
        try:
            return self.driver.find_element(By.XPATH, xpath).is_displayed()
        except:
            return False
    
    def exec_code(self, code: str):
        exec(self._get_import_lines())
        driver = self.driver
        exec(code)