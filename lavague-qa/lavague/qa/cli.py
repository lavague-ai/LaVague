import click
import os
from lavague.qa.generator import TestGenerator


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
    default="./features/demo_wikipedia.feature",
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
    url: str, feature: str, full_llm: bool, headless: bool, log_to_db: bool
) -> None:
    pytest_generator = TestGenerator(url, feature, full_llm, headless, log_to_db)
    pytest_generator.generate()
