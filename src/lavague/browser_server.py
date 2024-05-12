# server.py
from typing import Callable, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import func
import uvicorn
import base64 
from lavague.driver import AbstractDriver
from lavague.format_utils import extract_code_from_funct, extract_imports_from_lines

class Request(BaseModel):
    code: Optional[str] = None

driver_global: AbstractDriver = None
get_driver: Callable[[], AbstractDriver]

# fastapi set-up
app = FastAPI()

@app.get("/screenshot")
def scr():
    global driver_global
    if driver_global is None:
        driver_global = get_driver()
    driver_global.getScreenshot("screenshot.png")
    f = open("screenshot.png", "rb")
    scr = base64.b64encode(f.read())
    return scr.decode("ascii")

@app.post("/exec_code")
def exec_code(req: Request):
    global driver_global
    if driver_global is None:
        driver_global = get_driver()
    success = False
    error = ""
    driver_name, driver = driver_global.getDriver()  # define driver for exec
    exec(f"{driver_name.strip()} = driver")  # define driver in case its name is different
    source_code_lines = extract_code_from_funct(get_driver)
    import_lines = extract_imports_from_lines(source_code_lines)
    code_to_exec = f"""
{import_lines} 
{req.code}
"""
    try:
        exec(code_to_exec)
        success = True
    except Exception as e:
        error = repr(e)
        success = False
    return {"success": success, "error": error}


@app.get("/get_url")
def geturl():
    global driver_global
    if driver_global is None:
        driver_global = get_driver()
    url = driver_global.getUrl()
    return url

@app.get("/get_html")
def gethtml():
    global driver_global
    if driver_global is None:
        driver_global = get_driver()
    html = driver_global.getHtml()
    return {"html": html}

@app.get("/go_to")
def goto(url: str):
    global driver_global
    if driver_global is None:
        driver_global = get_driver()
    if url != driver_global.getUrl():
        driver_global.goTo(url)
    return ""

@app.get("/destroy")
def destroy():
    global driver_global
    if driver_global is not None:
        driver_global.destroy()
    return ""

@app.get("/")
def default():
    return ""

def run_server(driver_func: Callable[[], AbstractDriver] = None, debug: bool = False):
    global get_driver
    if driver_func is not None:
        get_driver = driver_func
    uvicorn.run(app, host="127.0.0.1", port=16500, log_level="debug", workers=1, limit_concurrency=3)