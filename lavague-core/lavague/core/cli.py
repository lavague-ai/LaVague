import click
from lavague.core.agent import WebAgent
from lavague.core.action import DEFAULT_PARSER
import sys


def run(url: str, objective: str, store_images: bool = False):
    DEFAULT_PARSER.store_images = store_images
    agent = WebAgent()
    trajectory = agent.run(url, objective)
    for action in trajectory.actions:
        print(type(action), action)
        print("**********")


@click.command()
@click.argument("url", required=True)
@click.argument("objective", required=True)
@click.option("--store-images", is_flag=True)
def cli_run(url: str, objective: str, store_images: bool = False):
    run(url=url, objective=objective, store_images=store_images)


if __name__ == "__main__":
    url = sys.argv[1]
    objective = sys.argv[2]
    store_images = "--store-images" in sys.argv
    run(url=url, objective=objective, store_images=store_images)
