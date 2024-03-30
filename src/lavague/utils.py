from .action_engine import ActionEngine, extract_first_python_code
from .defaults import default_get_driver, DefaultEmbedder, DefaultLLM, get_playwright_driver
from .prompts import DEFAULT_PROMPT, DEFAULT_PLAYWRIGHT_PROMPT

import importlib.util
from pathlib import Path

def import_from_path(path):
    # Convert the path to a Python module path
    module_name = Path(path).stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_action_engine(path, streaming, use_playwright=False):

    config_module = import_from_path(path)
    get_driver = getattr(config_module, "get_driver", default_get_driver)
    prompt_template= getattr(config_module, "prompt_template", DEFAULT_PROMPT)
    llm = getattr(config_module, "LLM", DefaultLLM)()
    embedder = getattr(config_module, "Embedder", DefaultEmbedder)()
    
    if use_playwright:
        get_driver = getattr(config_module, "get_driver", get_playwright_driver)
        prompt_template = getattr(config_module, "prompt_template", DEFAULT_PLAYWRIGHT_PROMPT)
    cleaning_function = getattr(config_module, "cleaning_function", extract_first_python_code)

    action_engine = ActionEngine(llm, embedder, prompt_template, cleaning_function, streaming=streaming)
    
    return action_engine, get_driver

def load_instructions(path):
    with open(path, "r") as file:
        instructions = file.readlines()
        
        base_url = instructions[0].strip()
        instructions = [instruction.strip() for instruction in instructions[1:]]
        
    return base_url, instructions

def add_indentation_to_code(code_to_indent: str, indentation_level=1):
    '''
    Adds indentation to the provided code so that it can be executed using exec
    code_to_indent: str: The code that needs to be indented
    indentation_level: int: The number of indentation levels to start with

    Note: This function can only support at max 1 line of try and except block, as it resets the indentation level after that

    Example:
    code_to_indent =
try:
from playwright.async_api import async_playwright
except (ImportError, ModuleNotFoundError) as error:
raise ImportError("Please install playwright using `pip install pytest-playwright` and then `playwright install` to install the necessary browser drivers") from error
p = await async_playwright().__aenter__()
browser = await p.chromium.launch()
page = await browser.new_page()
return page

will be converted to:

    try:
        from playwright.async_api import async_playwright
    except (ImportError, ModuleNotFoundError) as error:
        raise ImportError("Please install playwright using `pip install pytest-playwright` and then `playwright install` to install the necessary browser drivers") from error 
    p = await async_playwright().__aenter__()
    browser = await p.chromium.launch()
    page = await browser.new_page()
    return page

    '''
    lines = code_to_indent.split('\n')
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line]

    fixed_lines = []
    current_indentation_level = indentation_level
    for line in lines:
        if line.endswith(':'):
            current_indentation_level = indentation_level
            fixed_lines.append('    ' * current_indentation_level + line)
            current_indentation_level += 1
        else:
            fixed_lines.append('    ' * current_indentation_level + line)
            # Reset the indentation level after one line
            current_indentation_level = indentation_level

    fixed_code = '\n'.join(fixed_lines)

    return fixed_code

def wrap_code_in_async_function(original_code: str):
    '''
    Wraps the provided code in an async function and executes it using asyncio.run
    original_code: str:
    from playwright.async_api import async_playwright
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless = False)
    page = await browser.new_page()
    await page.goto("http://whatsmyuseragent.org/")

    This will convert the code above into a code like this, so that it can be executed using exec
    import asyncio
    async def wrapper_func():
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless = False)
        page = await browser.new_page()
        await page.goto("http://whatsmyuseragent.org/")
    asyncio.run(wrapper_func())
    '''
    # Indent the provided code properly
    indented_code = add_indentation_to_code(original_code)
    print("indented_code --> ", indented_code)

    # Define a wrapper function and place the provided code inside it
    wrapper_code = f'''
import asyncio
async def wrapper_func():
{indented_code}
asyncio.run(wrapper_func())
    '''
    return wrapper_code