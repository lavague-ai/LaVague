from typing import Dict, Optional, Iterator
from pydantic_core import from_json
from lavague.sdk.action import ActionParser, DEFAULT_PARSER
from lavague.sdk.trajectory.controller import TrajectoryController
from lavague.sdk.trajectory.model import TrajectoryData, RunStatus
from lavague.sdk.action import Action


class Trajectory(TrajectoryData):
    """Trajectory of web interactions towards an objective."""

    _controller: TrajectoryController

    @property
    def is_running(self):
        return self.status in (RunStatus.STARTING, RunStatus.RUNNING)

    def next_action(self):
        ret = self._controller.next_step(self.run_id)
        self.status = ret.run_status
        if ret.action:
            self.actions.append(ret.action)
        return ret.action

    def run_to_completion(self):
        try:
            while self.is_running:
                self.next_action()
            return self.status
        except KeyboardInterrupt:
            self.stop_run()
            return self.status

    def stop_run(self):
        self._controller.stop(self.run_id)
        self.status = RunStatus.CANCELLED

    def iter_actions(self) -> Iterator[Action]:
        yield from self.actions
        while self.is_running:
            yield self.next_action()

    @classmethod
    def from_data(
        cls,
        data: str | bytes | bytearray,
        parser: ActionParser = DEFAULT_PARSER,
        controller: Optional[TrajectoryController] = None,
    ):
        obj = from_json(data)
        return cls.from_dict(obj, parser, controller)

    @classmethod
    def from_dict(
        cls,
        data: Dict,
        parser: ActionParser = DEFAULT_PARSER,
        controller: Optional[TrajectoryController] = None,
    ):
        actions = [parser.parse(action) for action in data.get("actions", [])]
        trajectory = cls.model_validate({**data, "actions": actions})
        if controller is not None:
            trajectory._controller = controller
        return trajectory

    @classmethod
    def from_file(
        cls,
        file_path: str,
        parser: ActionParser = DEFAULT_PARSER,
        encoding="utf-8",
        controller: Optional[TrajectoryController] = None,
    ):
        with open(file_path, "r", encoding=encoding) as file:
            content = file.read()
            return cls.from_data(content, parser, controller)
