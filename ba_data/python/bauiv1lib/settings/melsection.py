# Released under the MIT License. See LICENSE for details.
#
"""UI for setting... settings."""

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Callable

class ParrySelectionWindow(bui.Window):
    """
    Allows you to like
    set different parry time windows
    but then like
    you dont get  as much benefit
    or somethin idk
    """

    def __init__(self, origin: Sequence[float] = (0, 0)):
        bui.set_party_window_open(True)
        self._width = 800
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._height= 600
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
            ),
            # We exist in the overlay stack so main-windows being
            # recreated doesn't affect us.
            prevent_main_window_auto_recreate=False,
        )
        uiscale = bui.app.ui_v1.uiscale
        leftside = self._width / self._width + 100
        short = 180
        self.parry1button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(leftside, self._height - short),
            size=(200, 200),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.5,
            label='ez',
            on_activate_call=self.parrysetup3,
        )
        self.parry2button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(leftside, self._height - short * 2),
            size=(200, 200),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.5,
            label='mid',
            on_activate_call=self.parrysetup2,
        )
        self.parry3button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(leftside, self._height - short * 3),
            size=(200, 200),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.3,
            label='precise \nas fuck',
            on_activate_call=self.parrysetup1,
        )
        textersspace = 210
        bui.textwidget(
            parent=self._root_widget,
            position=(leftside + textersspace, self._height - short),
            size=(150, 150),
            text='This will change parry timing to be 0.3. \nEasier to parry, but you get less health.',
            h_align='left',
            v_align='center',
            scale=1.0,
            maxwidth=500,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(leftside + textersspace, self._height - short * 2),
            size=(150, 150),
            text='This will change parry timing to be 0.2. \nIt will not affect health, nor will \nadd anything special.',
            h_align='left',
            v_align='center',
            scale=1.0,
            maxwidth=500,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(leftside + textersspace, self._height - short * 3),
            size=(150, 150),
            text='This will change parry timing to be 0.1. \nHarder to hit parries, but you can \ncounter and get more health.',
            h_align='left',
            v_align='center',
            scale=1.0,
            maxwidth=500,
        )
        
    def close(self) -> None:
        """Close the window."""
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
        
    # can someone out there tell me if 
    # there's a easier way to do this
    def parrysetup1(self) -> None:
        cfg = bui.app.config
        cfg['parrytype'] = 1
        cfg.apply_and_commit()
        self.close()
        
    def parrysetup2(self) -> None:
        cfg = bui.app.config
        cfg['parrytype'] = 2
        cfg.apply_and_commit()
        self.close()
        
    def parrysetup3(self) -> None:
        cfg = bui.app.config
        cfg['parrytype'] = 3
        cfg.apply_and_commit()
        self.close()
    
