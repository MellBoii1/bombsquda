# Released under the MIT License. See LICENSE for details.
#
"""Provides help related ui."""

from __future__ import annotations

from typing import override

import bauiv1 as bui
import babase as ba
import random

class InventoryWindow(bui.MainWindow):
    """Shows what you got."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 1400 if uiscale is bui.UIScale.SMALL else 450
        self._height = (
            1200
            if uiscale is bui.UIScale.SMALL else 400
        )
        # xoffs = 70 if uiscale is bui.UIScale.SMALL else 0
        # yoffs = -45 if uiscale is bui.UIScale.SMALL else 0

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.55
            if uiscale is bui.UIScale.SMALL
            else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
        )

        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(self._width - 60, screensize[0] / scale)
        target_height = min(self._height - 100, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 100.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_minimal' if uiscale is bui.UIScale.SMALL else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                yoffs - (150 if uiscale is bui.UIScale.SMALL else 80),
            ),
            size=(0, 0),
            text=bui.Lstr(resource='inventoryText'),
            color=bui.app.ui_v1.title_color,
            scale=0.9 if uiscale is bui.UIScale.SMALL else 1.0,
            maxwidth=(130 if uiscale is bui.UIScale.SMALL else 200),
            h_align='center',
            v_align='center',
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(50, yoffs - 100),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        button_width = 300
        imgsize = 60
        xoffs = 20
        image_mult = 0.4
        text_mult = 0.55
        otherxoffs = -10
        if uiscale is bui.UIScale.SMALL:
            yoffs -= 70
            image_mult += 0.1
            otherxoffs = -50
        yoffs += 20
        self._player_profiles_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.5 - button_width * 0.5, yoffs - 200),
            autoselect=True,
            size=(button_width, 60),
            label=bui.Lstr(resource='playerProfilesWindow.titleText'),
            color=(0.55, 0.5, 0.6),
            icon=bui.gettexture('cuteSpaz'),
            textcolor=(0.75, 0.7, 0.8),
            on_activate_call=self._player_profiles_press,
        )
        bui.imagewidget(
            parent=self._root_widget,
            position=(self._width * image_mult - xoffs + otherxoffs, yoffs - 265),
            size=(imgsize, imgsize),
            texture=bui.gettexture('spaztickets'),
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * text_mult - xoffs + otherxoffs, yoffs - 250),
            size=(300, 30),
            text=str(ba.app.config.get("squda_spaztix")),
            scale=1.0,
            maxwidth=self._width * 0.9,
            h_align='left',
            v_align='center',
        )
        yoffs -= 70
        bui.imagewidget(
            parent=self._root_widget,
            position=(self._width * image_mult - xoffs + otherxoffs, yoffs - 265),
            size=(imgsize, imgsize),
            texture=bui.gettexture('spaztokens'),
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * text_mult - xoffs + otherxoffs, yoffs - 250),
            size=(300, 30),
            text=str(ba.app.config.get("squda_spaztokens")),
            scale=1.0,
            maxwidth=self._width * 0.9,
            h_align='left',
            v_align='center',
        )
        yoffs -= 30
        xoffset = 0
        if uiscale is bui.UIScale.SMALL:
            xoffset = 130
            button_width = 500
        bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.7 - button_width * 0.5 - xoffset, yoffs - 270),
            autoselect=False,
            size=(button_width, 80),
            scale=0.4,
            text_scale=1.6,
            label=bui.Lstr(resource='whatIsThisText'),
            color=(0.55, 0.5, 0.6),
            textcolor=(0.75, 0.7, 0.8),
            on_activate_call=self.show_what_dis,
        )
        yoffs -= 40
        bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.7 - button_width * 0.5 - xoffset, yoffs - 270),
            autoselect=False,
            size=(button_width, 80),
            scale=0.4,
            text_scale=1.6,
            label=bui.Lstr(resource='transferText'),
            color=(0.55, 0.5, 0.6),
            textcolor=(0.75, 0.7, 0.8),
            on_activate_call=self._open_transfer,
        )
        yoffs -= 40
        bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.7 - button_width * 0.5 - xoffset, yoffs - 270),
            autoselect=False,
            size=(button_width, 80),
            scale=0.4,
            text_scale=1.6,
            label=bui.Lstr(resource='getTicketsText'),
            color=(0.55, 0.5, 0.6),
            textcolor=(0.75, 0.7, 0.8),
            on_activate_call=self._open_get_tickets,
        )

    def _player_profiles_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.profile.browser import ProfileBrowserWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self.main_window_replace(
            ProfileBrowserWindow(origin_widget=self._player_profiles_button)
        )
    
    def show_what_dis(self):
        if not self._root_widget or self._root_widget.transitioning_out:
            return
            
        from bauiv1lib.mell_about import MellInfoWindow
        MellInfoWindow(
            titletext=ba.Lstr(resource='aboutCustomCurrencyTitle'),
            bodytext=ba.Lstr(resource='aboutCustomCurrency'),
        )
        
    def _open_transfer(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.transfer import TransferWindow
        import mellboii.mell_resources as mell
        
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
        if ba.app.config.get('squda_noonline'):
            bui.screenmessage(bui.Lstr(resource='noOnlineError'), color=(1, 0, 0))
            bui.getsound('error').play()
            return
        bui.getsound('quickcon').play()
        if not mell.get_currency('tickets'):
            bui.screenmessage(bui.Lstr(resource='transferError2'), color=(1, 0, 0))
            bui.getsound('error').play()
            return
        self.main_window_replace(TransferWindow(origin_widget=self._root_widget))
    
    def _open_get_tickets(self) -> None:
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
        self.main_window_replace(GetSTicketsWindow(origin_widget=self._root_widget))

        
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

class GetSTicketsWindow(bui.MainWindow):
    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 1400 if uiscale is bui.UIScale.SMALL else 700
        self._height = (
            1200
            if uiscale is bui.UIScale.SMALL else 420
        )
        # xoffs = 70 if uiscale is bui.UIScale.SMALL else 0
        # yoffs = -45 if uiscale is bui.UIScale.SMALL else 0

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.55
            if uiscale is bui.UIScale.SMALL
            else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        self._r = 'getTicketsWindow'

        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(self._width - 60, screensize[0] / scale)
        target_height = min(self._height - 100, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 100.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_minimal' if uiscale is bui.UIScale.SMALL else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                yoffs - (150 if uiscale is bui.UIScale.SMALL else 100),
            ),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            scale=0.9 if uiscale is bui.UIScale.SMALL else 1.0,
            maxwidth=(130 if uiscale is bui.UIScale.SMALL else 200),
            h_align='center',
            v_align='center',
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(50, yoffs - 100),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        button_width = 200
        imgsize = 60
        xoffs = 20
        if uiscale is bui.UIScale.SMALL:
            yoffs -= 70
            otherxoffs = -50
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, yoffs - 130),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.explainText'),
            color=bui.app.ui_v1.title_color,
            scale=0.6 if uiscale is bui.UIScale.SMALL else 0.7,
            h_align='center',
            v_align='top',
        )
        yoffs -= 70
        bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.5 - button_width * 0.5, yoffs - 200),
            autoselect=True,
            size=(button_width, 60),
            label=bui.Lstr(resource=f'{self._r}.spazClicker'),
            color=(0.55, 0.5, 0.6),
            textcolor=(0.75, 0.7, 0.8),
            on_activate_call=self._spaz_clicker_pressed,
        )
    
    def _spaz_clicker_pressed(self):
        # from bauiv1lib.spazclicker import SpazClickerWindow
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
        self.main_window_replace(SpazClickerWindow(origin_widget=self._root_widget))
    
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

# when this gets bigger move to another script
class SpazClickerWindow(bui.MainWindow):
    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 1400 if uiscale is bui.UIScale.SMALL else 600
        self._height = (
            1200
            if uiscale is bui.UIScale.SMALL else 400
        )

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.55
            if uiscale is bui.UIScale.SMALL
            else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        self._r = 'clickerWindow'

        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(self._width - 60, screensize[0] / scale)
        target_height = min(self._height - 100, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 100.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_minimal' if uiscale is bui.UIScale.SMALL else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )
        self._texture = 'earthbound/spazbound'
        self._clicks = 0
        self.sounds = ['diagvoice/spaz']

        bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                yoffs - (150 if uiscale is bui.UIScale.SMALL else 100),
            ),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            scale=0.9 if uiscale is bui.UIScale.SMALL else 1.0,
            maxwidth=(130 if uiscale is bui.UIScale.SMALL else 200),
            h_align='center',
            v_align='center',
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(50, yoffs - 100),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        xoffs = 0
        scale = 1.0
        if uiscale is bui.UIScale.SMALL:
            yoffs -= 90
            scale = 1.5
            xoffs = 50
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, yoffs - (100 if uiscale is bui.UIScale.SMALL else 130)),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.explainText'),
            color=bui.app.ui_v1.title_color,
            scale=0.6 if uiscale is bui.UIScale.SMALL else 0.7,
            h_align='center',
            v_align='top',
        )
        yoffs -= 150
        pos = (self._width * 0.38 + xoffs, yoffs - 200)
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=pos,
            autoselect=True,
            size=(150 * scale, 150 * scale),
            button_type='square',
            label='',
            on_activate_call=self._click,
            enable_sound=False
        )
        bui.imagewidget(
            parent=self._root_widget,
            position=(pos[0] + 15 * scale, pos[1] + 15 * scale),
            size=(120 * scale, 120 * scale),
            texture=bui.gettexture(self._texture),
            draw_controller=btn,
        )
    
    def _gain_ticket(self):
        amount = 1
        key = 'squda_spaztix'
        ba.app.config[key] = ba.app.config.get(key, 0) + amount
        bui.getsound('gainCur').play()
    
    def _click(self):
        if self._clicks >= 7:
            self._gain_ticket()
            self._clicks = 0
        bui.getsound(random.choice(self.sounds)).play()
        self._clicks += 1
    
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
