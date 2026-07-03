""" i dunno """
from __future__ import annotations

from typing import TYPE_CHECKING, override, cast
import logging

import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib.popup import PopupMenu
from bascenev1lib.screen_border import STYLES
import babase as ba

if TYPE_CHECKING:
    from typing import Any, Callable

class ManualSignInWindow(bui.Window):
    def __init__(self):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 700
        height = 570 if uiscale is bui.UIScale.SMALL else 500
        v = height - 80
        scale = (
            1.5
            if uiscale is bui.UIScale.SMALL
            else 1.2 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        self._r = 'manualSignInWindow'
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                transition='in_scale',
                toolbar_visibility='menu_minimal',
                scale=scale,
            ),
            # We exist in the overlay stack so main-windows being
            # recreated doesn't affect us.
            prevent_main_window_auto_recreate=False,
        )
        xoffs = 0
        if uiscale is bui.UIScale.SMALL:
            xoffs = 100
        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.close
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=False,
                position=(width * 0.05, height - 80),
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
                height - (
                    75 if uiscale 
                    is bui.UIScale.SMALL 
                    else 40
                ),
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
            max_height=210,
        )
        v -= 210
        inc = 5
        stored = bui.app.config.get('squda_stored_credentials', {})
        try:
            name = list(stored.keys())[0]
            credential = list(stored.values())[0]
        except (IndexError, KeyError):
            name = ''
            credential = ''
            
        self._name_field = bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5 - 130, v),
            size=(300, 40),
            text=name,
            maxwidth=280,
            v_align='center',
            editable=True
        )
        v -= 50
        self._credential_field =  bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5 - 130, v),
            size=(300, 40),
            text=credential,
            maxwidth=280,
            v_align='center',
            editable=True
        )
        v -= 70
        bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(width * 0.5 - 60, v),
            size=(140, 40),
            text_scale=1.0,
            label=bui.Lstr(r=f'{self._r}.storeText'),
            on_activate_call=self._store_input,
        )
        v -= 50
        bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(width * 0.5 - 60, v),
            size=(140, 40),
            label=bui.Lstr(r=f'{self._r}.doneText'),
            on_activate_call=self._sign_in,
        )
            
    def close(self) -> None:
        """Close the window."""
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
    
    def _sign_in(self):
        c_input = cast(
            str, 
            bui.textwidget(query=self._credential_field)
        ).strip()
        accs = bui.app.plus.accounts
        accs.set_primary_credentials(c_input)
        self.close()
    
    def _store_input(self):
        name_input = cast(
            str, 
            bui.textwidget(query=self._name_field)
        ).strip()
        c_input = cast(
            str, 
            bui.textwidget(query=self._credential_field)
        ).strip()
        creds = bui.app.config.get('squda_stored_credentials', {})
        creds[name_input] = c_input
        bui.getsound('gunCocking').play()

