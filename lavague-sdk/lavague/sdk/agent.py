from typing import Optional
from lavague.sdk.trajectory import Trajectory
from lavague.sdk.client import LaVague, RunRequest
from lavague.sdk.utilities.config import get_config


class WebAgent:
    """
    Web agent class, used to interact with the web.
    """

    client: LaVague

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[LaVague] = None,
        create_public_runs: bool = False,
    ):
        if client is None:
            if api_key is None:
                api_key = get_config("LAVAGUE_API_KEY")
            client = LaVague(api_key=api_key)
        self.client = client
        self.create_public_runs = create_public_runs

    def run(
        self,
        url: str,
        objective: str,
        async_run=False,
        viewport_size=(1096, 1096),
        open_in_studio=False,
    ) -> Trajectory:
        request = RunRequest(
            url=url,
            objective=objective,
            step_by_step=True,
            is_public=self.create_public_runs,
            viewport_size=viewport_size,
        )
        trajectory = self.client.run(request)
        if open_in_studio:
            trajectory.open_in_studio()
        if not async_run:
            trajectory.run_to_completion()
        return trajectory

    def load(self, run_id: str) -> Trajectory:
        return self.client.load(run_id)
