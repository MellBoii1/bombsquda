# Released under the MIT License. See LICENSE for details.
#
"""Provides the top level play window."""

from __future__ import annotations

import logging
from typing import override, TYPE_CHECKING

import bascenev1 as bs
import bauiv1 as bui
import bascenev1lib.mainmenu as mainmenu
import babase as ba

if TYPE_CHECKING:
    from bauiv1 import MainWindowState


class PlaylistSelectContext:
    """For using PlayWindow to select a playlist instead of running game."""

    back_state: MainWindowState | None = None

class PlayWindow(bui.MainWindow):
    """Window for selecting overall play type."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        playlist_select_context: PlaylistSelectContext | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        import bacommon.cloud

        # TEMP TESTING
        if bool(False):
            print('HELLO FROM TEST')
            plus = bui.app.plus
            assert plus is not None
            plus.cloud.send_message_cb(
                bacommon.cloud.SecureDataCheckMessage(
                    data=b'fo', signature=b'mo'
                ),
                on_response=lambda r: print('GOT CHECK RESPONSE', r),
            )
            plus.cloud.send_message_cb(
                bacommon.cloud.SecureDataCheckerRequest(),
                on_response=lambda r: print('GOT CHECKER RESPONSE', r),
            )

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        bui.app.threadpool.submit_no_wait(self._preload_modules)

        classic = bui.app.classic
        assert classic is not None

        self._playlist_select_context = playlist_select_context

        uiscale = bui.app.ui_v1.uiscale
        width = 1300 if uiscale is bui.UIScale.SMALL else 1000
        height = 1000 if uiscale is bui.UIScale.SMALL else 550

        button_width = 400.0
        button_height = 360.0
        button_spacing = 3.0

        if origin_widget is not None:

            # Need to store this ourself since we can function as a
            # non-main window.
            self._transition_out = 'out_scale'
        else:
            self._transition_out = 'out_right'

        self._r = 'playWindow'
        self.dialog = 0

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        safesize = bui.get_virtual_safe_area_size()

        # We're a generally widescreen shaped window, so bump our
        # overall scale up a bit when screen width is wider than safe
        # bounds to take advantage of the extra space.
        smallscale = min(1.6, 1.35 * screensize[0] / safesize[0])

        scale = (
            smallscale
            if uiscale is bui.UIScale.SMALL
            else 0.9 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_height = min(height - 80, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_full'
                    if playlist_select_context is None
                    else 'menu_minimal'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        self._back_button: bui.Widget | None
        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget,
                on_cancel_call=self.main_window_back,
            )
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(50, yoffs - 100),
                size=(60, 60),
                scale=1.1,
                text_res_scale=1.5,
                text_scale=1.2,
                autoselect=True,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                width * 0.5,
                yoffs - (50 if uiscale is bui.UIScale.SMALL else 70),
            ),
            size=(0, 0),
            text=bui.Lstr(
                resource=(
                    (f'{self._r}.titleText')
                    if self._playlist_select_context is None
                    else 'playlistsText'
                )
            ),
            scale=1.2 if uiscale is bui.UIScale.SMALL else 1.7,
            res_scale=2.0,
            maxwidth=250,
            color=bui.app.ui_v1.heading_color,
            h_align='center',
            v_align='center',
        )

        scl = 0.75 if self._playlist_select_context is None else 0.68
        v = height * 0.5 - button_height * scl * 0.5 - 20.0
        clr = (0.6, 0.7, 0.6, 1.0)

        bcount = 3 if self._playlist_select_context is None else 2

        total_b_width = (
            bcount * button_width * scl + (bcount - 1) * button_spacing
        )
        hoffs = (width - total_b_width) * 0.5

        self._lineup_tex = bui.gettexture('playerLineup')
        angry_computer_transparent_mesh = bui.getmesh(
            'angryComputerTransparent'
        )
        self._lineup_1_transparent_mesh = bui.getmesh(
            'playerLineup1Transparent'
        )
        self._lineup_2_transparent_mesh = bui.getmesh(
            'playerLineup2Transparent'
        )
        self._lineup_3_transparent_mesh = bui.getmesh(
            'playerLineup3Transparent'
        )
        self._lineup_4_transparent_mesh = bui.getmesh(
            'playerLineup4Transparent'
        )
        self._eyes_mesh = bui.getmesh('plasticEyesTransparent')

        self._coop_button: bui.Widget | None = None

        # Only show coop button in regular variant.
        if self._playlist_select_context is None:
            self._coop_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(hoffs, v),
                size=(
                    scl * button_width,
                    scl * button_height,
                ),
                extra_touch_border_scale=0.1,
                autoselect=True,
                label='',
                button_type='square',
                on_activate_call=self._coop,
            )

            if uiscale is bui.UIScale.SMALL:
                bui.widget(
                    edit=btn,
                    left_widget=bui.get_special_widget('back_button'),
                )
                bui.widget(
                    edit=btn,
                    up_widget=bui.get_special_widget('account_button'),
                )
                bui.widget(
                    edit=btn,
                    down_widget=bui.get_special_widget('settings_button'),
                )

            self._draw_dude(
                0,
                btn,
                hoffs,
                v,
                scl,
                position=(140, 30),
                color=(0.72, 0.4, 1.0),
            )
            self._draw_dude(
                1,
                btn,
                hoffs,
                v,
                scl,
                position=(185, 53),
                color=(0.71, 0.5, 1.0),
            )
            self._draw_dude(
                2,
                btn,
                hoffs,
                v,
                scl,
                position=(220, 27),
                color=(0.67, 0.44, 1.0),
            )
            self._draw_dude(
                3, btn, hoffs, v, scl, position=(255, 57), color=(0.7, 0.3, 1.0)
            )
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(hoffs + scl * 230, v + scl * 153),
                size=(scl * 115, scl * 115),
                texture=self._lineup_tex,
                mesh_transparent=angry_computer_transparent_mesh,
            )

            bui.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(hoffs + scl * (-10), v + scl * 95),
                size=(scl * button_width, scl * 50),
                text=bui.Lstr(
                    resource='playModes.singlePlayerCoopText',
                    fallback_resource='playModes.coopText',
                ),
                maxwidth=scl * button_width * 0.7,
                res_scale=1.5,
                h_align='center',
                v_align='center',
                color=(0.7, 0.9, 0.7, 1.0),
                scale=scl * 1.5,
            )

            bui.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(hoffs + scl * (-10), v + (scl * 54)),
                size=(scl * button_width, scl * 30),
                text=bui.Lstr(resource=f'{self._r}.oneToFourPlayersText'),
                h_align='center',
                v_align='center',
                scale=0.83 * scl,
                flatness=1.0,
                maxwidth=scl * button_width * 0.7,
                color=clr,
            )

            hoffs += scl * button_width + button_spacing

        self._teams_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(hoffs, v),
            size=(
                scl * button_width,
                scl * button_height,
            ),
            extra_touch_border_scale=0.1,
            autoselect=True,
            label='',
            button_type='square',
            on_activate_call=self._team_tourney,
        )

        xxx = -14
        self._draw_dude(
            2,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 148, 30),
            color=(0.2, 0.4, 1.0),
        )
        self._draw_dude(
            3,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 181, 53),
            color=(0.3, 0.4, 1.0),
        )
        self._draw_dude(
            1,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 216, 33),
            color=(0.3, 0.5, 1.0),
        )
        self._draw_dude(
            0,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 245, 57),
            color=(0.3, 0.5, 1.0),
        )

        xxx = 155
        self._draw_dude(
            0,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 151, 30),
            color=(1.0, 0.5, 0.4),
        )
        self._draw_dude(
            1,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 189, 53),
            color=(1.0, 0.58, 0.58),
        )
        self._draw_dude(
            3,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 223, 27),
            color=(1.0, 0.5, 0.5),
        )
        self._draw_dude(
            2,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 257, 57),
            color=(1.0, 0.5, 0.5),
        )

        bui.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            position=(hoffs + scl * (-10), v + scl * 95),
            size=(scl * button_width, scl * 50),
            text=bui.Lstr(
                resource='playModes.teamsText', fallback_resource='teamsText'
            ),
            res_scale=1.5,
            maxwidth=scl * button_width * 0.7,
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
            scale=scl * 1.5,
        )
        bui.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            position=(hoffs + scl * (-10), v + (scl * 54)),
            size=(scl * button_width, scl * 30),
            text=bui.Lstr(resource=f'{self._r}.twoToEightPlayersText'),
            h_align='center',
            v_align='center',
            res_scale=1.5,
            scale=0.83 * scl,
            flatness=1.0,
            maxwidth=scl * button_width * 0.7,
            color=clr,
        )

        hoffs += scl * button_width + button_spacing
        self._free_for_all_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(hoffs, v),
            size=(scl * button_width, scl * button_height),
            extra_touch_border_scale=0.1,
            autoselect=True,
            label='',
            button_type='square',
            on_activate_call=self._free_for_all,
        )

        xxx = -5
        self._draw_dude(
            0,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 140, 30),
            color=(0.4, 1.0, 0.4),
        )
        self._draw_dude(
            3,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 185, 53),
            color=(1.0, 0.4, 0.5),
        )
        self._draw_dude(
            1,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 220, 27),
            color=(0.4, 0.5, 1.0),
        )
        self._draw_dude(
            2,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 255, 57),
            color=(0.5, 1.0, 0.4),
        )
        xxx = 140
        self._draw_dude(
            2,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 148, 30),
            color=(1.0, 0.9, 0.4),
        )
        self._draw_dude(
            0,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 182, 53),
            color=(0.7, 1.0, 0.5),
        )
        self._draw_dude(
            3,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 233, 27),
            color=(0.7, 0.5, 0.9),
        )
        self._draw_dude(
            1,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 266, 53),
            color=(0.4, 0.5, 0.8),
        )
        bui.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            position=(hoffs + scl * (-10), v + scl * 95),
            size=(scl * button_width, scl * 50),
            text=bui.Lstr(
                resource='playModes.freeForAllText',
                fallback_resource='freeForAllText',
            ),
            maxwidth=scl * button_width * 0.7,
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
            scale=scl * 1.5,
        )
        bui.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            position=(hoffs + scl * (-10), v + (scl * 54)),
            size=(scl * button_width, scl * 30),
            text=bui.Lstr(resource=f'{self._r}.twoToEightPlayersText'),
            h_align='center',
            v_align='center',
            scale=0.83 * scl,
            flatness=1.0,
            maxwidth=scl * button_width * 0.7,
            color=clr,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget,
                selected_child=(
                    self._coop_button
                    if self._playlist_select_context is None
                    else self._teams_button
                ),
            )
        else:
            bui.containerwidget(
                edit=self._root_widget,
                selected_child=(
                    self._coop_button
                    if self._playlist_select_context is None
                    else self._teams_button
                ),
            )

        self._restore_state()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull any values out of self here; if we do it in the lambda
        # we'll keep our window alive inadvertantly.
        playlist_select_context = self._playlist_select_context
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                playlist_select_context=playlist_select_context,
            )
        )

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use; avoids hitches (called in bg thread)."""
        import bauiv1lib.mainmenu as _unused1
        import bauiv1lib.account as _unused2
        import bauiv1lib.coop.browser as _unused3
        import bauiv1lib.playlist.browser as _unused4

    def _coop(self) -> None:
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
            
        # Show the submenu instead of jumping directly to browser
        if ba.app.config.get("canopencredits", True):
            self.dialog += 1
            if self.dialog == 1:    
                ba.screenmessage('I\'m not going there again.', color=(0.5, 0.25, 1.0))
                bui.getsound('spazAttack04').play()
            elif self.dialog == 2:
                ba.screenmessage('No seriously. I\'m not gonna go there.', color=(0.5, 0.25, 1.0))
                bui.getsound('spazAttack03').play()
            elif self.dialog == 3:
                ba.screenmessage('Why the hell do you wanna go back there anyways??', color=(0.5, 0.25, 1.0))
                bui.getsound('spazImpact02').play()
            elif self.dialog == 4:
                ba.screenmessage('Okay FINE. I\'ll go check if there\'s anyone there.\nAtleast so you\'ll stop fuckin\' bothering me.', color=(0.5, 0.25, 1.0))
                bui.getsound('spazImpact04').play()
                ba.apptimer(3.0, lambda: ba.screenmessage('..okay yeah they\'re DEFINETLY still there.', color=(0.5, 0.25, 1.0)))
                ba.apptimer(3.0, lambda: bui.getsound('spazImpact03').play())
                ba.apptimer(3.2, lambda: bui.getsound('recordscratch').play())
                ba.apptimer(3.2, lambda: bs.setmusic(None))
                ba.apptimer(5.5, lambda: ba.screenmessage('Well, guess I\'ll have to go there.\n AGAIN.', color=(0.5, 0.25, 1.0)))
                ba.apptimer(5.5, lambda: bui.getsound('spazAttack02').play())
                ba.apptimer(7.7, lambda: self.main_window_replace(CoopSubMenu(origin_widget=self._coop_button,nobackout=True)))
                ba.apptimer(7.7, lambda: bui.getsound('swish').play())
                ba.apptimer(8.4, lambda: bs.setmusic(bs.MusicType.MENU))
                ba.apptimer(8.5, lambda: ba.screenmessage('You re-unlocked Co-op.'))
                ba.apptimer(8.5, lambda: bui.getsound('ding').play())
                ba.app.config['canopencredits'] = False
                ba.app.config.commit()
            else:
                raise TypeError(f'Dialog number is {self.dialog}; it should ONLY be 5 and not above.\nWhat the fuck are you doing?')
        else:    
            self.main_window_replace(
                CoopSubMenu(
                    origin_widget=self._coop_button,
                )
            )

    def _team_tourney(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.playlist.browser import PlaylistBrowserWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            PlaylistBrowserWindow(
                origin_widget=self._teams_button,
                sessiontype=bs.DualTeamSession,
                playlist_select_context=self._playlist_select_context,
            )
        )

    def _free_for_all(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.playlist.browser import PlaylistBrowserWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            PlaylistBrowserWindow(
                origin_widget=self._free_for_all_button,
                sessiontype=bs.FreeForAllSession,
                playlist_select_context=self._playlist_select_context,
            )
        )

    def _draw_dude(
        self,
        i: int,
        btn: bui.Widget,
        hoffs: float,
        v: float,
        scl: float,
        position: tuple[float, float],
        color: tuple[float, float, float],
    ) -> None:
        # pylint: disable=too-many-positional-arguments
        h_extra = -100
        v_extra = 130
        eye_color = (
            0.7 * 1.0 + 0.3 * color[0],
            0.7 * 1.0 + 0.3 * color[1],
            0.7 * 1.0 + 0.3 * color[2],
        )
        if i == 0:
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0]),
                    v + scl * (v_extra + position[1]),
                ),
                size=(scl * 60, scl * 80),
                color=color,
                texture=self._lineup_tex,
                mesh_transparent=self._lineup_1_transparent_mesh,
            )
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0] + 12),
                    v + scl * (v_extra + position[1] + 53),
                ),
                size=(scl * 36, scl * 18),
                texture=self._lineup_tex,
                color=eye_color,
                mesh_transparent=self._eyes_mesh,
            )
        elif i == 1:
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0]),
                    v + scl * (v_extra + position[1]),
                ),
                size=(scl * 45, scl * 90),
                color=color,
                texture=self._lineup_tex,
                mesh_transparent=self._lineup_2_transparent_mesh,
            )
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0] + 5),
                    v + scl * (v_extra + position[1] + 67),
                ),
                size=(scl * 32, scl * 16),
                texture=self._lineup_tex,
                color=eye_color,
                mesh_transparent=self._eyes_mesh,
            )
        elif i == 2:
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0]),
                    v + scl * (v_extra + position[1]),
                ),
                size=(scl * 45, scl * 90),
                color=color,
                texture=self._lineup_tex,
                mesh_transparent=self._lineup_3_transparent_mesh,
            )
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0] + 5),
                    v + scl * (v_extra + position[1] + 59),
                ),
                size=(scl * 34, scl * 17),
                texture=self._lineup_tex,
                color=eye_color,
                mesh_transparent=self._eyes_mesh,
            )
        elif i == 3:
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0]),
                    v + scl * (v_extra + position[1]),
                ),
                size=(scl * 48, scl * 96),
                color=color,
                texture=self._lineup_tex,
                mesh_transparent=self._lineup_4_transparent_mesh,
            )
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0] + 2),
                    v + scl * (v_extra + position[1] + 62),
                ),
                size=(scl * 38, scl * 19),
                texture=self._lineup_tex,
                color=eye_color,
                mesh_transparent=self._eyes_mesh,
            )

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._teams_button:
                sel_name = 'Team Games'
            elif self._coop_button is not None and sel == self._coop_button:
                sel_name = 'Co-op Games'
            elif sel == self._free_for_all_button:
                sel_name = 'Free-for-All Games'
            elif sel == self._back_button:
                sel_name = 'Back'
            else:
                raise ValueError(f'unrecognized selection {sel}')
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = sel_name
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self))
            if sel_name == 'Team Games':
                sel = self._teams_button
            elif sel_name == 'Co-op Games' and self._coop_button is not None:
                sel = self._coop_button
            elif sel_name == 'Free-for-All Games':
                sel = self._free_for_all_button
            elif sel_name == 'Back' and self._back_button is not None:
                sel = self._back_button
            else:
                sel = (
                    self._coop_button
                    if self._coop_button is not None
                    else self._teams_button
                )
            bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)
            
