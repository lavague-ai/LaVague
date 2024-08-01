from abc import ABC, abstractmethod
import asyncio
import json
import threading
from typing import Callable, Dict
import uuid
from lavague.core.agents import WebAgent
from lavague.core.extractors import YamlFromMarkdownExtractor
from lavague.core.logger import AgentLogger
import types
import copy


class AgentSession(ABC):
    agent: WebAgent

    def __init__(self):
        self.uid = str(uuid.uuid4())
        self._stop_event: threading.Event = threading.Event()
        self._task: threading.Thread = None

    @abstractmethod
    async def send_message(self, message: str):
        pass

    @abstractmethod
    async def send_message_for_result(self, message: str, id: str) -> any:
        pass

    def handle_prompt_agent_action(self, type: str, args: str, id: str):
        if type == "run":
            start = {"type": "start"}
            interrupted = False
            asyncio.run(self.send_message(json.dumps(start)))
            try:
                self.agent.set_stop_signal(self._stop_event)
                self.agent.run(args)
            except Exception as e:
                pass
            finally:
                stop = {"type": "stop", "args": self.agent.interrupted}
                asyncio.run(self.send_message(json.dumps(stop)))
        elif type == "get":
            self.agent.get(args)

    def handle_agent_message(self, json_message):
        if "type" in json_message:

            def exe_task(id):
                self.handle_prompt_agent_action(
                    json_message["type"], json_message["args"], id
                )

            task_id = self.uid
            if json_message["type"] != "stop":
                self._stop_event.clear()
                self._task = threading.Thread(target=exe_task, args=(task_id,))
                self._task.start()
            else:
                stop_thread = threading.Thread(target=self.stop_task)
                stop_thread.start()

    def stop_task(self):
        if self._task and self._task.is_alive():
            self._stop_event.set()
            self._task.join(timeout=15)

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
                if "ret" in jso:
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
            YamlFromMarkdownExtractor()
        )

        # override logger method
        add_log = session.agent.logger.add_log

        def send_log(self, message):
            message_cp = copy.deepcopy(message)
            add_log(message_cp)
            if "screenshots" in message_cp:
                del message_cp["screenshots"]
            message_cp = {"type": "agent_log", "agent_log": message_cp}
            asyncio.run(session.send_message(json.dumps(message_cp)))

        session.agent.logger.add_log = types.MethodType(send_log, session.agent.logger)
