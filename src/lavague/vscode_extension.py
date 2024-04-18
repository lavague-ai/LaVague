from IPython.core.magic import register_line_magic
import requests
from .cli.config import Config
from .prompts import DEFAULT_PROMPT

try:

    @register_line_magic
    def lavague_exec(line: str):
        global engine_vscode
        global driver

        if "engine" not in globals():
            engine_vscode = Config.make_default_action_engine()
        html: str = driver.page_source
        code_full = ""
        try:
            r = requests.post("http://127.0.0.1:16500/push", data=engine_vscode.get_action_streaming(line, html), stream=True)
        except:
            pass
except:
    pass
