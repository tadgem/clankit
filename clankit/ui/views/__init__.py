"""UI View components for Clankit."""

from clankit.ui.views.console_view import ConsoleViewComponent
from clankit.ui.views.dialogs import DialogManager
from clankit.ui.views.diff_viewer import DiffViewerComponent
from clankit.ui.views.history_view import HistoryViewComponent
from clankit.ui.views.sidebar import SidebarComponent
from clankit.ui.views.staging_view import StagingViewComponent
from clankit.ui.views.toolbar import ToolbarComponent

__all__ = [
    "ConsoleViewComponent",
    "DialogManager",
    "DiffViewerComponent",
    "HistoryViewComponent",
    "SidebarComponent",
    "StagingViewComponent",
    "ToolbarComponent",
]
