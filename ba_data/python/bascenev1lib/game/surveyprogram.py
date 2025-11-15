# Released under the MIT License. See LICENSE for details.
#
"""Setup for 'first timer's."""

from __future__ import annotations

from typing import TYPE_CHECKING, override, cast
import logging

import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor.cutsceneplayer import CutscenePlayerSpecialEditionCuzFucked
import babase as ba

if TYPE_CHECKING:
    from typing import Callable
    
    
class SURVEYWindow(bui.MainWindow):
    """For selecting your options."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('SURVEYWindow')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 670
        self._r = 'SURVEYWindow'

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
        self.titletext = bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,)
        self.choosename = bui.textwidget(
            parent=self._root_widget,
            text='It\'s your first time around here. \nBefore we move on..\nChoose (YOUR) space marine\'s name.',
            position=(250, height - 220),
            maxwidth=400,
            size=(300, 200),
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
        )
        self.charactertex = bui.imagewidget(
            parent=self._root_widget,
            position=(300, height - 380),
            size=(220, 220),
            texture=bui.gettexture('spazbound'),
            color=(1, 1, 1),
        )
        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(150, height - 500),
            autoselect=True,
            size=(width - 270, 55),
            v_align='center',
            editable=True,
            maxwidth=width - 175,
        )
        self.btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(370, height - 600),
            size=(80, 70),
            autoselect=True,
            enable_sound=False,
            label='OK',
            on_activate_call=self.closeit,
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
            
    def closeit(self):
        self.changename()
        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            SURVEYWindow2(origin_widget=self._root_widget)
        )
        bui.getsound('okdesuka').play()
    def changename(self) -> None:
        cfg = bui.app.config
        cfg['playername'] = cast(str,
            bui.textwidget(query=self._text_field),
        ),
        cfg.apply_and_commit()
        
class SURVEYWindow2(bui.MainWindow):
    """For selecting your options."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('SURVEYWindow')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 670
        self._r = 'SURVEYWindow'

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
        self.titletext = bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,)
        self.choosename = bui.textwidget(
            parent=self._root_widget,
            text='Now, name this knight.',
            position=(250, height - 200),
            maxwidth=400,
            size=(300, 200),
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
        )
        self.charactertex = bui.imagewidget(
            parent=self._root_widget,
            position=(300, height - 380),
            size=(220, 220),
            texture=bui.gettexture('krisbound'),
            color=(1, 1, 1),
        )
        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(150, height - 500),
            autoselect=True,
            size=(width - 270, 55),
            v_align='center',
            editable=True,
            maxwidth=width - 175,
        )
        self.btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(370, height - 600),
            size=(80, 70),
            autoselect=True,
            enable_sound=False,
            label='OK',
            on_activate_call=self.closeit,
        )
        
    def get_main_window_state(self):
        # Return empty objects, because why would we save
        # a window's state if we're not gonna go back??
        return DummyWindowState()
            
    def closeit(self):
        self.changename()
        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            SURVEYWindow3(origin_widget=self._root_widget)
        )
        bui.getsound('okdesuka').play()
        
    def changename(self) -> None:
        cfg = bui.app.config
        cfg['character1name'] = cast(str,
            bui.textwidget(query=self._text_field),
        ),
        cfg.apply_and_commit()
        
