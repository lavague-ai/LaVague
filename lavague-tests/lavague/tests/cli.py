import click
import os
from pathlib import Path
from typing import List
from .config import TestConfig
from .runner import TestRunner


@click.command()
@click.option(
    "--directory",
    "-d",
    default=os.getcwd() + "/lavague-tests/sites",
    type=str,
    required=False,
    help="sites directory",
)
@click.option(
    "--site",
    "-s",
    type=str,
    required=False,
    multiple=True,
    help="site name",
)
@click.option(
    "--display",
    is_flag=True,
    help="if set browser will be displayed",
)
def cli(directory: str, site: List[str], display: bool) -> None:
    sites_to_test: List[Path] = []
    try:
        for item in os.listdir(directory):
            if (len(site) == 0 or item in site) and os.path.isfile(
                os.path.join(directory, item, "config.yml")
            ):
                try:
                    config = TestConfig(os.path.join(directory, item))
                    sites_to_test.append(config)
                except Exception as e:
                    click.echo(f"Invalid site config '{item}': {e}")
                    raise e
    except FileNotFoundError:
        click.echo(f"Directory '{directory}' not found.")

    runner = TestRunner(sites=sites_to_test, headless=not display)
    res = runner.run()
    print(str(res))
    exit(0 if res.is_success() else -1)


if __name__ == "__main__":
    cli()
