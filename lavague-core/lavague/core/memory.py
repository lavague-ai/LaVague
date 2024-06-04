"""TODO: Make this class generalizable"""

from lavague.core.logger import AgentLogger, Loggable


class ShortTermMemory(Loggable):
    """
    Short term memory module of the agent.
    """

    def __init__(self, user_data=None, logger: AgentLogger = None) -> None:
        current_state = {
            "external_observations": {
                "vision": "[SCREENSHOT]",
            },
            "internal_state": {
                "user_inputs": [],
                "agent_outputs": [],
            },
        }
        self.logger = logger

        if user_data:
            current_state["internal_state"]["user_inputs"].append(user_data)

        self.current_state = current_state

        self.previous_instructions: str = "[NONE]"
        self.last_engine: str = "[NONE]"

    def set_user_data(self, user_data=None):
        if user_data:
            self.current_state["internal_state"]["user_inputs"].append(user_data)

    def get_state(self):
        current_state = self.current_state
        past = {
            "previous_instructions": str(self.previous_instructions),
            "last_engine": self.last_engine,
        }

        logger = self.logger

        if logger:
            log = {
                "current_state": current_state,
                "past": past,
            }
            logger.add_log(log)
        return current_state, past

    def update_state(self, instruction, last_engine, success, output):
        if not success:
            instruction = "[FAILED] " + instruction

        if output:
            self.current_state["internal_state"]["agent_outputs"].append(output)

        if self.previous_instructions == "[NONE]":
            self.previous_instructions = f"""
- {instruction}"""
        else:
            self.previous_instructions += f"""
- {instruction}"""
        self.last_engine = last_engine
