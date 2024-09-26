from lavague.trajectory import Trajectory
from lavague.action import Action, ActionType
from lavague.action.navigation import (
    NavigationCommand,
    NavigationOutput,
    WebNavigationAction,
)
from lavague.action.extraction import ExtractionOutput, WebExtractionAction
from typing import Optional, cast


class TrajectoryExporter:
    def generate_setup(self, trajectory: Trajectory) -> Optional[str]:
        """Generate setup code (imports, configurations, etc.)"""
        return None

    def generate_teardown(self, trajectory: Trajectory) -> Optional[str]:
        """Generate teardown code (cleanup, final assertions, etc.)"""
        return None

    def on_missing_action(self, action: Action) -> None:
        """Generate code for missing action"""
        raise NotImplementedError(
            f"Action tpye {action.action_type} has unhandled output {action.action_output}"
        )

    def translate_action(self, action: Action) -> Optional[str]:
        """Translate a single action to target framework code"""
        instruction = action.instruction
        output = ""

        match action.action_type:
            case ActionType.NAVIGATION:
                action = cast(WebNavigationAction, action)
                for action_output in action.action_output:
                    match action_output.navigation_command:
                        case NavigationCommand.CLICK:
                            output = self.translate_click(action_output)
                        case NavigationCommand.HOVER:
                            output = self.translate_hover(action_output)
                        case NavigationCommand.SET_VALUE:
                            output = self.translate_set_value(action_output)
                        case NavigationCommand.SET_VALUE_AND_ENTER:
                            output = self.translate_set_value_and_enter(action_output)
                        case NavigationCommand.TYPE_KEY:
                            output = self.translate_type_key(action_output)
                        case NavigationCommand.SCROLL:
                            output = self.translate_scroll(action_output)
                        case _:
                            self.on_missing_action(action)

            case ActionType.EXTRACTION:
                action = cast(WebExtractionAction, action)
                for extraction_output in action.action_output:
                    output = self.translate_extract(extraction_output)

            case _:
                self.on_missing_action(action)

        output = f"# {instruction}\n{output}\n"
        return output

    def translate_click(self, action_output: NavigationOutput) -> Optional[str]:
        """Translates a click action into re usable code"""
        raise NotImplementedError("translate_click is not implemented")

    def translate_hover(self, action_output: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("translate_hover is not implemented")

    def translate_extract(self, action_output: ExtractionOutput) -> Optional[str]:
        raise NotImplementedError("translate_extract is not implemented")

    def translate_set_value(self, action_output: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("translate_set_value is not implemented")

    def translate_set_value_and_enter(
        self, action_output: NavigationOutput
    ) -> Optional[str]:
        raise NotImplementedError("translate_set_value_and_enter is not implemented")

    def translate_type_key(self, action_output: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("translate_type_key is not implemented")

    def translate_scroll(self, action_output: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("translate_scroll is not implemented")

    def merge_code(self, *codes: str | None) -> str:
        """Combine multiple strings into a single string"""
        return "\n".join(list(map(lambda x: x or "", codes)))

    def export(self, trajectory: Trajectory) -> str:
        setup = self.generate_setup(trajectory)
        teardown = self.generate_teardown(trajectory)
        actions = [self.translate_action(action) for action in trajectory.actions]
        return self.merge_code(setup, *actions, teardown)

    def export_to_file(self, trajectory: Trajectory, file_path: str):
        exported = self.export(trajectory)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(exported)