class CoopSubMenu(bui.MainWindow):
    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        playlist_select_context: PlaylistSelectContext | None = None,
        nobackout: bool = False,
    ):
        self.dialog = 1
        self.nobackout = nobackout
        self._main_window_transition_out = 'out_scale'
        self._root_widget = bui.containerwidget(
            size=(400, 300),
            transition='in_right',
            parent=bui.get_special_widget('overlay_stack'),
            on_cancel_call=self.main_window_back if not self.nobackout else self.saythingyr
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(200, 250),
            scale=1.3,
            text="Choose Campaign",
            h_align='center',
            v_align='center',
            size=(0, 0),
        )

        bui.buttonwidget(
            parent=self._root_widget,
            label="Normal Campaign",
            position=(100, 150),
            size=(200, 50),
            on_activate_call=self._normal_campaign,
        )

        bui.buttonwidget(
            parent=self._root_widget,
            label="Custom Campaign (not done)",
            position=(100, 80),
            size=(200, 50),
            on_activate_call=self._custom_campaign,
        )

        # Back button
        bui.buttonwidget(
            parent=self._root_widget,
            label="Back",
            position=(100, 20),
            size=(200, 50),
            on_activate_call=self.main_window_back if not self.nobackout else self.saythingyr,
        )
    
    def saythingyr(self):
        if self.dialog == 1:
            ba.screenmessage('Nope. We\'re going back there. Whether you like it or not.', color=(0.5, 0.25, 1.0))
            bui.getsound('spazAttack02').play()
            self.dialog += 1
        elif self.dialog == 2:
            ba.screenmessage('Just get in the dang thingy already.', color=(0.5, 0.25, 1.0))
            bui.getsound('spazFall02').play()
            self.dialog += 1
        elif self.dialog == 3:
            ba.screenmessage('MOVEEEEE ITTTTTTTTT!!!!!!!!!!!!!!', color=(1.0, 0.25, 0.25))
            bui.getsound('spazFall03').play()
    
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
            )
        )
        
    def _normal_campaign(self) -> None:
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
        from bauiv1lib.coop.browser import CoopBrowserWindow
        self.main_window_replace(
            CoopBrowserWindow(
                origin_widget=self._root_widget,
            )
        )

    def _custom_campaign(self) -> None:
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
        from bauiv1lib.coop.altbrowser import CoopBrowserWindow
        self.main_window_replace(
            CoopBrowserWindow(
                origin_widget=self._root_widget,
            )
        )
    # uh... this game's coding is duct tape. yeah.
