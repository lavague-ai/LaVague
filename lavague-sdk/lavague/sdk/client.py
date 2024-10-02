from io import BytesIO
from typing import Any, Optional, Tuple

import requests
from lavague.sdk.action import DEFAULT_PARSER, ActionParser
from lavague.sdk.trajectory import Trajectory
from lavague.sdk.trajectory.controller import TrajectoryController
from lavague.sdk.trajectory.model import StepCompletion
from lavague.sdk.utilities.config import LAVAGUE_API_BASE_URL, get_config, is_flag_true
from PIL import Image, ImageFile
from pydantic import BaseModel


class RunRequest(BaseModel):
    url: str
    objective: str
    step_by_step: Optional[bool] = False
    cloud_driver: Optional[bool] = True
    await_completion: Optional[bool] = False
    is_public: Optional[bool] = False
    viewport_size: Optional[Tuple[int, int]] = None


class RunUpdate(BaseModel):
    objective: Optional[str] = None
    is_public: Optional[bool] = False


class LaVague(TrajectoryController):
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

    def run(self, request: RunRequest) -> Trajectory:
        content = self.request_api(
            "/runs",
            "POST",
            request.model_dump(),
        )
        return Trajectory.from_data(content, self.parser, self)

    def update(self, run_id: str, request: RunUpdate) -> Trajectory:
        content = self.request_api(
            f"/runs/{run_id}",
            "PATCH",
            request.model_dump(),
        )
        return Trajectory.from_data(content, self.parser, self)

    def load(self, run_id: str) -> Trajectory:
        content = self.request_api(f"/runs/{run_id}", "GET")
        return Trajectory.from_data(content, self.parser, self)

    def next_step(self, run_id: str) -> StepCompletion:
        content = self.request_api(
            f"/runs/{run_id}/step",
            "POST",
        )
        return StepCompletion.model_validate_json(content)

    def stop(self, run_id: str) -> None:
        self.request_api(
            f"/runs/{run_id}/stop",
            "POST",
        )

    def get_preaction_screenshot(self, step_id: str) -> ImageFile.ImageFile:
        content = self.request_api(f"/steps/{step_id}/screenshot/preaction", "GET")
        return Image.open(BytesIO(content))

    def get_postaction_screenshot(self, step_id: str) -> ImageFile.ImageFile:
        content = self.request_api(f"/steps/{step_id}/screenshot/preaction", "GET")
        return Image.open(BytesIO(content))

    def get_screenshot(self, run_id: str) -> ImageFile.ImageFile:
        content = self.request_api(f"/runs/{run_id}/screenshot", "GET")
        return Image.open(BytesIO(content))

    def get_run_view_url(self, run_id: str) -> str:
        return f"{self.api_base_url}/runs/{run_id}/view"


class ApiException(Exception):
    pass
