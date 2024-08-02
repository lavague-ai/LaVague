import click
import os
from lavague.qa.generator import TestGenerator
from lavague.tests.cli import _load_context


@click.command()
@click.option(
    "--url",
    "-u",
    type=str,
    default="https://en.wikipedia.org/",
    required=False,
    help="URL of the site to test",
)
@click.option(
    "--feature",
    "-f",
    default=os.getcwd() + "/demo_wikipedia.feature",
    type=str,
    required=False,
    help="Path to the .feature file containing Gherkin",
)
@click.option(
    "--full-llm",
    "-llm",
    is_flag=True,
    required=False,
    help="Enable full LLM pytest generation",
)
@click.option(
    "--context",
    "-c",
    type=str,
    default=None,
    required=False,
    help="Path of python file containing an initialized context and token_counter. Defaults to OpenAI GPT4o",
)
@click.option(
    "--headless",
    "-h",
    is_flag=True,
    required=False,
    help="Enable headless mode for the browser",
)
@click.option(
    "--log-to-db",
    "-db",
    is_flag=True,
    required=False,
    help="Enables logging to a SQLite database",
)
def cli(
    url: str,
    feature: str,
    full_llm: bool,
    context: str,
    headless: bool,
    log_to_db: bool,
) -> None:
    context, token_counter = _load_context(context)
    pytest_generator = TestGenerator(
        context, url, feature, full_llm, token_counter, headless, log_to_db
    )
    pytest_generator.generate()
