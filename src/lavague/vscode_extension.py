from IPython.core.magic import register_line_magic
import requests
from .action_engine import ActionEngine
from .cli.config import Config
from .prompts import DEFAULT_PROMPT
try:
    @register_line_magic
    def lavague_exec(line: str):
        global engine
        global driver
        
        if 'engine' not in globals():
            engine = Config.make_default_action_engine()
        html: str = driver.page_source
        code: str = engine.get_action(line, html)
        print(type(line))
        try:
            r = requests.post('http://127.0.0.1:8081/push', json={'data' : code})
        except:
            pass
except:
    pass