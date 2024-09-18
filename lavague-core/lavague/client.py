from pydantic import BaseModel
from lavague.utilities.config import get_config, is_flag_true, LAVAGUE_API_BASE_URL
from lavague.action import ActionParser, DEFAULT_PARSER
from lavague.trajectory import Trajectory
from typing import Any, Optional
import requests


class LaVagueClient(BaseModel):
    """
    Client to interact with the LaVague API.
    """

    api_base_url: str = get_config("LAVAGUE_API_BASE_URL", LAVAGUE_API_BASE_URL)
    api_key: str = get_config("LAVAGUE_API_KEY")
    telemetry: bool = is_flag_true("LAVAGUE_TELEMETRY", True)
    parser: ActionParser = DEFAULT_PARSER

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
