from abc import ABC, abstractmethod


class ActionBuilder(ABC):
    @abstractmethod
    def get_action(self, query: str) -> str:
        pass


class ActionBuilderStore:
    def __init__(self, *args: ActionBuilder):
        self.tools: dict[str, ActionBuilder] = {
            (type(tool).__name__, tool) for tool in args
        }

    def get_action(self, action: str, query: str) -> str:
        action_builder = self.tools.get(action)
        if action_builder is None:
            raise ValueError(f"No such ActionBuilder: {action}")
        return action_builder.get_action(query)
