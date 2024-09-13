from pydantic import BaseModel
from lavague.core.utilities.config import get_config, LAVAGUE_API_BASE_URL
from lavague.core.action import ActionParser, DEFAULT_PARSER
from lavague.core.trajectory import Trajectory
from pydantic_core import from_json
from typing import Any, Optional
import requests


class LaVagueClient(BaseModel):
    """
    Client to interact with the LaVague API.
    """

    api_base_url: str = get_config("LAVAGUE_API_BASE_URL", LAVAGUE_API_BASE_URL)
    api_key: str = get_config("LAVAGUE_API_KEY")
    parser: ActionParser = DEFAULT_PARSER

    def request_api(self, endpoint: str, method: str, json: Optional[Any]) -> bytes:
        response = requests.request(
            method,
            f"{self.api_base_url}/{endpoint}",
            json=json,
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        if response.status_code > 299:
            raise ApiException(response.text)
        return response.content

    def run(self, url: str, objective: str) -> Trajectory:
        content = self.request_api("/run", "POST", {"url": url, "objective": objective})
        result = from_json(content)
        result_list = result.get("results", [])
        actions = [self.parser.parse(action) for action in result_list]
        trajectory = Trajectory(**result, actions=actions)
        return trajectory


class ApiException(Exception):
    pass
