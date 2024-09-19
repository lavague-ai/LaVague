from lavague.action.base import (
    Action,
    ActionStatus,
    ActionParser,
    DEFAULT_PARSER,
    UnhandledTypeException,
)

from lavague.action.navigation import NavigationAction

DEFAULT_PARSER.register("web_navigation", NavigationAction)
