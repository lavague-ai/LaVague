import click
from lavague.server import AgentSession

def create_agent(session: AgentSession):
    from lavague.core import WorldModel, ActionEngine
    from lavague.core.agents import WebAgent
    from lavague.drivers.driverserver import DriverServer

    world_model = WorldModel()
    driver = DriverServer(session)
    action_engine = ActionEngine(driver)
    return WebAgent(world_model, action_engine)

@click.command()
@click.option(
    "--port",
    "-p",
    type=int,
    required=False,
    default=8000,
    help="Server port",
)
def cli(port: int) -> None:
    from lavague.server import AgentServer
    server = AgentServer(create_agent, port=port)
    server.serve()

if __name__ == "__main__":
    cli()
