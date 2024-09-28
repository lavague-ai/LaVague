from typing import Optional
from lavague.sdk.trajectory import Trajectory
from lavague.sdk.client import LaVagueClient
from lavague.sdk.utilities.config import get_config


class WebAgent:
    """
    Web agent class, used to interact with the web.
    """

    client: LaVagueClient

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[LaVagueClient] = None,
    ):
        if client is None:
            if api_key is None:
                api_key = get_config("LAVAGUE_API_KEY")
            client = LaVagueClient(api_key=api_key)
        self.client = client

    def run(self, url: str, objective: str, async_run=False) -> Trajectory:
        trajectory = self.client.create_run(url, objective, step_by_step=True)
        if not async_run:
            trajectory.run_to_completion()
        return trajectory

    def load(self, run_id: str) -> Trajectory:
        return self.client.load_run(run_id)
