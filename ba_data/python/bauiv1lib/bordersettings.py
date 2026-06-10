""" i dunno """

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib.popup import PopupMenu
from bascenev1lib.screen_border import STYLES
import babase as ba

if TYPE_CHECKING:
    from typing import Any, Callable

class BorderSettingsWindow(bui.Window):
    """borderms"""

    def __init__(self, origin: Sequence[float] = (0, 0)):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 500
        height = 570 if uiscale is bui.UIScale.SMALL else 530
        v = height - 80
        self.res = bui.app.config.get('squda_border_res')
        self.style = bui.app.config.get('squda_border_style')
        scale = (
            1.5
            if uiscale is bui.UIScale.SMALL
            else 1.2 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        self._r = 'borderSettings'
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
        )
        v -= 180
        inc = 5
        # WIDTH
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.2 + xoffs, v),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.widthText'),
            maxwidth=(200 if uiscale is bui.UIScale.SMALL else 250),
            h_align='center',
            v_align='center',
        )
        bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.4 + xoffs, v - 25),
            size=(80, 80),
            scale=0.65,
            text_scale=1.6,
            label='-',
            repeat=True,
            on_activate_call=bui.Call(self.set_width, -inc),
        )
        self.width_text = bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.4 + 130 + xoffs, v),
            size=(0, 0),
            text=str(self.res[0]),
            maxwidth=130,
            h_align='center',
            v_align='center',
        )
        bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.4 + 200 + xoffs, v - 25),
            size=(80, 80),
            scale=0.65,
            text_scale=1.6,
            label='+',
            repeat=True,
            on_activate_call=bui.Call(self.set_width, inc),
        )
        v -= 70
        # HEIGHT
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.2 + xoffs, v),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.heightText'),
            maxwidth=(200 if uiscale is bui.UIScale.SMALL else 250),
            h_align='center',
            v_align='center',
        )
        bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.4 + xoffs, v - 25),
            size=(80, 80),
            scale=0.65,
            text_scale=1.6,
            label='-',
            repeat=True,
            on_activate_call=bui.Call(self.set_height, -inc),
        )
        self.height_text = bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.4 + 130 + xoffs, v),
            size=(0, 0),
            text=str(self.res[1]),
            maxwidth=130,
            h_align='center',
            v_align='center',
        )
        bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.4 + 200 + xoffs, v - 25),
            size=(80, 80),
            scale=0.65,
            text_scale=1.6,
            label='+',
            repeat=True,
            on_activate_call=bui.Call(self.set_height, inc),
        )
        v -= 70
        # STYLING
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.25 + xoffs, v),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.styleText'),
            maxwidth=(200 if uiscale is bui.UIScale.SMALL else 250),
            h_align='center',
            v_align='center',
        )
        choices = list(STYLES.keys())
        cdisp = [bui.Lstr(r=f'{self._r}.style{i}') for i in choices]
        PopupMenu(
            parent=self._root_widget,
            position=(width * 0.4 + 40 + xoffs, v - 30),
            width=250,
            autoselect=False,
            on_value_change_call=bui.WeakCall(self.set_style),
            choices=choices,
            choices_display=cdisp,
            button_size=(200, 60),
            current_choice=bui.app.config.get("squda_border_style"),
        )
        v -= 90
        # TOGGLE
        bui.checkboxwidget(
            parent=self._root_widget,
            position=(width * 0.26 + xoffs, v),
            size=(220, 50),
            autoselect=False,
            maxwidth=300,
            textcolor=(1, 1, 1),
            value=bui.app.config.get('squda_border_toggle', False),
            text=bui.Lstr(resource=f"{self._r}.toggleText"),
            on_value_change_call=self.toggle,
        )
        
        uiscale = bui.app.ui_v1.uiscale
            
    def close(self) -> None:
        """Close the window."""
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
    
    def update(self):
        self.res = bui.app.config.get('squda_border_res')
        self.style = bui.app.config.get('squda_border_style')
        border = getattr(bui.app, 'screen_border', None)
        if border:
            with bs.get_foreground_host_session().context:
                border.refresh_size()
                border.set_style(self.style)
        bui.textwidget(
            edit=self.width_text,
            text=str(self.res[0]),
        )
        bui.textwidget(
            edit=self.height_text,
            text=str(self.res[1]),
        )
    
    def toggle(self, val):
        bui.app.config['squda_border_toggle'] = val
        if val == True:
            sesh = bs.get_foreground_host_session
            sesh._make_border()
        else:
            border = getattr(bui.app, 'screen_border', None)
            if border:
                border.delete()
                bui.app.screen_border = None
    
    def set_width(self, val):
        bui.app.config['squda_border_res'] = (
            self.res[0] + val, self.res[1]
        )
        self.update()
    
    def set_height(self, val):
        bui.app.config['squda_border_res'] = (
            self.res[0], self.res[1] + val
        )
        self.update()
    
    def set_style(self, val):
        bui.app.config['squda_border_style'] = val
        self.update()
    

