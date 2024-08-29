from lavague.drivers.driverserver import DriverServer
from lavague.server import AgentServer, AgentSession

from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent


def create_agent(session: AgentSession):
    world_model = WorldModel()
    driver = DriverServer(session)
    action_engine = ActionEngine(driver)
    return WebAgent(world_model, action_engine)

server = AgentServer(create_agent)
server.serve()