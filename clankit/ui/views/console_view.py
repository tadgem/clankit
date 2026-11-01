"""Real-time Git CLI activity log and console drawer."""

from __future__ import annotations
import dearpygui.dearpygui as dpg
from clankit.git.models import CommandResult
from clankit.ui.theme import SourceTreeColors


class ConsoleViewComponent:
    """Displays executed git CLI commands and process outputs for user transparency."""

    def __init__(self, parent_tag: str, tag: str = "git_console_drawer"):
        self.parent_tag = parent_tag
        self.tag = tag
        self.list_tag = f"{tag}_list"
        self.details_tag = f"{tag}_details"
        self.results: list[CommandResult] = []

    def build(self) -> None:
        """Build the collapsible activity console drawer."""
        with dpg.collapsing_header(
            parent=self.parent_tag,
            label="Git Activity Console (CLI Transparency)",
            default_open=False,
            tag=self.tag,
        ):
            with dpg.group(horizontal=True):
                dpg.add_button(label="Clear History", callback=self.clear_logs)
                dpg.add_text("Raw git commands executed directly by Clankit:", color=SourceTreeColors.TEXT_MUTED)

            with dpg.child_window(tag=self.list_tag, height=130, border=True, horizontal_scrollbar=True):
                dpg.add_text("No git commands executed yet.", tag=f"{self.list_tag}_empty", color=SourceTreeColors.TEXT_MUTED)

            dpg.add_text("Command Details & Output:", color=SourceTreeColors.TEXT_MUTED)
            dpg.add_input_text(
                tag=self.details_tag,
                multiline=True,
                readonly=True,
                height=100,
                width=-1,
                default_value="Select or run a command to view stdout/stderr output.",
            )

    def log_command(self, result: CommandResult) -> None:
        """Append an executed command to the console log."""
        self.results.append(result)

        # Remove empty placeholder if present
        if dpg.does_item_exist(f"{self.list_tag}_empty"):
            dpg.delete_item(f"{self.list_tag}_empty")

        status_text = f"[OK {result.duration_ms:.1f}ms]" if result.success else f"[ERR {result.returncode}]"
        status_color = SourceTreeColors.STATUS_ADDED if result.success else SourceTreeColors.STATUS_DELETED

        item_tag = f"cmd_log_{len(self.results)}"
        with dpg.group(parent=self.list_tag, horizontal=True, tag=item_tag):
            dpg.add_text(status_text, color=status_color)
            dpg.add_selectable(
                label=f"$ {result.display_command}",
                user_data=result,
                callback=self._on_select_command,
            )

        # Set default value of details box to latest command output
        self._show_details(result)

    def _on_select_command(self, sender, app_data, user_data: CommandResult) -> None:
        self._show_details(user_data)

    def _show_details(self, result: CommandResult) -> None:
        text = [
            f"COMMAND: $ {result.display_command}",
            f"WORKING DIR: {result.cwd}",
            f"EXIT CODE: {result.returncode}",
            f"DURATION: {result.duration_ms:.2f} ms",
            "---------------- STDOUT ----------------",
            result.stdout if result.stdout else "(empty)",
            "---------------- STDERR ----------------",
            result.stderr if result.stderr else "(empty)",
        ]
        dpg.set_value(self.details_tag, "\n".join(text))

    def clear_logs(self) -> None:
        self.results.clear()
        dpg.delete_item(self.list_tag, children_only=True)
        dpg.add_text("No git commands executed yet.", parent=self.list_tag, tag=f"{self.list_tag}_empty", color=SourceTreeColors.TEXT_MUTED)
        dpg.set_value(self.details_tag, "")
