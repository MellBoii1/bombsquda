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

class BorderSettingsWindow(bui.Window):
    """borderms"""

    def __init__(self, origin: Sequence[float] = (0, 0)):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 500
        height = 600
        v = height - 80
        self.res = bui.app.config.get('squda_border_res')
        scale = (
            1.55
            if uiscale is bui.UIScale.SMALL
            else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        self._r = 'borderSettings'
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                transition='in_scale',
                scale=scale,
            ),
            # We exist in the overlay stack so main-windows being
            # recreated doesn't affect us.
            prevent_main_window_auto_recreate=False,
        )
        self._back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(width * 0.1, height - 80),
            size=(80, 80),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.3,
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.close,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        
        bui.textwidget(
            parent=self._root_widget,
            position=(
                width * 0.5,
                height - 40,
            ),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            scale=0.9 if uiscale is bui.UIScale.SMALL else 1.0,
            maxwidth=(130 if uiscale is bui.UIScale.SMALL else 250),
            h_align='center',
            v_align='center',
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, v),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.infoText'),
            maxwidth=(width * 0.9),
            h_align='center',
            v_align='top',
        )
        v -= 180
        inc = 5
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.2, v),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.widthText'),
            maxwidth=(200 if uiscale is bui.UIScale.SMALL else 250),
            h_align='center',
            v_align='center',
        )
        bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.4, v - 25),
            size=(80, 80),
            scale=0.65,
            text_scale=1.6,
            label='-',
            on_activate_call=bui.Call(self.set_width, -inc),
        )
        self.width_text = bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.2, v),
            size=(0, 0),
            text=str(self.res[0]),
            maxwidth=(200 if uiscale is bui.UIScale.SMALL else 250),
            h_align='center',
            v_align='center',
        )
        bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.4 + 200, v - 25),
            size=(80, 80),
            scale=0.65,
            text_scale=1.6,
            label='+',
            on_activate_call=bui.Call(self.set_width, inc),
        )
        
        uiscale = bui.app.ui_v1.uiscale
            
    def close(self) -> None:
        """Close the window."""
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
        self._timer = None
    
    def update_labels(self):
        pass
    
    def set_width(self, val):
        bui.app.config['squda_border_res'] = (
            self.res[0] + val, self.res[1]
        )
        self.update_labels()
    
    def set_height(self, val):
        bui.app.config['squda_border_res'] = (
            self.res[0] + val, self.res[1]
        )
        self.update_labels()

