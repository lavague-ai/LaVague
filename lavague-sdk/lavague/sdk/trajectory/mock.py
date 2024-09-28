from lavague.sdk.trajectory.controller import TrajectoryController
from lavague.sdk.action import Action, ActionParser, DEFAULT_PARSER, ActionStatus
from lavague.sdk.trajectory.model import StepCompletion, RunStatus
from typing import List, Dict


class MockTrajectoryController(TrajectoryController):
    def __init__(self, next_actions: List[Action]):
        self.next_actions = next_actions
        self.current_action_index = -1

    def next_step(self, run_id: str):
        self.current_action_index += 1
        action = self.next_actions[self.current_action_index]
        run_status = (
            RunStatus.RUNNING if self.has_next_step() else self.get_completion_status()
        )
        return StepCompletion(action=action, run_status=run_status)

    def has_next_step(self):
        return self.current_action_index < len(self.next_actions) - 1

    def get_completion_status(self) -> RunStatus:
        return (
            RunStatus.SUCCESS
            if len(self.next_actions) == 0
            or self.next_actions[-1].status == ActionStatus.COMPLETED
            else RunStatus.FAILED
        )

    def stop_run(self, run_id: str):
        pass

    @classmethod
    def from_actions_dict(
        cls, next_actions_list: List[Dict], parser: ActionParser = DEFAULT_PARSER
    ):
        return cls([parser.parse(action_dict) for action_dict in next_actions_list])
