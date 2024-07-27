import click
import os
from pathlib import Path
from typing import List
from lavague.tests.config import TestConfig
from lavague.tests.runner import TestRunner


@click.command()
@click.option(
    "--context",
    "-c",
    type=str,
    default=os.getcwd() + "/lavague-tests/contexts/default_context.py",
    required=False,
    help="python file containing an initialized context and token_counter. Default is context/default_context.py",
)
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
@click.option(
    "--log-to-db",
    "-db",
    is_flag=True,
    help="if set, enables logging to the default SQLite database",
)
def cli(
    context: str, directory: str, site: List[str], display: bool, log_to_db: bool
) -> None:
    context, token_counter = _load_context(context)
    sites_to_test = _load_sites(directory, site)

    # add methods, extract site loading as well.
    runner = TestRunner(
        context=context,
        sites=sites_to_test,
        token_counter=token_counter,
        headless=not display,
        log_to_db=log_to_db,
    )
    res = runner.run()
    print(str(res))
    exit(0 if res.is_success() else -1)


def _load_sites(directory, site):
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
    return sites_to_test


def _load_context(context):
    # read context file and execute it
    with open(context, "r") as file:
        file_content = file.read()
    local_namespace = {}
    exec(file_content, {}, local_namespace)

    # ensure variables are defined
    if "context" in local_namespace and "token_counter" in local_namespace:
        return local_namespace["context"], local_namespace["token_counter"]
    else:
        raise Exception(
            "Expected variables (`context` and `token_counter`) not found in the provided context file"
        )


if __name__ == "__main__":
    cli()
