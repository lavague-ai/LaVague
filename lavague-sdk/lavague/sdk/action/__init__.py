from lavague.sdk.action.base import (
    Action,
    Instruction,
    EngineType,
    ActionType,
    ActionStatus,
    ActionParser,
    DEFAULT_PARSER,
    UnhandledTypeException,
)

from lavague.sdk.action.navigation import WebNavigationAction
from lavague.sdk.action.extraction import WebExtractionAction

DEFAULT_PARSER.register("web_navigation", WebNavigationAction)
DEFAULT_PARSER.register("web_extraction", WebExtractionAction)
