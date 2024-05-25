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
        
        driver: WebDriver = self.driver.get_driver()
        
        if "SCROLL_DOWN" in instruction:
            code = """driver.execute_script("window.scrollBy(0, window.innerHeight);")"""
        elif "SCROLL_UP" in instruction:
            code = """driver.execute_script("window.scrollBy(0, -window.innerHeight);")"""
        elif "WAIT" in instruction:
            code = f"time.sleep({self.time_between_actions})"
        else:
            raise ValueError(f"Unknown instruction: {instruction}")
        
        local_scope = {"driver": driver}
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

