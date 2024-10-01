from lavague.sdk.client import LaVagueClient
from lavague.sdk.base_driver import BaseDriver


class CloudDriver(BaseDriver):
    """
    Cloud driver class, used to interact with the cloud.
    """

    def __init__(self, client: LaVagueClient):
        self.client = client
