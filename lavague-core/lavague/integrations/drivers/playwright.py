from typing import Tuple, Callable, Optional
from playwright.sync_api import Page
from ...driver import BaseDriver

class PlaywrightDriver(BaseDriver):
    def __init__(self, get_sync_playwright_page: Optional[Callable[[], Page]] = None):
        super().__init__(get_sync_playwright_page)
    
    def default_init_code(self) -> Page:
        # these imports are necessary as they will be pasted to the output
        try:
            from playwright.sync_api import sync_playwright
        except (ImportError, ModuleNotFoundError) as error:
            raise ImportError(
                "Please install playwright using `pip install playwright` and then `playwright install` to install the necessary browser drivers"
            ) from error
        p = sync_playwright().__enter__()
        browser = p.chromium.launch()
        page = browser.new_page()
        return page

    def get_driver(self) -> Page:
        return self.driver

    def get_url(self) -> str:
        return self.driver.url

    def go_to_url_code(self, url: str) -> str:
        return f'page.goto("{url}")'

    def goto(self, url: str) -> None:
        return self.driver.goto(url)

    def get_html(self) -> str:
        return self.driver.content()

    def get_screenshot(self, filename: str) -> None:
        return self.driver.screenshot(path=filename)

    def get_dummy_code(self) -> str:
        return "page.mouse.wheel(delta_x=0, delta_y=500)"

    def destroy(self) -> None:
        self.driver.close()

    def check_visibility(self, xpath: str) -> bool:
        try:
            return self.driver.locator(f'xpath={xpath}').is_visible()
        except:
            return False

    def exec_code(self, code: str):
        exec(self._get_import_lines())
        page = self.driver
        exec(code)