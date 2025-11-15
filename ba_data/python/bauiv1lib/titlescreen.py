""" i dunno """

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib.popup import PopupMenu
import babase as ba

if TYPE_CHECKING:
    from typing import Any, Callable


class TitleWindow(bui.MainWindow):
    def __init__(
        self, 
        origin_widget: bui.Widget | None = None,
        transition: str | None = 'in_right',
        ):
        bui.set_party_window_open(True)
        self._width = 0
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._height= 0
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(10, -100),
            size=(0, 0),
            scale=1.6,
            text='PRESS SELECT',
            color=(1, 1, 1),
            h_align='center',
            v_align='center',
        )
        self.play_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(1000, 1000),
            size=(80, 80),
            color=(0.6, 0.3, 0.3),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.3,
            label='hi im the select button your supposed \nto press me with a button twin',
            on_activate_call=self.close,
        )
    def close(self) -> None:
        """Close the window."""
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
        from bauiv1lib.mainmenu import MainMenuWindow
        self.main_window_replace(
            MainMenuWindow(
                origin_widget=self._root_widget,
            )
        )
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
