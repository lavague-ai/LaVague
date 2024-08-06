from abc import ABC, abstractmethod
import asyncio
import json
import threading
from typing import Callable
import uuid
from lavague.core.agents import WebAgent
from lavague.core.extractors import YamlFromMarkdownExtractor
import types
import copy


class AgentSession(ABC):
    agent: WebAgent

    def __init__(self):
        self.uid = str(uuid.uuid4())
        self._task: threading.Thread = None

    @abstractmethod
    async def send_message(self, message: str):
        pass

    @abstractmethod
    async def send_message_for_result(self, message: str, id: str) -> any:
        pass

    def exe_start_stop(self, run: Callable):
        asyncio.run(self.send_message(json.dumps({"type": "start"})))
        try:
            run()
        except Exception:
            pass
        finally:
            try:
                asyncio.run(
                    self.send_message(
                        json.dumps({"type": "stop", "args": self.agent.interrupted})
                    )
                )
            except:
                print("The stop signal could not be sent")

    def handle_prompt_agent_action(self, type: str, args: str, id: str):
        if type == "run":
            self.exe_start_stop(lambda: self.agent.run(args))

        elif type == "run_step":
            self.exe_start_stop(lambda: self.agent.run_step(args))

        elif type == "get":
            self.agent.get(args)

        elif type == "prepare_run":
            self.agent.prepare_run()

        elif type == "navigate":
            self.exe_start_stop(
                lambda: self.agent.action_engine.navigation_engine.execute_instruction(
                    args
                )
            )

        elif type == "nav_action":
            self.exe_start_stop(
                lambda: self.agent.action_engine.navigation_engine.execute_action(args)
            )

    def handle_agent_message(self, json_message):
        if "type" in json_message:

            def exe_task(id):
                self.handle_prompt_agent_action(
                    json_message["type"], json_message["args"], id
                )

            task_id = self.uid
            self._task = threading.Thread(target=exe_task, args=(task_id,))
            self._task.start()

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
