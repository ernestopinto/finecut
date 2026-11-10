"""Smoke tests for the Finecut main window."""

from pytestqt.qtbot import QtBot

from finecut.ui.main_window import FinecutMainWindow


def test_main_window_displays_new_snip_button(qtbot: QtBot) -> None:
    """Verify the window renders its title, + Novo trigger, and stub click feedback."""
    window = FinecutMainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "Finecut"
    assert window.new_snip_button.text() == "+ Novo"

    window.new_snip_button.click()
    assert "FC-003" in window.statusBar().currentMessage()
