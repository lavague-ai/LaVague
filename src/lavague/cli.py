from typing import Tuple, List
from pydantic import BaseModel
import click
import yaml

class Instructions(BaseModel):
    url: str
    instructions: List[str]


def load_imports():
    """These imports are expensive, so we do them after the arguments parsing, so that the cli is smooth"""
    from .telemetry import send_telemetry
    from .utils import load_action_engine, load_instructions
    from .command_center import GradioDemo

def load_instructions(path) -> Instructions:
    with open(path, "r") as file:
        config = yaml.safe_load(file)
    return Instructions(**config)

@click.group()

@click.option(
    "--instructions",
    "-i",
    type=click.Path(exists=True),
    required=True,
)

@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    required=True,
)

@click.pass_context
def main(ctx, instructions, config):
    """Copilot for devs to automate automation"""
    ctx.ensure_object(dict)
    ctx.obj["instructions"] = load_instructions(instructions)
    ctx.obj["config"] = config
    load_imports()

@main.command()
@click.pass_context
def build(ctx):
    """Generate a python script that can run the successive actions in one go."""
    pass

@main.command()
@click.pass_context
def launch(ctx):
    """Launch a gradio demo of lavague"""
    pass

if __name__ == '__main__':
    main(obj={})