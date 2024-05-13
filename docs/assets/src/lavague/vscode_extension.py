from typing import Optional
from IPython.core.magic import register_line_magic
import requests
from .cli.config import Config

try:
    @register_line_magic
    def lavague_exec(line: str):
        global engine_vscode
        global driver

        if "engine" not in globals():
            engine_vscode = Config.make_default_action_engine()
        html: str = driver.page_source
        try:
            r = requests.post(
                "http://127.0.0.1:16500/push",
                data=engine_vscode.get_action_streaming_vscode(line, html, driver.current_url),
                stream=True,
            )
        except Exception as e:
            pass
except:
    pass

try:
    @register_line_magic
    def lavague_export(line: Optional[str] = None):
        try:
            r = requests.post("http://127.0.0.1:16500/export")
        except:
            pass
except:
    pass