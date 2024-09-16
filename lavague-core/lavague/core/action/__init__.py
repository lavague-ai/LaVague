from lavague.core.action.base import (
    Action,
    ActionStatus,
    ActionParser,
    DEFAULT_PARSER,
    UnhandledTypeException,
)

from lavague.core.action.navigation import NavigationAction

DEFAULT_PARSER.register("navigation", NavigationAction)
