from abc import ABC, abstractmethod
import asyncio
import json
import threading
from typing import Callable
import uuid
from lavague.core.agents import WebAgent
from lavague.core.extractors import JsonFromMarkdownExtractor
from lavague.core.logger import AgentLogger
import types


class AgentSession(ABC):
    uid = str(uuid.uuid4())
    agent: WebAgent

    @abstractmethod
    async def send_message(self, message: str):
        pass

    @abstractmethod
    async def send_message_for_result(self, message: str, id: str) -> any:
        pass

    def handle_prompt_agent_action(self, type: str, args: str):
        if type == "run":
            self.agent.run(args)
        elif type == "get":
            self.agent.get(args)

    def handle_agent_message(self, json_message):
        if "type" in json_message:

            def exe_task():
                self.handle_prompt_agent_action(
                    json_message["type"], json_message["args"]
                )

            task = threading.Thread(target=exe_task)
            task.start()

    def send_command_and_get_response_sync(self, command, args=""):
        id = str(uuid.uuid4())
        event = threading.Event()
        response_data = {}

        data = {"command": command, "args": args, "id": id}

        message = json.dumps(data)

        def send_command():
            response = asyncio.run(self.send_message_for_result(message, id))
            response_data["response"] = response
            event.set()

        response_thread = threading.Thread(target=send_command)
        response_thread.start()

        # Wait for the response
        event.wait()

        ret = ""
        if "response" in response_data:
            try:
                jso = response_data["response"]
                ret = jso["ret"]
                response_data.clear()
            except Exception as e:
                print("Failed to get response data", e)
                pass
        return ret


class CommunicationChannel(ABC):
    sessions: list[AgentSession] = []
    agent_factory: Callable[[AgentSession], WebAgent] = None

    @abstractmethod
    def start(self):
        pass

    def stop(self):
        for session in self.sessions:
            session.stop()

    def add_session(self, session: AgentSession):
        session.agent = self.agent_factory(session)
        if session.agent is None:
            raise Exception("Agent factory must provide an Agent")
        self.setup_session_agent(session)
        self.sessions.append(session)

    def setup_session_agent(self, session: AgentSession):
        # override extractor for JSON format
        session.agent.action_engine.navigation_engine.extractor = (
            JsonFromMarkdownExtractor()
        )

        # override logger method
        add_log = session.agent.logger.add_log

        def send_log(self, message):
            add_log(message)
            message = {"type": "agent_log", "agent_log": message}
            asyncio.run(session.send_message(json.dumps(message)))

        session.agent.logger.add_log = types.MethodType(send_log, session.agent.logger)