class SURVEYWindow3(bui.MainWindow):
    """For selecting your options."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('SURVEYWindow')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 670
        self._r = 'SURVEYWindow'

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
        self.titletext = bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,)
        self.choosename = bui.textwidget(
            parent=self._root_widget,
            text='Name the ninja.',
            position=(250, height - 200),
            maxwidth=400,
            size=(300, 200),
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
        )
        self.charactertex = bui.imagewidget(
            parent=self._root_widget,
            position=(300, height - 380),
            size=(220, 220),
            texture=bui.gettexture('snakebound'),
            color=(1, 1, 1),
        )
        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(150, height - 500),
            autoselect=True,
            size=(width - 270, 55),
            v_align='center',
            editable=True,
            maxwidth=width - 175,
        )
        self.btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(370, height - 600),
            size=(80, 70),
            autoselect=True,
            enable_sound=False,
            label='OK',
            on_activate_call=self.closeit,
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
            
    def closeit(self):
        self.changename()
        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            SURVEYWindow4(origin_widget=self._root_widget)
        )
        bui.getsound('okdesuka').play()
        
    def changename(self) -> None:
        cfg = bui.app.config
        cfg['character2name'] = cast(str,
            bui.textwidget(query=self._text_field),
        ),
        cfg.apply_and_commit()
        
class SURVEYWindow4(bui.MainWindow):
    """For selecting your options."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('SURVEYWindow')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 670
        self._r = 'SURVEYWindow'

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
        self.titletext = bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,)
        self.choosename = bui.textwidget(
            parent=self._root_widget,
            text='And finally, choose the \nlast yellow one\'s name.',
            position=(250, height - 200),
            maxwidth=400,
            size=(300, 200),
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
        )
        self.charactertex = bui.imagewidget(
            parent=self._root_widget,
            position=(300, height - 380),
            size=(220, 220),
            texture=bui.gettexture('noobbound'),
            color=(1, 1, 1),
        )
        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(150, height - 500),
            autoselect=True,
            size=(width - 270, 55),
            v_align='center',
            editable=True,
            maxwidth=width - 175,
        )
        self.btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(370, height - 600),
            size=(80, 70),
            autoselect=True,
            enable_sound = False,
            label='OK',
            on_activate_call=self.closeit,
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
            
    def closeit(self):
        self.changename()
        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            SURVEYWindow5(origin_widget=self._root_widget)
        )
        bui.getsound('okdesuka').play()
        
    def changename(self) -> None:
        cfg = bui.app.config
        cfg['character3name'] = cast(str,
            bui.textwidget(query=self._text_field),
        ),
        cfg.apply_and_commit()

class SURVEYWindow5(bui.MainWindow):
    """For selecting your options."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('SURVEYWindow')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 350
        self._r = 'SURVEYWindow'

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
        self.titletext = bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,)
        self.choosename = bui.textwidget(
            parent=self._root_widget,
            text='Now, please select your settings.',
            position=(250, height - 200),
            maxwidth=400,
            size=(300, 200),
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
        )
        self.btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(350, height - 250),
            size=(80, 70),
            autoselect=True,
            label='OK',
            on_activate_call=self.closeit,
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
            
    def closeit(self):
        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            ALTBombSqudaSettings(origin_widget=self._root_widget)
        )
         
        
class ALTBombSqudaSettings(bui.MainWindow):
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
        thefuckedupuifix = 220
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
            text='Make my Spaz have a weird texture',
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
            text='Make the gameplay too loud',
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
            text='Make every powerup the random-based one',
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
            text='Make me die even with one hit',
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
            text='Make me parry whenever i want',
            on_value_change_call=self.changeparry
        )
        self._shutdownprevention = bui.checkboxwidget(
            parent=self._root_widget,
            position=(250, 50 + thefuckedupuifix),
            size=(180, 40),
            autoselect=False,
            maxwidth=300,
            textcolor=(1.0, 1.0, 1.0),
            value=bui.app.config.get("dontshutdown", False),
            text='Do not shutdown my device',
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
            text='Do not delay upon attempting to quit the game',
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
            text='Show people on Discord if i\'m playing',
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
            text='Enable the EarthBound Stat Meter',
            on_value_change_call=self.changemeter
        )
        self.choosename = bui.textwidget(
            parent=self._root_widget,
            text='You may always change these \nlater down the line.',
            position=(250, height - 80),
            maxwidth=400,
            size=(300, 200),
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
        )
        self.btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(370, height - 700),
            size=(80, 70),
            autoselect=True,
            label='OK',
            on_activate_call=self.closeit,
        )
        
    def closeit(self):
        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            SURVEYWindow6(origin_widget=self._root_widget)
        )

    def changehardmode(self, val: str) -> None:
        cfg = bui.app.config
        cfg['spazhardmode'] = val
        cfg.apply_and_commit()
        
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
        
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
        
class SURVEYWindow6(bui.MainWindow):
    """For selecting your options."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('SURVEYWindow')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 350
        self._r = 'SURVEYWindow'

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
        self.titletext = bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,)
        self.choosename = bui.textwidget(
            parent=self._root_widget,
            text='Do you acknowledge the possibility\nof not enjoying this experience?',
            position=(250, height - 200),
            maxwidth=400,
            size=(300, 200),
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
        )
        self.btn1 = bui.buttonwidget(
            parent=self._root_widget,
            position=(250, height - 250),
            size=(80, 70),
            autoselect=False,
            label='NO',
            on_activate_call=self.closeit,
        )
        self.btn2 = bui.buttonwidget(
            parent=self._root_widget,
            position=(350, height - 250),
            size=(80, 70),
            autoselect=True,
            label='YES',
            on_activate_call=self.closeit,
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
            
    def closeit(self):
        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            SURVEYWindow7(origin_widget=self._root_widget)
        )
