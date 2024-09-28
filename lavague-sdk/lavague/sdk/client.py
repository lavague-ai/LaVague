from pydantic import BaseModel
from lavague.sdk.utilities.config import get_config, is_flag_true, LAVAGUE_API_BASE_URL
from lavague.sdk.action import ActionParser, DEFAULT_PARSER
from lavague.sdk.trajectory import Trajectory
from typing import Any, Optional
import requests


class LaVagueClient(BaseModel):
    """
    Client to interact with the LaVague API.
    """

    def __init__(self):
        self.api_base_url = get_config("LAVAGUE_API_BASE_URL", LAVAGUE_API_BASE_URL)
        self.api_key = get_config("LAVAGUE_API_KEY")
        self.telemetry: bool = is_flag_true("LAVAGUE_TELEMETRY", True)
        self.parser: ActionParser = DEFAULT_PARSER

    def request_api(self, endpoint: str, method: str, json: Optional[Any]) -> bytes:
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

    def run(self, url: str, objective: str) -> Trajectory:
        content = self.request_api("/run", "POST", {"url": url, "objective": objective})
        return Trajectory.from_data(content, self.parser)


class ApiException(Exception):
    pass
