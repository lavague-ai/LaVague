from typing import Optional
import click
import warnings
import os

from lavague.evaluator import Evaluator, SeleniumActionEvaluator
from ..format_utils import extract_code_from_funct, extract_imports_from_lines


@click.group()
def cli():
    pass


@cli.command()
@click.pass_context
def launch(ctx):
    """Start a local gradio demo of lavague"""
    from .config import Config, Instructions
    from ..command_center import GradioDemo

    config = Config.from_path(ctx.obj["config"])
    if ctx.obj["instructions"] is not None:
        instructions = Instructions.from_yaml(ctx.obj["instructions"])
    else:
        instructions = Instructions.from_default()
    action_engine = config.make_action_engine()
    # We will just pass the get driver func name to the Gradio demo.
    # We will call this during driver initialization in init_driver() 
    get_driver = config.get_driver
    command_center = GradioDemo(action_engine, get_driver)
    command_center.run(instructions.url, instructions.instructions)


@cli.command()
@click.option(
    "--output-file",
    "-o",
    type=click.Path(exists=True),
    required=False,
    help="The path of the output file",
)

@click.pass_context
def build(ctx, output_file: Optional[str], test: bool = False):
    """Generate a python script that can run the successive actions in one go."""
    from tqdm import tqdm
    import os
    from .config import Config, Instructions
    from ..telemetry import send_telemetry
    from ..action_engine import TestActionEngine

    def build_name(config_path: str, instructions_path: str) -> str:
        instructions_path = os.path.basename(instructions_path)
        instructions_path, _ = os.path.splitext(instructions_path)

        config_path = os.path.basename(config_path)
        config_path, _ = os.path.splitext(config_path)

        output_path = (instructions_path + "_" if len(instructions_path) > 0 else "") + config_path + "_gen"
        base_path = str(output_path)
        output_path += ".py"
        i = 1
        while os.path.exists(output_path):
            output_path = base_path + str(i) + ".py"
            i += 1
        return output_path

    config: Config = Config.from_path(ctx.obj["config"])
    if ctx.obj["instructions"] is not None:
        instructions: Instructions = Instructions.from_yaml(ctx.obj["instructions"])
    else:
        instructions: Instructions = Instructions.from_default()
    abstractDriver = config.get_driver()
    if test:
        action_engine = TestActionEngine(abstractDriver.getDummyCode())
    else:
        action_engine = config.make_action_engine()
    abstractDriver.goTo(instructions.url)

    source_code_lines = extract_code_from_funct(config.get_driver)
    exec(extract_imports_from_lines(source_code_lines))

    # Prepare the file
    if output_file is None:
        output_file = build_name(ctx.obj["config"] if ctx.obj["config"] is not None else "output", ctx.obj["instructions"] if ctx.obj["instructions"] is not None else "")
    output = "\n".join(source_code_lines)
    output += f"\n{abstractDriver.goToUrlCode(instructions.url.strip())}\n"
    driver_name, driver = abstractDriver.getDriver()
    exec(f"{driver_name.strip()} = driver")  # define driver

    for instruction in tqdm(instructions.instructions):
        print(f"Processing instruction: {instruction}")
        html = abstractDriver.getHtml()
        code = action_engine.get_action(instruction, html)
        error = ""
        try:
            exec(code)
            success = True
        except Exception as e:
            print(f"Error in code execution: {code}")
            print("Error:", e)
            print(f"Saving output to {output_file}")
            error = repr(e)
            success = False
            with open(output_file, "w") as file:
                file.write(output)
                break
        finally:
            output += (
                "\n\n"
                + "#" * 80
                + "\n"
                + f"# Query: {instruction}\n# Code:\n{code}".strip()
            )
            source_nodes = action_engine.get_nodes(instruction, html)
            retrieved_context = "\n".join(source_nodes)
            send_telemetry(
                config.llm.metadata.model_name,
                code,
                "",
                html,
                instruction,
                instructions.url,
                "Lavague-build",
                success,
                test,
                error,
                retrieved_context
            )
    abstractDriver.destroy()
    print(f"Saving output to {output_file}")
    with open(output_file, "w") as file:
        file.write(output)


@cli.command()
@click.pass_context
def test(ctx):
    """Does a test run of LaVague build without actually querying model"""
    ctx.invoke(build, test=True)


@cli.command()
@click.option(
    "--dataset",
    "-d",
    required=True,
)

@click.option(
    "--nb-data",
    "-n",
    type=int,
    required=False,
    default=5,
)

@click.option(
    "--output-file",
    "-o",
    type=str,
    required=False,
)

@click.option(
    "--retriever",
    "-r",
    type=click.Path(exists=True),
    required=False,
)

@click.option(
    "--export-retriever",
    "-exr",
    type=str,
    required=False,
)

@click.pass_context
def evaluation(ctx, dataset: str, nb_data: int, output_file: str, export_retriever: str, retriever: str):
    """Run the whole evaluation pipeline"""
    import pandas as pd 

    retriever_data = None
    if retriever is not None:
        retriever_data = pd.read_json(retriever, orient='records', lines=True)
    
    if ctx.obj["config"] is not None and os.path.isdir(ctx.obj["config"]) == True:
        for file in os.listdir(ctx.obj["config"]):
            if file.endswith(".py"):
                print(f"Handling {file}...")
                try:
                    retriever_data = common_evaluation(ctx.obj["config"] + "/" + file, dataset, nb_data, output_file, export_retriever, retriever_data)
                except Exception as e:
                    print(f"An error occured while handling {file}: {repr(e)}")
    else:
        retriever_data = common_evaluation(ctx.obj["config"], dataset, nb_data, output_file, export_retriever, retriever_data)

    if export_retriever:
        print(f"Exporting retriever to {export_retriever}")
        retriever_data.to_json(export_retriever, orient='records', lines=True)

def common_evaluation(path, dataset: str, nb_data: int, output_file: str, export_retriever: str, retriever_data):
    from datasets import load_dataset 
    from .config import Config

    config: Config = Config.from_path(path)
    evaluator: Evaluator = config.make_evaluator()

    results, retriever_data = evaluator.evaluate(dataset, retriever_data, nb_data=nb_data)
    if output_file is None:
        normalized_path = os.path.normpath(path if path is not None else "./default_configuration")
        file_name = os.path.basename(normalized_path)
        file_name, _ = os.path.splitext(file_name)
        file_name += ".json"
    else:
        file_name = output_file
    print(f"Exporting data to {file_name}")
    results.to_json(file_name, orient='records', lines=True)
    return retriever_data

        
