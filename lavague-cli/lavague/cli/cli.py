from typing import List, Optional, Any
import click


class CliError(Exception):
    pass

def load_attr_from_module(attr_module_str: str) -> Any:
    import importlib

    module_str, _, attr_str = attr_module_str.partition(":")
    if not module_str or not attr_str:
        raise CliError(
            f"engine string {attr_module_str} must be in format <module>:<attribute>."
        )
    try:
        spec = importlib.util.spec_from_file_location(module_str, module_str + ".py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except ModuleNotFoundError as exc:
        if exc.name != module_str:
            raise exc from None
        raise CliError(f'Could not import module "{module_str}".')
    try:
        return getattr(module, attr_str)
    except AttributeError:
        raise CliError(
            f'Attribute "{attr_str}" not found in module "{module_str}".'
        )


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--url",
    default=None,
    help="The initial url that the inner driver will navigate to.",
)
@click.option(
    "--instruction",
    "-i",
    default=None,
    multiple=True,
    help="Instruction which will be used as default. You can define multiple.",
)
@click.option(
    "--engine",
    default=None,
    help="<module>:<attribute> Points to an ActionEngine object while will used in the gradio demo.",
)
def launch(url: Optional[str], engine: Optional[str], instruction: Optional[List[str]]):
    """Launch a local gradio demo of lavague."""
    from lavague.contexts.openai import OpenaiContext
    from lavague.gradio import GradioDemo
    from lavague.core import ActionEngine
    from lavague.drivers.selenium import SeleniumDriver

    instruction = list(instruction)

    if engine is None:
        action_engine = ActionEngine.from_context(
            SeleniumDriver(url), OpenaiContext.from_defaults()
        )
    else:
        action_engine = load_attr_from_module(engine)
        if url is not None:
            action_engine.driver.goto(url)
    
    if action_engine.driver.get_url() is None and len(instruction) == 0:
        action_engine.driver.goto("https://news.ycombinator.com/")
        instruction = ["Click on search bar, then type 'lavague', then click enter"]

    gradio_demo = GradioDemo(action_engine, instruction)
    gradio_demo.launch()


# TODO
@cli.command()
def eval():
    pass