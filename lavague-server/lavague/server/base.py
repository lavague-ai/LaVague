from typing import Callable
from lavague.core.agents import WebAgent
from lavague.server.websocket_channel import WebSocketHandler
from lavague.server.channel import CommunicationChannel


class AgentServer:
    def __init__(
        self,
        agent_factory: Callable[[], WebAgent],
        communication_channel: CommunicationChannel = None,
        port: int = 8000,
    ):
        if communication_channel is None:
            communication_channel = WebSocketHandler(port)
        self.communication_channel = communication_channel
        self.communication_channel.agent_factory = agent_factory

    def serve(self):
        try:
            self.communication_channel.start()
        except KeyboardInterrupt:
            print("The server was interrupted.")
            pass

    def close(self):
        self.communication_channel.close()
