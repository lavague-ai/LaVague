from typing import Callable
from lavague.core.agents import WebAgent
from .websocket_channel import WebSocketHandler
from .channel import CommunicationChannel


class AgentServer:
    def __init__(
        self,
        agent_factory: Callable[[], WebAgent],
        communication_channel: CommunicationChannel = None,
    ):
        if communication_channel is None:
            communication_channel = WebSocketHandler()
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
