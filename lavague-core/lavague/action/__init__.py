from lavague.action.base import (
    Action,
    ActionStatus,
    ActionParser,
    DEFAULT_PARSER,
    UnhandledTypeException,
    ActionTranslator,
)

from lavague.action.navigation import NavigationAction

DEFAULT_PARSER.register("navigation", NavigationAction)
