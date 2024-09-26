from lavague.trajectory.model import StepCompletion
from lavague.utilities.config import get_config, is_flag_true, LAVAGUE_API_BASE_URL
from lavague.action import ActionParser, DEFAULT_PARSER
from lavague.trajectory import RunnableTrajectory
from lavague.trajectory.controller import TrajectoryController
from typing import Any, Optional
import requests


class LaVagueClient(TrajectoryController):
    """Client to interact with the LaVague API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        parser: ActionParser = DEFAULT_PARSER,
        telemetry: bool = is_flag_true("LAVAGUE_TELEMETRY", True),
    ):
        self.api_key: str = api_key or get_config("LAVAGUE_API_KEY")
        self.api_base_url: str = api_base_url or get_config(
            "LAVAGUE_API_BASE_URL", LAVAGUE_API_BASE_URL
        )
        self.parser = parser
        self.telemetry = telemetry

    def request_api(
        self, endpoint: str, method: str, json: Optional[Any] = None
    ) -> bytes:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        if not self.telemetry:
            headers["DNT"] = "1"
        response = requests.request(
            method,
            f"{self.api_base_url}/{endpoint}",
            json=json,
            headers=headers,
        )
        if response.status_code > 299:
            raise ApiException(response.text)
        return response.content

    def create_run(
        self, url: str, objective: str, step_by_step=False
    ) -> RunnableTrajectory:
        content = self.request_api(
            "/runs",
            "POST",
            {"url": url, "objective": objective, "step_by_step": step_by_step},
        )
        return RunnableTrajectory.from_data(content, self.parser)

    def next_step(self, run_id: str) -> StepCompletion:
        content = self.request_api(
            f"/runs/{run_id}/step",
            "POST",
        )
        return StepCompletion.model_validate_json(content)

    def stop_run(self, run_id: str) -> None:
        self.request_api(
            f"/runs/{run_id}/stop",
            "POST",
        )


class ApiException(Exception):
    pass
