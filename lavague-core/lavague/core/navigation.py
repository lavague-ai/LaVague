import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from lavague.core.logger import AgentLogger
from lavague.core.action_engine import BaseActionEngine
from lavague.core.base_driver import BaseDriver

class NavigationControl(BaseActionEngine):
    driver: BaseDriver
    time_between_actions: float
    logger: AgentLogger
    
    def __init__(self, 
                 driver: BaseDriver, 
                 time_between_actions: float = 1.5,
                 logger: AgentLogger = None) -> None:
        self.driver: BaseDriver = driver
        self.time_between_actions = time_between_actions
        self.logger = logger
    
    def execute_instruction(self, instruction: str):
        logger = self.logger
        # TODO: Not clean the fact that we have driver / meta_driver around. Should settle for better names
        meta_driver: BaseDriver = self.driver
        driver: WebDriver = meta_driver.get_driver()
        
        # if "SCROLL_DOWN" in instruction:
        #     code = """driver.execute_script("window.scrollBy(0, window.innerHeight);")"""
        # elif "SCROLL_UP" in instruction:
        #     code = """driver.execute_script("window.scrollBy(0, -window.innerHeight);")"""
        if "WAIT" in instruction:
            code = f"""
import time
time.sleep({self.time_between_actions})"""
        elif "BACK" in instruction:
            code = """driver.back()"""
        elif "SCAN" in instruction:
        # TODO: Should scan be in the navigation controls or in the driver?
            code = """meta_driver.get_screenshots_whole_page()"""
        else:
            raise ValueError(f"Unknown instruction: {instruction}")
        
        
        local_scope = {"driver": driver, "meta_driver": meta_driver}
        exec(code, local_scope, local_scope)
        success = True
        output = None
        
        if logger:
            log = {
                "engine": "Navigation Controls",
                "instruction": instruction,
                "engine_log": None,
                "success": success,
                "output": output,
                "code": code
            }
            logger.add_log(log)
        
        return success, output

