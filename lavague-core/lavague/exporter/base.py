from lavague.trajectory import Trajectory
from lavague.action import Action, ActionTranslator
from typing import Optional, Self, Protocol, TypeVar, Callable
import copy


class ActionWrapper(Protocol):
    def __call__(self, action: Action, code: str) -> str: ...


class TrajectoryExporter:
    def generate_setup(self, trajectory: Trajectory) -> Optional[str]:
        """Generate setup code (imports, configurations, etc.)"""
        return None

    def generate_teardown(self, trajectory: Trajectory) -> Optional[str]:
        """Generate teardown code (cleanup, final assertions, etc.)"""
        return None

    def on_missing_action(self, action: Action, method_name: str) -> None:
        """Generate code for missing action"""
        raise NotImplementedError(
            f"Action {action.action} translator is missing, please add a '{method_name}' method in {self.__class__.__name__} or attach it with {self.__class__.__name__}.add_action_translator('{action.engine}_{action.action}', my_translator_function)"
        )

    def translate_action(self, action: Action) -> Optional[str]:
        """Translate a single action to target framework code"""
        method_name = f"translate_{action.engine}_{action.action}"

        if hasattr(self, method_name):
            return getattr(self, method_name)(action)

        self.on_missing_action(action, method_name)

    def merge_code(self, *codes: str | None) -> str:
        """Combine multiple strings into a single string"""
        return "".join(list(map(lambda x: x or "", codes)))

    def export(self, trajectory: Trajectory) -> str:
        setup = self.generate_setup(trajectory)
        teardown = self.generate_teardown(trajectory)
        actions = [self.translate_action(action) for action in trajectory.actions]
        return self.merge_code(setup, *actions, teardown)

    def __call__(self, trajectory: Trajectory) -> str:
        return self.export(trajectory)

    def export_to_file(self, trajectory: Trajectory, file_path: str):
        exported = self.export(trajectory)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(exported)

    def with_wrapper(self, wrapper: ActionWrapper, clone=True) -> Self:
        instance = copy.copy(self) if clone else self
        instance.translate_action = lambda action: wrap_action_translator(
            self.translate_action, wrapper
        )(action)
        return instance

    @classmethod
    def add_action_translator(
        cls, name: str, translator: Callable[[Self, Action], Optional[str]]
    ) -> None:
        """Add a new action translator to the exporter"""
        setattr(cls, f"translate_{name}", translator)

    @classmethod
    def from_translator(
        cls, action_translator: ActionTranslator
    ) -> "TrajectoryExporter":
        class DynamicExporter(cls):
            def translate_action(self, action: Action) -> Optional[str]:
                return action_translator(action)

        return DynamicExporter()

    @classmethod
    def from_method(cls, method_name: str) -> "TrajectoryExporter":
        return cls.from_translator(method_action_translator(method_name))


def translate_action(action: Action, method_name: str) -> Optional[str]:
    return getattr(action, method_name)() if hasattr(action, method_name) else None


def method_action_translator(name: str) -> ActionTranslator[Action]:
    def wrapper(action: Action) -> Optional[str]:
        return translate_action(action, name)

    return wrapper


T = TypeVar("T", bound=Action)


def wrap_action_translator(
    action_translator: ActionTranslator[T],
    wrapper: ActionWrapper,
) -> ActionTranslator[T]:
    def wrapped(action: T) -> Optional[str]:
        code = action_translator(action)
        return wrapper(action, code) if code else None

    return wrapped
