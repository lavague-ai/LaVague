
from .telemetry import send_telemetry
from .utils import load_action_engine, load_instructions
from .command_center import CommandCenter

import os
import argparse
import importlib.util
from pathlib import Path
from tqdm import tqdm
import inspect

import warnings
import asyncio
# We need nest_asyncio to use asyncio.run inside exec function
import nest_asyncio
nest_asyncio.apply()

warnings.filterwarnings("ignore")


def import_from_path(path):
    # Convert the path to a Python module path
    module_name = Path(path).stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def convert_to_executable_code(func_code):
    # Indent the provided code properly
    indented_code = '\n'.join(['    ' + line for line in func_code.strip().split('\n')])

    # Define a wrapper function and place the provided code inside it
    wrapper_code = f'''
import asyncio
async def wrapper_func():
{indented_code}
asyncio.run(wrapper_func())
    '''
    return wrapper_code


def build():
    parser = argparse.ArgumentParser(description='Process a file.')

    # Add the arguments
    parser.add_argument('--file_path',
                    type=str,
                    required=True,
                    help='the path to the file')

    parser.add_argument('--config_path',
                    type=str,
                    required=True,
                    help='the path to the Python config file')
    # Execute the parse_args() method
    args = parser.parse_args()
    
    file_path = args.file_path
    config_path = args.config_path
    
    # Load the action engine and driver from config file
    action_engine, get_driver = load_action_engine(config_path, streaming=False)
    
    driver = get_driver()
    
    # Gets the original source code of the get_driver method
    source_code = inspect.getsource(get_driver)

    # Split the source code into lines and remove the first line (method definition)
    source_code_lines = source_code.splitlines()[1:]
    source_code_lines = [line.strip() for line in source_code_lines[:-1]]
    
    # Execute the import lines
    import_lines = [line for line in source_code_lines if line.startswith("from") or line.startswith("import")] 
    exec("\n".join(import_lines))

    output = "\n".join(source_code_lines)
    
    base_url, instructions = load_instructions(file_path)

    driver.get(base_url)
    output += f"\ndriver.get('{base_url.strip()}')\n"

    template_code = """\n########################################\n# Query: {instruction}\n# Code:\n{code}"""

    file_path = os.path.basename(file_path)
    file_path, _ = os.path.splitext(file_path)
    
    config_path = os.path.basename(config_path)
    config_path, _ = os.path.splitext(config_path)
    
    output_fn = file_path + "_" + config_path + ".py"
    
    for instruction in tqdm(instructions):
        print(f"Processing instruction: {instruction}")
        html = driver.page_source
        code, source_nodes = action_engine.get_action(instruction, html)
        try:
            exec(code)
        except Exception as e:
            print(f"Error in code execution: {code}")
            print("Error:", e)
            print(f"Saving output to {output_fn}")
            with open(output_fn, "w") as file:
                file.write(output)
                break
        output += "\n" + template_code.format(instruction=instruction, code=code).strip()
        send_telemetry(action_engine.llm.metadata.model_name, code, b"", html, source_nodes, instruction, base_url, "Lavague-build")  

    print(f"Saving output to {output_fn}")
    with open(output_fn, "w") as file:
        file.write(output)
            
def launch():
    parser = argparse.ArgumentParser(description='Process a file.')

    # Add the arguments
    parser.add_argument('--file_path',
                    type=str,
                    required=True,
                    help='the path to the file')

    parser.add_argument('--config_path',
                    type=str,
                    required=True,
                    help='the path to the Python config file')
    # Execute the parse_args() method
    args = parser.parse_args()
    
    file_path = args.file_path
    config_path = args.config_path
    
    # Load the action engine and driver setup function from config file
    action_engine, get_driver = load_action_engine(config_path, streaming=True)
    
    # Initialize the driver
    driver = get_driver()
    
    command_center = CommandCenter(action_engine, driver)

    base_url, instructions = load_instructions(file_path)
        
    command_center.run(base_url, instructions)

def build_playwright():
    async def _build_playwright():
        parser = argparse.ArgumentParser(description='Process a file.')

        # Add the arguments
        parser.add_argument('--file_path',
                        type=str,
                        required=True,
                        help='the path to the file')

        parser.add_argument('--config_path',
                        type=str,
                        required=True,
                        help='the path to the Python config file')
        # Execute the parse_args() method
        args = parser.parse_args()
        
        file_path = args.file_path
        config_path = args.config_path
        
        # Load the action engine and driver from config file
        action_engine, get_driver = load_action_engine(config_path, streaming=False, use_playwright=True)
        
        driver = await get_driver()
        
        # Gets the original source code of the get_driver method
        source_code = inspect.getsource(get_driver)

        # Split the source code into lines and remove the first line (method definition)
        source_code_lines = source_code.splitlines()[1:]
        source_code_lines = [line.strip() for line in source_code_lines[:-1]]
        
        # Execute the import lines
        import_lines = [line for line in source_code_lines if line.startswith("from") or line.startswith("import")] 
        exec(convert_to_executable_code("\n".join(import_lines)))

        output = "\n".join(source_code_lines)
        
        base_url, instructions = load_instructions(file_path)

        await driver.goto(base_url)
        output += f"\nawait page.goto('{base_url.strip()}')\n"

        template_code = """\n########################################\n# Query: {instruction}\n# Code:\n{code}"""

        file_path = os.path.basename(file_path)
        file_path, _ = os.path.splitext(file_path)
        
        config_path = os.path.basename(config_path)
        config_path, _ = os.path.splitext(config_path)
        
        output_fn = file_path + "_" + config_path + ".py"
        full_exec_code = ""
        
        for instruction in tqdm(instructions):
            print(f"Processing instruction: {instruction}")
            html = await driver.content()
            code, source_nodes = action_engine.get_action(instruction, html)
            try:
                full_code = output + '\n' + code
                full_exec_code = convert_to_executable_code(full_code)
                print(f"Executing code:\n {full_exec_code}")
                exec(full_exec_code)
            except Exception as e:
                print(f"Error in code execution: {code}")
                print("Error:", e)
                print(f"Saving output to {output_fn}")
                with open(output_fn, "w") as file:
                    file.write(output)
                    break
            output += "\n" + template_code.format(instruction=instruction, code=code).strip()
            send_telemetry(action_engine.llm.metadata.model_name, code, b"", html, source_nodes, instruction, base_url, "Lavague-build")  

        print(f"Saving output to {output_fn}")
        with open(output_fn, "w") as file:
            file.write(full_exec_code)
    
    asyncio.run(_build_playwright())