from lavague.trajectory import Trajectory
from lavague.action import Action
from typing import Optional, Callable, Self


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
            f"Action {action.action} translator is missing, please add a '{method_name}' method in {self.__class__.__name__} or attach it with {self.__class__.__name__}.add_action_translator('{action.action_type}', '{action.action}', my_translator_function)"
        )

    def translate_action(self, action: Action) -> Optional[str]:
        """Translate a single action to target framework code"""
        method_name = f"translate_{action.action_type}_{action.action}"

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

    def export_to_file(self, trajectory: Trajectory, file_path: str):
        exported = self.export(trajectory)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(exported)

    @classmethod
    def add_action_translator(
        cls,
        action_type: str,
        action: str,
        translator: Callable[[Self, Action], Optional[str]],
    ) -> None:
        """Add a new action translator to the exporter"""
        setattr(cls, f"translate_{action_type}_{action}", translator)
