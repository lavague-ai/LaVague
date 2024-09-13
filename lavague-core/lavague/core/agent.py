import logging
from pydantic import BaseModel
from typing import Optional
from lavague.core.trajectory import Trajectory
from lavague.core.client import LaVagueClient
from lavague.core.utilities.config import get_config

logging_print = logging.getLogger(__name__)
logging_print.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(format)
logging_print.addHandler(ch)
logging_print.propagate = False


class WebAgent(BaseModel):
    """
    Web agent class, used to interact with the web.
    """

    client: LaVagueClient

    def __init__(self, api_key: Optional[str] = None, client: LaVagueClient = None):
        if client is None:
            if api_key is None:
                api_key = get_config("LAVAGUE_API_KEY")
            client = LaVagueClient(api_key=api_key)

        super().__init__(client=client)

    def run(self, url: str, objective: str) -> Trajectory:
        return self.client.run(url, objective)

    def __call__(self, url: str, objective: str) -> Trajectory:
        return self.run(url, objective)