class MelWindow(bui.MainWindow):
    """Window for selecting BombSquda settings."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('BombSquda Settings')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 700
        self._r = 'melWindow'

        uiscale = bui.app.ui_v1.uiscale

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        safesize = bui.get_virtual_safe_area_size()

        # We're a generally widescreen shaped window, so bump our
        # overall scale up a bit when screen width is wider than safe
        # bounds to take advantage of the extra space.
        smallscale = min(2.0, 1.5 * screensize[0] / safesize[0])

        scale = (
            smallscale
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_height = min(height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        # scroll_width = target_width
        # scroll_height = target_height - 25
        # scroll_bottom = yoffs - 54 - scroll_height

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(50, yoffs - 80.0),
                size=(70, 70),
                scale=0.8,
                text_scale=1.2,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        thefuckedupuifix = 200
        bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,)
        self._fuckedupspaz = bui.checkboxwidget(
            parent=self._root_widget,
            position=(250, 300 + thefuckedupuifix),
            size=(180, 40),
            autoselect=False,
            maxwidth=300,
            textcolor=(1.0, 1.0, 1.0),
            value=bui.app.config.get("spazfuckedup", False),
            text='big eyed spaz!!!!!!',
            on_value_change_call=self.changespazinga
        )
        self._noise = bui.checkboxwidget(
            parent=self._root_widget,
            position=(250, 250 + thefuckedupuifix),
            size=(180, 40),
            autoselect=False,
            maxwidth=300,
            textcolor=(1.0, 1.0, 1.0),
            value=bui.app.config.get("noisepolution", False),
            text='make my game inaudible',
            on_value_change_call=self.changenoise
        )
        self._random = bui.checkboxwidget(
            parent=self._root_widget,
            position=(250, 200 + thefuckedupuifix),
            size=(180, 40),
            autoselect=False,
            maxwidth=300,
            textcolor=(1.0, 1.0, 1.0),
            value=bui.app.config.get("gamblingmode", False),
            text='i love gambling!',
            on_value_change_call=self.changegambling
        )
        self._hardmode = bui.checkboxwidget(
            parent=self._root_widget,
            position=(250, 150 + thefuckedupuifix),
            size=(180, 40),
            autoselect=False,
            maxwidth=300,
            textcolor=(0.9, 0.2, 0.2),
            value=bui.app.config.get("spazhardmode", False),
            text='make me oneshot die lmfao',
            on_value_change_call=self.changehardmode
        )
        self._canalwaysparry = bui.checkboxwidget(
            parent=self._root_widget,
            position=(250, 100 + thefuckedupuifix),
            size=(180, 40),
            autoselect=False,
            maxwidth=300,
            textcolor=(1.0, 1.0, 1.0),
            value=bui.app.config.get("parryalways", False),
            text='i wanna parry all the time',
            on_value_change_call=self.changeparry
        )
        self.parrysetup = bui.buttonwidget(
            parent=self._root_widget,
            position=(600, 90 + thefuckedupuifix),
            button_type='square',
            size=(180, 50),
            label='setup parrying type',
            autoselect=False,
            on_activate_call=ParrySelectionWindow
        )
        self._shutdownprevention = bui.checkboxwidget(
            parent=self._root_widget,
            position=(250, 50 + thefuckedupuifix),
            size=(180, 40),
            autoselect=False,
            maxwidth=300,
            textcolor=(1.0, 1.0, 1.0),
            value=bui.app.config.get("dontshutdown", False),
            text='pls dont shutdown my pc i dont like that',
            on_value_change_call=self.changeshutdown
        )
        self._changemario = bui.checkboxwidget(
            parent=self._root_widget,
            position=(250, 0 + thefuckedupuifix),
            size=(180, 40),
            autoselect=False,
            maxwidth=300,
            textcolor=(1.0, 1.0, 1.0),
            value=bui.app.config.get("dontdomarioman", False),
            text='i hate fuckass mario delay on quit',
            on_value_change_call=self.changemario
        )
        self._changediscord = bui.checkboxwidget(
            parent=self._root_widget,
            position=(250, -50 + thefuckedupuifix),
            size=(180, 40),
            autoselect=False,
            maxwidth=300,
            textcolor=(1.0, 1.0, 1.0),
            value=bui.app.config.get("richpresence", False),
            text='enable discord rpc',
            on_value_change_call=self.changediscord
        )
        self._changemeter = bui.checkboxwidget(
            parent=self._root_widget,
            position=(250, -100 + thefuckedupuifix),
            size=(180, 40),
            autoselect=False,
            maxwidth=300,
            textcolor=(1.0, 1.0, 1.0),
            value=bui.app.config.get("enablemeter", False),
            text='enable earthbound-ish visualizer',
            on_value_change_call=self.changemeter
        )

    def changehardmode(self, val: str) -> None:
        cfg = bui.app.config
        cfg['spazhardmode'] = val
        cfg.apply_and_commit()
        if val == True:
            bui.getsound('baditem').play()
        if val == False:
            bui.getsound('okitem').play()

    def changegambling(self, val: str) -> None:
        cfg = bui.app.config
        cfg['gamblingmode'] = val
        cfg.apply_and_commit() 
        
    def changenoise(self, val: str) -> None:
        cfg = bui.app.config
        cfg['noisepolution'] = val
        cfg.apply_and_commit()
        
    def changespazinga(self, val: str) -> None:
        cfg = bui.app.config
        cfg['spazfuckedup'] = val
        cfg.apply_and_commit()
        
    def changeparry(self, val: str) -> None:
        cfg = bui.app.config
        cfg['parryalways'] = val
        cfg.apply_and_commit()
        
    def changeshutdown(self, val: str) -> None:
        cfg = bui.app.config
        cfg['dontshutdown'] = val
        cfg.apply_and_commit()
        
    def changemario(self, val: str) -> None:
        cfg = bui.app.config
        cfg['dontdomarioman'] = val
        cfg.apply_and_commit()
    
    def changediscord(self, val: str) -> None:
        cfg = bui.app.config
        cfg['richpresence'] = val
        cfg.apply_and_commit()
    
    def changemeter(self, val: str) -> None:
        cfg = bui.app.config
        cfg['enablemeter'] = val
        cfg.apply_and_commit()
    