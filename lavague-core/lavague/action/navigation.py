from lavague.action import Action
from typing import Optional


class NavigationAction(Action):
    """Navigation action performed by the agent."""

    xpath: str
    value: Optional[str] = None
