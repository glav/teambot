"""Split-pane terminal interface for TeamBot."""

from teambot.ui.app import TeamBotApp, should_use_split_pane
from teambot.ui.widgets import InputPane, OutputPane

__all__ = ["TeamBotApp", "InputPane", "OutputPane", "should_use_split_pane"]
