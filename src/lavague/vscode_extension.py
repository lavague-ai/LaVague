from IPython.core.magic import register_line_magic
import requests
from .action_engine import ActionEngine
from .cli.config import Config
from .prompts import DEFAULT_PROMPT
try:
    @register_line_magic
    def lavague_exec(line: str):
        global engine_vscode
        global driver

        if "engine" not in globals():
            config = Config.make_default_action_engine()
            engine_vscode = config.make_action_engine()
        html: str = driver.page_source
        code_full = ""
        for code in engine_vscode.get_action_streaming(line, html):
            try:
                code_full += code
                r = requests.post('http://127.0.0.1:8081/push', json={'data' : code})
            except:
                pass
        try:
            code_full = engine_vscode.cleaning_function(code_full)
            r = requests.post('http://127.0.0.1:8081/push', json={'full_code' : code_full, 'over' : True})
        except:
            pass
except:
    pass
