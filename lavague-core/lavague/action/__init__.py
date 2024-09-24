from lavague.action.base import (
    Action,
    ActionType,
    ActionStatus,
    ActionParser,
    DEFAULT_PARSER,
    UnhandledTypeException,
)

from lavague.action.navigation import WebNavigationAction
from lavague.action.extraction import WebExtractionAction

DEFAULT_PARSER.register("web_navigation", WebNavigationAction)
DEFAULT_PARSER.register("web_extraction", WebExtractionAction)
