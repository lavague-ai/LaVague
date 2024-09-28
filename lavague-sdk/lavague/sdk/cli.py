import click
from lavague.sdk import WebAgent
import sys
from typing import Optional


def run(url: str, objective: str, file: Optional[str] = None):
    agent = WebAgent()
    trajectory = agent.run(url, objective)
    if file:
        trajectory.write_to_file(file)
    else:
        print(trajectory.model_dump_json(indent=2))


@click.command()
@click.argument("url", required=True)
@click.argument("objective", required=True)
@click.option("--file", "-f", required=False)
def cli_run(url: str, objective: str, file: Optional[str]):
    run(url, objective, file)


if __name__ == "__main__":
    url = sys.argv[1]
    objective = sys.argv[2]
    run(url, objective)