class SURVEYWindow7(bui.MainWindow):
    """For selecting your options."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('SURVEYWindow')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 350
        self._r = 'SURVEYWindow'

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
        self.titletext = bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,)
        self.choosename = bui.textwidget(
            parent=self._root_widget,
            text='Good. Very good. Your answers \nshall be recorded.\nDo you want to move on?',
            position=(250, height - 200),
            maxwidth=400,
            size=(300, 200),
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
        )
        self.btn4 = bui.buttonwidget(
            parent=self._root_widget,
            position=(250, height - 250),
            size=(80, 70),
            autoselect=False,
            label='NO',
            on_activate_call=ba.quit,
        )
        self.btn4 = bui.buttonwidget(
            parent=self._root_widget,
            position=(350, height - 250),
            size=(80, 70),
            autoselect=True,
            label='YES',
            on_activate_call=self.closeit,
        )
    def closeit(self):
        bs.pushcall(lambda: bs.new_host_session(SurveySessionThing2))
        
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
            
        
class SURVEYActivity(bs.Activity[bs.Player, bs.Team]):
    """Activity showing the rotating main menu bg stuff."""
    _stdassets = bs.Dependency(bs.AssetPackage, 'stdassets@1')


    def __init__(self, settings: dict):
        super().__init__(settings)
        
        with bs.ContextRef.empty():
            bui.app.ui_v1.set_main_window(
                SURVEYWindow(),
                is_top_level=True,
                suppress_warning=True,
            )
    def on_transition_in(self) -> None:
        bs.setmusic(bs.MusicType.SURVEY)
        self.bgterrain = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('thePadBG'),
                    'color': (0.1, 0.1, 0.9),
                    'lighting': False,
                    'background': True,
                    'color_texture': bs.gettexture('menuBG'),
                },
            )
        )
        self.blackthing = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('white2'),
                'absolute_scale': True,
                'position': (0, 0),
                'attach': 'center',
                'opacity': 0.0,
                'fill_screen': True,
                'color': (0, 0, 0)
            }
        )

class SurveySessionThing(bs.Session):
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.setactivity(bs.newactivity(SURVEYActivity))
    @override
    def on_player_request(self, player: bs.SessionPlayer) -> bool:
        # Reject all player requests.
        return False
        
class SurveySessionThing2(bs.Session):
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.setactivity(bs.newactivity(SURVEYActivity2))
    @override
    def on_player_request(self, player: bs.SessionPlayer) -> bool:
        # Reject all player requests.
        return False
        
class SURVEYActivity2(bs.Activity[bs.Player, bs.Team]):
    """Activity showing the rotating main menu bg stuff."""
    _stdassets = bs.Dependency(bs.AssetPackage, 'stdassets@1')


    def __init__(self, settings: dict):
        super().__init__(settings)
        
    def on_transition_in(self) -> None:
        from bascenev1lib.mainmenu import MainMenuSession
        self.bgterrain = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('thePadBG'),
                    'color': (0.1, 0.1, 0.9),
                    'lighting': False,
                    'background': True,
                    'color_texture': bs.gettexture('menuBG'),
                },
            )
        )
        self.blackthing = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('white2'),
                'absolute_scale': True,
                'position': (0, 0),
                'attach': 'center',
                'opacity': 0.0,
                'fill_screen': True,
                'color': (0, 0, 0)
            }
        )
        bs.setmusic(None)
        bs.animate(self.blackthing, "opacity", {
            0.0: (0.0),
            1.5: (1.0)
        })
        bui.app.config['playersfirsttime'] = False
        bui.app.config.apply_and_commit()
        bs.timer(2.5, lambda: bs.setmusic(bs.MusicType.LOGOTYPE))
        bs.timer(2.5, lambda: CutscenePlayerSpecialEditionCuzFucked(
            cutscene_id=41,
            frame_delays=[
            2.2, 0.3, 0.3, 0.3, 0.3, 0.3,
            0.3, 0.3, 0.2, 0.2, 0.1, 
            0.1, 0.1, 0.1, 0.1, 0.1,
            0.1, 0.1, 0.1, 0.1, 0.1,
            0.1, 0.1, 0.1, 0.1, 21.2,
            ],
            fade_duration=2.0
        )
        )
        bs.timer(36.0, lambda: bs.pushcall(lambda: bs.new_host_session(MainMenuSession)))