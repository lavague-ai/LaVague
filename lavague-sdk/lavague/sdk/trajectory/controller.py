from abc import ABC, abstractmethod
from lavague.sdk.trajectory.model import StepCompletion


class TrajectoryController(ABC):
    @abstractmethod
    def next_step(self, run_id: str) -> StepCompletion:
        pass

    @abstractmethod
    def stop(self, run_id: str) -> None:
        pass
