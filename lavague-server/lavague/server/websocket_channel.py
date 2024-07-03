import asyncio
import websockets
from websockets.exceptions import ConnectionClosed
from .channel import AgentSession, CommunicationChannel
import json


class WebSocketSession(AgentSession):
    responses: dict[str, any] = {}

    def __init__(self, websocket):
        self.websocket = websocket

    async def start(self):
        await self.read_messages()

    def stop(self):
        if self.websocket:
            asyncio.create_task(self.websocket.close())
            self.websocket = None

    async def read_messages(self):
        try:
            async for message in self.websocket:
                self.handle_message(message)
        except ConnectionClosed:
            print("Client disconnected")
        finally:
            self.stop()

    def handle_message(self, message):
        if message == "PING":
            asyncio.create_task(self.send_message("PONG"))
            return
        try:
            json_message = json.loads(message)
            self.hande_json_message(json_message)
        except json.JSONDecodeError:
            print(f"Unhandled message {message}")
            pass
        self.client_response = message

    def hande_json_message(self, json_message):
        if "id" in json_message:
            self.responses[json_message["id"]] = json_message
        self.handle_agent_message(json_message)

    async def send_message_for_result(self, message: str, id: str):
        await self.send_message(message)
        return await self.wait_for_result(id)

    async def wait_for_result(self, id: str) -> any:
        while id not in self.responses:
            await asyncio.sleep(0.1)
        return self.responses.pop(id, None)

    async def send_message(self, message: str):
        if self.websocket is None:
            raise Exception(f"WebSocket connection is closed for {self.uid}")
        await self.websocket.send(message)


class WebSocketHandler(CommunicationChannel):
    def __init__(self, port: int = 8000):
        self.port = port

    def start(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.server = websockets.serve(
            self.handler, "0.0.0.0", self.port, max_size=20 * 1024 * 1024
        )
        asyncio.get_event_loop().run_until_complete(self.server)
        print(f"WebSocket server listening on port {self.port}")
        asyncio.get_event_loop().run_forever()

    def stop(self):
        super(CommunicationChannel, self).stop()
        if self.server and self.server.ws_server:
            self.server.ws_server.close()

    async def handler(self, websocket, path):
        session = WebSocketSession(websocket)
        self.add_session(session)
        print(f"Start session {session.uid}")
        await session.start()
        print(f"Stop session {session.uid}")
        self.sessions.remove(session)
