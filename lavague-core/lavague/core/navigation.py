import time
from lavague.core.utilities.web_utils import display_screenshot, sort_files_by_creation
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from lavague.core.logger import AgentLogger
from lavague.core.action_engine import BaseActionEngine
from lavague.core.base_driver import BaseDriver
from PIL import Image

class NavigationControl(BaseActionEngine):
    driver: BaseDriver
    time_between_actions: float
    logger: AgentLogger

    def __init__(
        self,
        driver: BaseDriver,
        time_between_actions: float = 1.5,
        logger: AgentLogger = None,
    ) -> None:
        self.driver: BaseDriver = driver
        self.time_between_actions = time_between_actions
        self.logger = logger
        self.display = False

    def set_display(self, display: bool):
        self.display = display

    def execute_instruction(self, instruction: str):
        logger = self.logger
        # TODO: Not clean the fact that we have driver / meta_driver around. Should settle for better names
        meta_driver: BaseDriver = self.driver
        driver: WebDriver = meta_driver.get_driver()
        display_page = False

        if "SCROLL_DOWN" in instruction:
            code = """driver.execute_script("window.scrollBy(0, window.innerHeight);")"""
        elif "SCROLL_UP" in instruction:
            code = """driver.execute_script("window.scrollBy(0, -window.innerHeight);")"""
        elif "WAIT" in instruction:
            code = f"""
import time
time.sleep({self.time_between_actions})"""
        elif "BACK" in instruction:
            code = """driver.back()"""
        elif "SCAN" in instruction:
            # TODO: Should scan be in the navigation controls or in the driver?
            code = """meta_driver.get_screenshots_whole_page()"""
            display_page = True
        else:
            raise ValueError(f"Unknown instruction: {instruction}")

        local_scope = {"driver": driver, "meta_driver": meta_driver}
        exec(code, local_scope, local_scope)
        if display_page and self.display:
            try:
                scr_path = self.driver.get_current_screenshot_folder()
                lst = sort_files_by_creation(scr_path)
                for scr in lst:
                    img = Image.open(scr_path.as_posix() + "/" + scr)
                    display_screenshot(img)
                    time.sleep(0.35)
            except:
                pass
        success = True
        output = None

        if logger:
            log = {
                "engine": "Navigation Controls",
                "instruction": instruction,
                "engine_log": None,
                "success": success,
                "output": output,
                "code": code,
            }
            logger.add_log(log)

        return success, output
