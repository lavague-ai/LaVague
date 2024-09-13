from lavague.core.action.base import Action, ActionParser, DEFAULT_PARSER

from lavague.core.action.navigation import NavigationAction
from lavague.core.action.navigation_control import ControlsAction

DEFAULT_PARSER.register("navigation", NavigationAction)
DEFAULT_PARSER.register("controls", ControlsAction)
