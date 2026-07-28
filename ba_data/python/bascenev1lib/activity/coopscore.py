# Released under the MIT License. See LICENSE for details.
#
"""Provides a score screen for coop games."""
# pylint: disable=too-many-lines

from __future__ import annotations

import random
import logging
from typing import TYPE_CHECKING, override

from efro.util import strict_partial
import bacommon.bs
from bacommon.login import LoginType
import bascenev1 as bs
import bauiv1 as bui
import babase as ba
import mellboii.mell_resources as mell
import threading

from bascenev1lib.actor.text import Text
from bascenev1lib.actor.zoomtext import ZoomText
from bascenev1lib.actor.image import Image

if TYPE_CHECKING:
    from typing import Any, Sequence


class CoopScoreScreen(bs.Activity[bs.Player, bs.Team]):
    """Score screen showing the results of a cooperative game."""

    def __init__(self, settings: dict):
        # pylint: disable=too-many-statements
        super().__init__(settings)

        plus = bs.app.plus
        assert plus is not None

        # Keep prev activity alive while we fade in
        self.transition_time = 0.5
        self.inherits_tint = True
        self.inherits_vr_camera_offset = True
        self.inherits_music = True
        self.use_fixed_vr_overlay = True
        self._win_music = settings['win_music_override']
        self._lose_music = settings['lose_music_override']

        self._do_new_rating: bool = self.session.tournament_id is not None

        self._score_display_sound = bs.getsound('scoreHit01')
        self._score_display_sound_small = bs.getsound('scoreHit02')
        self.drum_roll_sound = bs.getsound('drumRoll')
        self.cymbal_sound = bs.getsound('cymbal')

        self._replay_icon_texture = bui.gettexture('replayIcon')
        self._menu_icon_texture = bui.gettexture('menuIcon')
        self._next_level_icon_texture = bui.gettexture('nextLevelIcon')

        self._campaign: bs.Campaign = settings['campaign']

        self._have_achievements = (
            bs.app.classic is not None
            and bs.app.classic.ach.achievements_for_coop_level(
                self._campaign.name + ':' + settings['level']
            )
        )

        self._game_service_icon_color: Sequence[float] | None
        self._game_service_achievements_texture: bui.Texture | None
        self._game_service_leaderboards_texture: bui.Texture | None

        # Tie in to specific game services if they are active.
        adapter = plus.accounts.login_adapters.get(LoginType.GPGS)
        gpgs_active = adapter is not None and adapter.is_back_end_active()
        adapter = plus.accounts.login_adapters.get(LoginType.GAME_CENTER)
        game_center_active = (
            adapter is not None and adapter.is_back_end_active()
        )

        if game_center_active:
            self._game_service_icon_color = (1.0, 1.0, 1.0)
            icon = bui.gettexture('gameCenterIcon')
            self._game_service_achievements_texture = icon
            self._game_service_leaderboards_texture = icon
            self._account_has_achievements = True
        elif gpgs_active:
            self._game_service_icon_color = (0.8, 1.0, 0.6)
            self._game_service_achievements_texture = bui.gettexture(
                'googlePlayAchievementsIcon'
            )
            self._game_service_leaderboards_texture = bui.gettexture(
                'googlePlayLeaderboardsIcon'
            )
            self._account_has_achievements = True
        else:
            self._game_service_icon_color = None
            self._game_service_achievements_texture = None
            self._game_service_leaderboards_texture = None
            self._account_has_achievements = False

        self._cashregistersound = bs.getsound('cashRegister')
        self._gun_cocking_sound = bs.getsound('gunCocking')
        self._dingsound = bs.getsound('ding')
        self._score_link: str | None = None
        self._root_ui: bui.Widget | None = None
        self._background: bs.Actor | None = None
        self._old_best_rank = 0.0
        self._game_name_str: str | None = None
        self._game_config_str: str | None = None

        # Ui bits.
        self._corner_button_offs: tuple[float, float] | None = None
        self._restart_button: bui.Widget | None = None
        self._next_level_error: bs.Actor | None = None

        # Score/gameplay bits.
        self._was_complete: bool | None = None
        self._is_complete: bool | None = None
        self._newly_complete: bool | None = None
        self._is_more_levels: bool | None = None
        self._next_level_name: str | None = None
        self._show_info: dict[str, Any] | None = None
        self._name_str: str | None = None
        self._friends_loading_status: bs.Actor | None = None
        self._score_loading_status: bs.Actor | None = None
        self._tournament_time_remaining: float | None = None
        self._tournament_time_remaining_text: Text | None = None
        self._tournament_time_remaining_text_timer: bs.BaseTimer | None = None
        self._submit_score = self.session.submit_score

        # Stuff for activity skip by pressing button
        self._birth_time = bs.time()
        self._min_view_time = 5.0
        self._allow_server_transition = False
        self._server_transitioning: bool | None = None

        self._playerinfos: list[bs.PlayerInfo] = settings['playerinfos']
        assert isinstance(self._playerinfos, list)
        assert all(isinstance(i, bs.PlayerInfo) for i in self._playerinfos)

        self._score: int | None = settings['score']
        assert isinstance(self._score, (int, type(None)))

        self._fail_message: bs.Lstr | None = settings['fail_message']
        assert isinstance(self._fail_message, (bs.Lstr, type(None)))

        self._begin_time: float | None = None

        self._score_order: str
        if 'score_order' in settings:
            if not settings['score_order'] in ['increasing', 'decreasing']:
                raise ValueError(
                    'Invalid score order: ' + settings['score_order']
                )
            self._score_order = settings['score_order']
        else:
            self._score_order = 'increasing'
        assert isinstance(self._score_order, str)
        self._score_type: str
        if 'score_type' in settings:
            if not settings['score_type'] in ['points', 'time']:
                raise ValueError(
                    'Invalid score type: ' + settings['score_type']
                )
            self._score_type = settings['score_type']
        else:
            self._score_type = 'points'
        assert isinstance(self._score_type, str)

        self._level_name: str = settings['level']
        assert isinstance(self._level_name, str)

        self._game_name_str = self._campaign.name + ':' + self._level_name
        self._game_config_str = (
            str(len(self._playerinfos))
            + 'p'
            + self._campaign.getlevel(self._level_name)
            .get_score_version_string()
            .replace(' ', '_')
        )

        try:
            self._old_best_rank = self._campaign.getlevel(
                self._level_name
            ).rating
        except Exception:
            self._old_best_rank = 0.0

        self._victory: bool = settings['outcome'] == 'victory'

    @override
    def __del__(self) -> None:
        super().__del__()

        # If our UI is still up, kill it.
        if self._root_ui and not self._root_ui.transitioning_out:
            with bui.ContextRef.empty():
                bui.containerwidget(edit=self._root_ui, transition='out_left')

    @override
    def on_transition_in(self) -> None:
        from bascenev1lib.actor import background  # FIXME NO BSSTD

        bs.set_analytics_screen('Coop Score Screen')
        super().on_transition_in()
        self._background = background.Background(
            fade_time=0.45, start_faded=False, show_logo=True, flash=not self._victory
        )
        if self._victory:
            if self._win_music:
                bs.setmusic(self._win_music)
            else:
                bs.setmusic(bs.MusicType.SCORES)
        else:
            if self._lose_music:
                bs.setmusic(self._lose_music)
            else:
                bs.setmusic(bs.MusicType.DEFEAT)

    def _ui_menu(self) -> None:
        bui.containerwidget(edit=self._root_ui, transition='out_left')
        with self.context:
            bs.timer(0.1, bs.Call(bs.WeakCall(self.session.end)))

    def _ui_restart(self) -> None:
        from bauiv1lib.tournamententry import TournamentEntryWindow

        # If we're in a tournament and it looks like there's no time left,
        # disallow.
        if self.session.tournament_id is not None:
            if self._tournament_time_remaining is None:
                bui.screenmessage(
                    bui.Lstr(resource='tournamentCheckingStateText'),
                    color=(1, 0, 0),
                )
                bui.getsound('error').play()
                return
            if self._tournament_time_remaining <= 0:
                bui.screenmessage(
                    bui.Lstr(resource='tournamentEndedText'), color=(1, 0, 0)
                )
                bui.getsound('error').play()
                return

        # If there are currently fewer players than our session min,
        # don't allow.
        if len(self.players) < self.session.min_players:
            bui.screenmessage(
                bui.Lstr(resource='notEnoughPlayersRemainingText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        self._campaign.set_selected_level(self._level_name)

        # If this is a tournament, go back to the tournament-entry UI
        # otherwise just hop back in.
        tournament_id = self.session.tournament_id
        if tournament_id is not None:
            assert self._restart_button is not None
            TournamentEntryWindow(
                tournament_id=tournament_id,
                tournament_activity=self,
                position=self._restart_button.get_screen_space_center(),
            )
        else:
            bui.containerwidget(edit=self._root_ui, transition='out_left')
            self.can_show_ad_on_death = True
            with self.context:
                self.end({'outcome': 'restart'})

    def _ui_next(self) -> None:

        # If we didn't just complete this level but are choosing to play the
        # next one, set it as current (this won't happen otherwise).
        if (
            self._is_complete
            and not self._newly_complete
        ):
            assert self._next_level_name is not None
            self._campaign.set_selected_level(self._next_level_name)
        if isinstance(bs.get_foreground_host_session(), bs.CoopSession):
            sessionname = self.session.campaign_level_name
            if sessionname == 'The Finale':
                from bascenev1lib.creditsroll import CreditsActivity
                bs.pushcall(
                    bs.Call(
                        self.session.setactivity, 
                        CreditsActivity()
                    )
                )
                return
        bui.containerwidget(edit=self._root_ui, transition='out_left')
        with self.context:
            self.end({'outcome': 'next_level'})

    def _ui_gc(self) -> None:
        if bs.app.plus is not None:
            bs.app.plus.show_game_service_ui(
                'leaderboard',
                game=self._game_name_str,
                game_version=self._game_config_str,
            )
        else:
            logging.warning('show_game_service_ui requires plus feature-set')

    def _ui_show_achievements(self) -> None:
        if bs.app.plus is not None:
            bs.app.plus.show_game_service_ui('achievements')
        else:
            logging.warning('show_game_service_ui requires plus feature-set')

    def _ui_worlds_best(self) -> None:
        if self._score_link is None:
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource='scoreListUnavailableText'), color=(1, 0.5, 0)
            )
        else:
            bui.open_url(self._score_link)

    def _ui_error(self) -> None:
        with self.context:
            self._next_level_error = Text(
                bs.Lstr(resource='completeThisLevelToProceedText'),
                flash=True,
                maxwidth=360,
                scale=0.54,
                h_align=Text.HAlign.CENTER,
                color=(0.5, 0.7, 0.5, 1),
                position=(300, -235),
            )
            bui.getsound('error').play()
            bs.timer(
                2.0,
                bs.WeakCall(
                    self._next_level_error.handlemessage, bs.DieMessage()
                ),
            )

    def _should_show_worlds_best_button(self) -> bool:

        # Old high score lists webpage for tourneys seems broken
        # (looking at meteor shower at least).
        if self.session.tournament_id is not None:
            return False

        # Link is too complicated to display with no browser.
        return True

    def request_ui(self) -> None:
        """Set up a callback to show our UI at the next opportune time."""
        classic = bui.app.classic
        assert classic is not None
        # We don't want to just show our UI in case the user already has the
        # main menu up, so instead we add a callback for when the menu
        # closes; if we're still alive, we'll come up then.
        # If there's no main menu this gets called immediately.
        classic.add_main_menu_close_callback(bui.WeakCall(self.show_ui))

    def show_ui(self) -> None:
        """Show the UI for restarting, playing the next Level, etc."""
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches

        assert bui.app.classic is not None

        delay = 0.7 if (self._score is not None) else 0.0

        # If there's no players left in the game, lets not show the UI
        # (that would allow restarting the game with zero players, etc).
        if not self.players:
            return
        
        if getattr(bs.app, 'stress_testing', False):
            return

        rootc = self._root_ui = bui.containerwidget(
            size=(0, 0),
            transition='in_right',
            toolbar_visibility='no_menu_minimal',
        )

        h_offs = 7.0
        v_offs = -280.0
        v_offs2 = -236.0

        # We wanna prevent controllers users from popping up browsers
        # or game-center widgets in cases where they can't easily get back
        # to the game (like on mac).
        can_select_extra_buttons = bui.app.classic.platform == 'android'

        bui.set_main_ui_input_device(None)  # Menu is up for grabs.

        if self._have_achievements and self._account_has_achievements:
            bui.buttonwidget(
                parent=rootc,
                color=(0.45, 0.4, 0.5),
                position=(h_offs - 520, v_offs + 450 - 235 + 40),
                size=(300, 60),
                label=bui.Lstr(resource='achievementsText'),
                on_activate_call=bui.WeakCall(self._ui_show_achievements),
                transition_delay=delay + 1.5,
                icon=self._game_service_achievements_texture,
                icon_color=self._game_service_icon_color,
                autoselect=True,
                selectable=can_select_extra_buttons,
            )

        if self._should_show_worlds_best_button():
            bui.buttonwidget(
                parent=rootc,
                color=(0.45, 0.4, 0.5),
                position=(220, v_offs2 + 439),
                size=(350, 62),
                label=(
                    bui.Lstr(resource='tournamentStandingsText')
                    if self.session.tournament_id is not None
                    else (
                        bui.Lstr(resource='worldsBestScoresText')
                        if self._score_type == 'points'
                        else bui.Lstr(resource='worldsBestTimesText')
                    )
                ),
                autoselect=True,
                texture=bui.gettexture('empty'),
                on_activate_call=bui.WeakCall(self._ui_worlds_best),
                transition_delay=delay + 1.9,
                selectable=can_select_extra_buttons,
            )
        else:
            pass

        variant = bui.app.env.variant
        vart = type(variant)
        arcade_or_demo = variant is vart.ARCADE or variant is vart.DEMO

        show_next_button = self._is_more_levels and not arcade_or_demo

        if not show_next_button:
            h_offs += 60

        # Due to virtual-bounds changes, have to squish buttons a bit to
        # avoid overlapping with tips at bottom. Could look nicer to
        # rework things in the middle to get more space, but would
        # rather not touch this old code more than necessary.
        small_buttons = False

        if small_buttons:
            menu_button = bui.buttonwidget(
                parent=rootc,
                autoselect=True,
                position=(h_offs - 130 - 45, v_offs + 40),
                size=(100, 50),
                label='',
                button_type='square',
                on_activate_call=bui.WeakCall(self._ui_menu),
            )
            bui.imagewidget(
                parent=rootc,
                draw_controller=menu_button,
                position=(h_offs - 130 - 60 + 43, v_offs + 43),
                size=(45, 45),
                texture=self._menu_icon_texture,
                opacity=0.8,
            )
        else:
            menu_button = bui.buttonwidget(
                parent=rootc,
                autoselect=True,
                position=(h_offs - 130 - 60, v_offs),
                size=(110, 85),
                label='',
                on_activate_call=bui.WeakCall(self._ui_menu),
            )
            bui.imagewidget(
                parent=rootc,
                draw_controller=menu_button,
                position=(h_offs - 130 - 60 + 22, v_offs + 14),
                size=(60, 60),
                texture=self._menu_icon_texture,
                opacity=0.8,
            )

        if small_buttons:
            self._restart_button = restart_button = bui.buttonwidget(
                parent=rootc,
                autoselect=True,
                position=(h_offs - 60, v_offs + 40),
                size=(100, 50),
                label='',
                button_type='square',
                on_activate_call=bui.WeakCall(self._ui_restart),
            )
            bui.imagewidget(
                parent=rootc,
                draw_controller=restart_button,
                position=(h_offs - 60 + 25, v_offs + 42),
                size=(47, 47),
                texture=self._replay_icon_texture,
                opacity=0.8,
            )
        else:
            self._restart_button = restart_button = bui.buttonwidget(
                parent=rootc,
                autoselect=True,
                position=(h_offs - 60, v_offs),
                size=(110, 85),
                label='',
                on_activate_call=bui.WeakCall(self._ui_restart),
            )
            bui.imagewidget(
                parent=rootc,
                draw_controller=restart_button,
                position=(h_offs - 60 + 19, v_offs + 7),
                size=(70, 70),
                texture=self._replay_icon_texture,
                opacity=0.8,
            )

        next_button: bui.Widget | None = None

        # Our 'next' button is disabled if we haven't unlocked the next
        # level yet and invisible if there is none.
        if show_next_button:
            if self._is_complete:
                call = bui.WeakCall(self._ui_next)
                button_sound = True
                image_opacity = 0.8
                color = None
            else:
                call = bui.WeakCall(self._ui_error)
                button_sound = False
                image_opacity = 0.2
                color = (0.3, 0.3, 0.3)

            if small_buttons:
                next_button = bui.buttonwidget(
                    parent=rootc,
                    autoselect=True,
                    position=(h_offs + 130 - 75, v_offs + 40),
                    size=(100, 50),
                    label='',
                    button_type='square',
                    on_activate_call=call,
                    color=color,
                    enable_sound=button_sound,
                )
                bui.imagewidget(
                    parent=rootc,
                    draw_controller=next_button,
                    position=(h_offs + 130 - 60 + 12, v_offs + 40),
                    size=(50, 50),
                    texture=self._next_level_icon_texture,
                    opacity=image_opacity,
                )
            else:
                next_button = bui.buttonwidget(
                    parent=rootc,
                    autoselect=True,
                    position=(h_offs + 130 - 60, v_offs),
                    size=(110, 85),
                    label='',
                    on_activate_call=call,
                    color=color,
                    enable_sound=button_sound,
                )
                bui.imagewidget(
                    parent=rootc,
                    draw_controller=next_button,
                    position=(h_offs + 130 - 60 + 12, v_offs + 5),
                    size=(80, 80),
                    texture=self._next_level_icon_texture,
                    opacity=image_opacity,
                )

        x_offs_extra = 0 if show_next_button else -100
        self._corner_button_offs = (
            h_offs + 300.0 + x_offs_extra,
            v_offs + 519.0,
        )

        bui.containerwidget(
            edit=rootc,
            selected_child=(
                next_button
                if (self._newly_complete and self._victory and show_next_button)
                else restart_button
            ),
            on_cancel_call=menu_button.activate,
        )

    def _player_press(self, outcome: str) -> None:
        # (Only for headless builds).

        # If this activity is a good 'end point', ask server-mode just
        # once if it wants to do anything special like switch sessions
        # or kill the app.
        if (
            self._allow_server_transition
            and bs.app.classic is not None
            and bs.app.classic.server is not None
            and self._server_transitioning is None
        ):
            self._server_transitioning = (
                bs.app.classic.server.handle_transition()
            )
            assert isinstance(self._server_transitioning, bool)
        else:
            self._server_transitioning = False

        # If server-mode is handling this, don't do anything ourself.
        if (
            self._server_transitioning is True 
            and bs.app.classic.server is not None
        ):
            return

        # Otherwise restart current level.
        self._campaign.set_selected_level(self._level_name)
        with self.context:
            self.end({'outcome': outcome})

    def _safe_assign(self, player: bs.Player) -> None:
        # Just to be extra careful, don't assign if we're transitioning out.
        # (though theoretically that should be ok).
        if not self.is_transitioning_out() and player:
            player.assigninput(
                (
                    bs.InputType.JUMP_PRESS,
                    bs.InputType.BOMB_PRESS,
                    bs.InputType.PICK_UP_PRESS,
                ),
                bs.WeakCall(self._player_press, 'restart'),
            )
            player.assigninput(
                bs.InputType.PUNCH_PRESS, 
                bs.WeakCall(
                    self._player_press, 'next_level'
                )
            )

    @override
    def on_player_join(self, player: bs.Player) -> None:
        super().on_player_join(player)
        
        # Host can't press retry button, so anyone can do it instead.
        time_till_assign = max(
            0, self._birth_time + self._min_view_time - bs.time()
        )

        bs.timer(time_till_assign, bs.WeakCall(self._safe_assign, player))

    @override
    def on_begin(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        super().on_begin()

        app = bs.app
        plus = app.plus
        assert plus is not None

        self._begin_time = bs.time()

        # Calc whether the level is complete and other stuff.
        levels = self._campaign.levels
        level = self._campaign.getlevel(self._level_name)
        self._was_complete = level.complete
        self._is_complete = self._was_complete or self._victory
        self._newly_complete = self._is_complete and not self._was_complete
        self._is_more_levels = (
            level.index < len(levels) - 1
        ) and self._campaign.sequential

        # Any time we complete a level, set the next one as unlocked.
        if self._is_complete and self._is_more_levels:
            plus.add_v1_account_transaction(
                {
                    'type': 'COMPLETE_LEVEL',
                    'campaign': self._campaign.name,
                    'level': self._level_name,
                }
            )
            self._next_level_name = levels[level.index + 1].name

            # If this is the first time we completed it, set the next one
            # as current.
            if self._newly_complete:
                cfg = app.config
                cfg['Selected Coop Game'] = (
                    self._campaign.name + ':' + self._next_level_name
                )
                cfg.commit()
                self._campaign.set_selected_level(self._next_level_name)

        bs.timer(1.0, bs.WeakCall(self.request_ui))

        variant = bs.app.env.variant
        vart = type(variant)
        arcade_or_demo = variant is vart.ARCADE or variant is vart.DEMO

        if (
            self._is_complete
            and self._victory
            and self._is_more_levels
            and not arcade_or_demo
        ):
            Text(
                (
                    bs.Lstr(
                        value='${A}:\n',
                        subs=[('${A}', bs.Lstr(resource='levelUnlockedText'))],
                    )
                    if self._newly_complete
                    else bs.Lstr(
                        value='${A}:\n',
                        subs=[('${A}', bs.Lstr(resource='nextLevelText'))],
                    )
                ),
                transition=Text.Transition.IN_RIGHT,
                transition_delay=5.2,
                flash=self._newly_complete,
                scale=0.54,
                h_align=Text.HAlign.CENTER,
                maxwidth=270,
                color=(0.5, 0.7, 0.5, 1),
                position=(270, -235),
            ).autoretain()
            assert self._next_level_name is not None
            Text(
                bs.Lstr(translate=('coopLevelNames', self._next_level_name)),
                transition=Text.Transition.IN_RIGHT,
                transition_delay=5.2,
                flash=self._newly_complete,
                scale=0.7,
                h_align=Text.HAlign.CENTER,
                maxwidth=205,
                color=(0.5, 0.7, 0.5, 1),
                position=(270, -255),
            ).autoretain()
            if self._newly_complete:
                bs.timer(5.2, self._cashregistersound.play)
                bs.timer(5.2, self._dingsound.play)
            if isinstance(bs.get_foreground_host_session(), bs.CoopSession):
                sessionname = self.session.campaign_level_name
                if sessionname == 'The Finale':
                    self._next_level_name = 'Credits'
        offs_x = -195
        if len(self._playerinfos) > 1:
            pstr = bs.Lstr(
                value='- ${A} -',
                subs=[
                    (
                        '${A}',
                        bs.Lstr(
                            resource='multiPlayerCountText',
                            subs=[('${COUNT}', str(len(self._playerinfos)))],
                        ),
                    )
                ],
            )
        else:
            pstr = bs.Lstr(
                value='- ${A} -',
                subs=[('${A}', bs.Lstr(resource='singlePlayerCountText'))],
            )
        ZoomText(
            self._campaign.getlevel(self._level_name).displayname,
            maxwidth=800,
            flash=False,
            trail=False,
            color=(0.5, 1, 0.5, 1),
            h_align='center',
            scale=0.4,
            position=(0, 292),
            jitter=1.0,
        ).autoretain()
        Text(
            pstr,
            maxwidth=300,
            transition=Text.Transition.FADE_IN,
            scale=0.7,
            h_align=Text.HAlign.CENTER,
            v_align=Text.VAlign.CENTER,
            color=(0.5, 0.7, 0.5, 1),
            position=(0, 230),
        ).autoretain()

        if len(self._playerinfos) > 1:
            adisp = plus.get_v1_account_display_string()
            time_till_assign = max(
                0, self._birth_time + self._min_view_time - bs.time()
            )
            subs = [
                ('${BOMB}', ba.charstr(ba.SpecialChar.RIGHT_BUTTON)),
                ('${PUNCH}', ba.charstr(ba.SpecialChar.LEFT_BUTTON)),
                ('${JUMP}', ba.charstr(ba.SpecialChar.BOTTOM_BUTTON)),
                ('${GRAB}', ba.charstr(ba.SpecialChar.TOP_BUTTON)),
            ]
            Text(
                bs.Lstr(resource='coopScorePlayerPress', subs=subs),
                maxwidth=300,
                transition=Text.Transition.IN_BOTTOM_SLOW,
                transition_delay=time_till_assign,
                scale=1.1,
                h_align=Text.HAlign.CENTER,
                v_align=Text.VAlign.CENTER,
                v_attach=Text.VAttach.BOTTOM,
                color=(0.5, 0.7, 0.5, 0.5),
                position=(0, 60),
                flash=True,
            ).autoretain()
            
        if self._score is not None:
            bs.timer(0.35, self._score_display_sound_small.play)

        # Vestigial remain; this stuff should just be instance vars.
        self._show_info = {}

        if self._score is not None:
            bs.timer(0.8, bs.WeakCall(self._show_score_val, offs_x))
        else:
            bs.pushcall(bs.WeakCall(self._show_fail))

        self._name_str = name_str = ', '.join(
            [p.name for p in self._playerinfos]
        )

        self._score_loading_status = Text(
            bs.Lstr(
                value='${A}...',
                subs=[('${A}', bs.Lstr(resource='loadingText'))],
            ),
            position=(350, 150 + 30),
            color=(1, 1, 1, 0.4),
            transition=Text.Transition.FADE_IN,
            scale=0.7,
            transition_delay=2.0,
        )

        if self._score is not None and self._submit_score:
            bs.timer(0.4, bs.WeakCall(self._play_drumroll))

        # Add us to high scores, filter, and store.
        our_high_scores_all = self._campaign.getlevel(
            self._level_name
        ).get_high_scores()

        our_high_scores = our_high_scores_all.setdefault(
            str(len(self._playerinfos)) + ' Player', []
        )

        if self._score is not None:
            our_score: list | None = [
                self._score,
                {
                    'players': [
                        {'name': p.name, 'character': p.character}
                        for p in self._playerinfos
                    ]
                },
            ]
            our_high_scores.append(our_score)
        else:
            our_score = None

        try:
            our_high_scores.sort(
                reverse=self._score_order == 'increasing', key=lambda x: x[0]
            )
        except Exception:
            logging.exception('Error sorting scores.')
            print(f'our_high_scores: {our_high_scores}')

        del our_high_scores[10:]

        if self._score is not None:
            sver = self._campaign.getlevel(
                self._level_name
            ).get_score_version_string()
            plus.add_v1_account_transaction(
                {
                    'type': 'SET_LEVEL_LOCAL_HIGH_SCORES',
                    'campaign': self._campaign.name,
                    'level': self._level_name,
                    'scoreVersion': sver,
                    'scores': our_high_scores_all,
                }
            )
        if plus.get_v1_account_state() != 'signed_in':
            # We expect this only in kiosk mode; complain otherwise.
            if not arcade_or_demo:
                logging.error('got not-signed-in at score-submit; unexpected')
            bs.pushcall(bs.WeakCall(self._got_score_results, None))
        else:
            assert self._game_name_str is not None
            assert self._game_config_str is not None
            def submit_er():
                mell.submit_score(
                    {
                        'game_name': self._game_name_str,
                        'game_config': self._game_config_str,
                        'name': name_str,
                        'score': self._score,
                        'done_call': bs.WeakCall(self._got_score_results),
                        'order': self._score_order,
                        'tournament_id': self.session.tournament_id,
                        'score_type': self._score_type,
                        'campaign': self._campaign.name,
                        'level': self._level_name,
                    }
                )
            if self._score is not None:
                bs.pushcall(threading.Thread(
                    target=submit_er,
                ).start)
            
        # If we're not doing the world's-best button, just show a title
        # instead.
        ts_height = 300
        ts_h_offs = 290
        v_offs = 40
        txt = Text(
            (
                bs.Lstr(resource='tournamentStandingsText')
                if self.session.tournament_id is not None
                else (
                    bs.Lstr(resource='worldsBestScoresText')
                    if self._score_type == 'points'
                    else bs.Lstr(resource='worldsBestTimesText')
                )
            ),
            maxwidth=210,
            position=(ts_h_offs - 10, ts_height / 2 + 25 + v_offs + 20),
            transition=Text.Transition.IN_LEFT,
            v_align=Text.VAlign.CENTER,
            scale=1.2,
            transition_delay=2.2,
        ).autoretain()

        # If we've got a button on the server, only show this on clients.
        if self._should_show_worlds_best_button():
            assert txt.node
            txt.node.client_only = True

        ts_height = 300
        ts_h_offs = -480
        v_offs = 40
        Text(
            (
                bs.Lstr(resource='yourBestScoresText')
                if self._score_type == 'points'
                else bs.Lstr(resource='yourBestTimesText')
            ),
            maxwidth=210,
            position=(ts_h_offs - 10, ts_height / 2 + 25 + v_offs + 20),
            transition=Text.Transition.IN_RIGHT,
            v_align=Text.VAlign.CENTER,
            scale=1.2,
            transition_delay=1.8,
        ).autoretain()

        display_scores = list(our_high_scores)
        display_count = 5

        while len(display_scores) < display_count:
            display_scores.append((0, None))

        showed_ours = False
        h_offs_extra = 85 if self._score_type == 'points' else 130
        v_offs_extra = 20
        v_offs_names = 0
        scale = 1.0
        p_count = len(self._playerinfos)
        h_offs_extra -= 75
        if p_count > 1:
            h_offs_extra -= 20
        if p_count == 2:
            scale = 0.9
        elif p_count == 3:
            scale = 0.65
        elif p_count == 4:
            scale = 0.5
        times: list[tuple[float, float]] = []
        for i in range(display_count):
            times.insert(
                random.randrange(0, len(times) + 1),
                (1.9 + i * 0.05, 2.3 + i * 0.05),
            )
        for i in range(display_count):
            try:
                if display_scores[i][1] is None:
                    name_str = '-'
                else:
                    name_str = ', '.join(
                        [p['name'] for p in display_scores[i][1]['players']]
                    )
            except Exception:
                logging.exception(
                    'Error calcing name_str for %s.', display_scores
                )
                name_str = '-'
            if display_scores[i] == our_score and not showed_ours:
                flash = True
                color0 = (0.6, 0.4, 0.1, 1.0)
                color1 = (0.6, 0.6, 0.6, 1.0)
                tdelay1 = 3.7
                tdelay2 = 3.7
                showed_ours = True
            else:
                flash = False
                color0 = (0.6, 0.4, 0.1, 1.0)
                color1 = (0.6, 0.6, 0.6, 1.0)
                tdelay1 = times[i][0]
                tdelay2 = times[i][1]
            Text(
                (
                    str(display_scores[i][0])
                    if self._score_type == 'points'
                    else bs.timestring((display_scores[i][0] * 10) / 1000.0)
                ),
                position=(
                    ts_h_offs + 20 + h_offs_extra,
                    v_offs_extra
                    + ts_height / 2
                    + -ts_height * (i + 1) / 10
                    + v_offs
                    + 11.0,
                ),
                h_align=Text.HAlign.RIGHT,
                v_align=Text.VAlign.CENTER,
                color=color0,
                flash=flash,
                transition=Text.Transition.IN_RIGHT,
                transition_delay=tdelay1,
            ).autoretain()

            Text(
                bs.Lstr(value=name_str),
                position=(
                    ts_h_offs + 35 + h_offs_extra,
                    v_offs_extra
                    + ts_height / 2
                    + -ts_height * (i + 1) / 10
                    + v_offs_names
                    + v_offs
                    + 11.0,
                ),
                maxwidth=80.0 + 100.0 * len(self._playerinfos),
                v_align=Text.VAlign.CENTER,
                color=color1,
                flash=flash,
                scale=scale,
                transition=Text.Transition.IN_RIGHT,
                transition_delay=tdelay2,
            ).autoretain()

        # Show achievements for this level.
        ts_height = -150
        ts_h_offs = -480
        v_offs = 40

        # Only make this if we don't have the button (never want clients
        # to see it so no need for client-only version, etc).
        if self._have_achievements:
            if not self._account_has_achievements:
                Text(
                    bs.Lstr(resource='achievementsText'),
                    position=(ts_h_offs - 10, ts_height / 2 + 25 + v_offs + 3),
                    maxwidth=210,
                    host_only=True,
                    transition=Text.Transition.IN_RIGHT,
                    v_align=Text.VAlign.CENTER,
                    scale=1.2,
                    transition_delay=2.8,
                ).autoretain()

            assert self._game_name_str is not None
            assert bs.app.classic is not None
            achievements = bs.app.classic.ach.achievements_for_coop_level(
                self._game_name_str
            )
            hval = -455
            vval = -100
            tdelay = 0.0
            for ach in achievements:
                ach.create_display(hval, vval + v_offs, 3.0 + tdelay)
                vval -= 55
                tdelay += 0.250

        bs.timer(5.0, bs.WeakCall(self._show_tips))

    def _play_drumroll(self) -> None:
        bs.NodeActor(
            bs.newnode(
                'sound',
                attrs={
                    'sound': self.drum_roll_sound,
                    'positional': False,
                    'loop': False,
                },
            )
        ).autoretain()

    def _got_friend_score_results(self, results: list[Any] | None) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        from efro.util import asserttype

        # delay a bit if results come in too fast
        assert self._begin_time is not None
        base_delay = max(0, 1.9 - (bs.time() - self._begin_time))
        ts_height = 300
        ts_h_offs = -550
        v_offs = 30

        # Report in case of error.
        if results is None:
            self._friends_loading_status = Text(
                bs.Lstr(resource='friendScoresUnavailableText'),
                maxwidth=330,
                position=(-475, 150 + v_offs),
                color=(1, 1, 1, 0.4),
                transition=Text.Transition.FADE_IN,
                transition_delay=base_delay + 0.8,
                scale=0.7,
            )
            return

        self._friends_loading_status = None

        # Ok, it looks like we aren't able to reliably get a just-submitted
        # result returned in the score list, so we need to look for our score
        # in this list and replace it if ours is better or add ours otherwise.
        if self._score is not None:
            our_score_entry = [self._score, 'Me', True]
            for score in results:
                if score[2]:
                    if self._score_order == 'increasing':
                        our_score_entry[0] = max(score[0], self._score)
                    else:
                        our_score_entry[0] = min(score[0], self._score)
                    results.remove(score)
                    break
            results.append(our_score_entry)
            results.sort(
                reverse=self._score_order == 'increasing',
                key=lambda x: asserttype(x[0], int),
            )

        # If we're not submitting our own score, we still want to change the
        # name of our own score to 'Me'.
        else:
            for score in results:
                if score[2]:
                    score[1] = 'Me'
                    break
        h_offs_extra = 80 if self._score_type == 'points' else 130
        v_offs_extra = 20
        v_offs_names = 0
        scale = 1.0

        # Make sure there's at least 5.
        while len(results) < 5:
            results.append([0, '-', False])
        results = results[:5]
        times: list[tuple[float, float]] = []
        for i in range(len(results)):
            times.insert(
                random.randrange(0, len(times) + 1),
                (base_delay + i * 0.05, base_delay + 0.3 + i * 0.05),
            )
        for i, tval in enumerate(results):
            score = int(tval[0])
            name_str = tval[1]
            is_me = tval[2]
            if is_me and score == self._score:
                flash = True
                color0 = (0.6, 0.4, 0.1, 1.0)
                color1 = (0.6, 0.6, 0.6, 1.0)
                tdelay1 = base_delay + 1.0
                tdelay2 = base_delay + 1.0
            else:
                flash = False
                if is_me:
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.9, 1.0, 0.9, 1.0)
                else:
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.6, 0.6, 0.6, 1.0)
                tdelay1 = times[i][0]
                tdelay2 = times[i][1]
            if name_str != '-':
                Text(
                    (
                        str(score)
                        if self._score_type == 'points'
                        else bs.timestring((score * 10) / 1000.0)
                    ),
                    position=(
                        ts_h_offs + 20 + h_offs_extra,
                        v_offs_extra
                        + ts_height / 2
                        + -ts_height * (i + 1) / 10
                        + v_offs
                        + 11.0,
                    ),
                    h_align=Text.HAlign.RIGHT,
                    v_align=Text.VAlign.CENTER,
                    color=color0,
                    flash=flash,
                    transition=Text.Transition.IN_RIGHT,
                    transition_delay=tdelay1,
                ).autoretain()
            else:
                if is_me:
                    print('Error: got empty name_str on score result:', tval)

            Text(
                bs.Lstr(value=name_str),
                position=(
                    ts_h_offs + 35 + h_offs_extra,
                    v_offs_extra
                    + ts_height / 2
                    + -ts_height * (i + 1) / 10
                    + v_offs_names
                    + v_offs
                    + 11.0,
                ),
                color=color1,
                maxwidth=160.0,
                v_align=Text.VAlign.CENTER,
                flash=flash,
                scale=scale,
                transition=Text.Transition.IN_RIGHT,
                transition_delay=tdelay2,
            ).autoretain()

    def _on_v2_score_results(
        self, response: bacommon.bs.ScoreSubmitResponse | Exception
    ) -> None:

        if isinstance(response, Exception):
            logging.debug('Got error score-submit response: %s', response)
            return

        assert isinstance(response, bacommon.bs.ScoreSubmitResponse)

        # Aim to have these effects run shortly after the final rating
        # hit happens.
        with self.context:
            assert self._begin_time is not None
            delay = max(0, 5.5 - (bs.time() - self._begin_time))

            assert bui.app.classic is not None
            bs.timer(
                delay,
                strict_partial(
                    bui.app.classic.run_bs_client_effects, response.effects
                ),
            )

    def _got_score_results(self, results: dict[str, Any] | None) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        plus = bs.app.plus
        assert plus is not None
        classic = bs.app.classic
        assert classic is not None

        # We need to manually run this in the context of our activity
        # and only if we aren't shutting down.
        # (really should make the submit_score call handle that stuff itself)
        if self.expired:
            return

        with self.context:
            # Delay a bit if results come in too fast.
            assert self._begin_time is not None
            base_delay = max(0, 2.7 - (bs.time() - self._begin_time))
            # v_offs = 20
            v_offs = 64
            if (
                results.get('error')
                or results.get('status', '') == 'fail'
            ):
                self._score_loading_status = Text(
                    bs.Lstr(resource='worldScoresUnavailableText'),
                    position=(300, 130 + v_offs),
                    color=(1, 1, 1, 0.4),
                    transition=Text.Transition.FADE_IN,
                    transition_delay=base_delay + 0.3,
                    scale=0.7,
                )
                return
            self._score_loading_status = None
            assert self._show_info is not None
            self._show_info['results'] = results
            if results.get('tops', '') != '':
                self._show_info['tops'] = results.get('tops')
            else:
                self._show_info['tops'] = []
            self._score_link = results.get('link')
            offs_x = -195

            ts_h_offs = 280
            ts_height = 300

            # Show the number of games represented by this
            # list (except for in tournaments).
            if self.session.tournament_id is None:
                Text(
                    bs.Lstr(
                        resource='lastGamesText',
                        subs=[
                            (
                                '${COUNT}',
                                str(self._show_info['results']['total']),
                            )
                        ],
                    ),
                    position=(
                        ts_h_offs - 35 + 95,
                        ts_height / 2 + 6 + v_offs - 41,
                    ),
                    color=(0.4, 0.4, 0.4, 1.0),
                    scale=0.7,
                    transition=Text.Transition.IN_RIGHT,
                    transition_delay=base_delay + 0.3,
                ).autoretain()
            else:
                v_offs += 40

            h_offs_extra = 0
            v_offs_names = 0
            scale = 1.0
            p_count = len(self._playerinfos)
            if p_count > 1:
                h_offs_extra -= 40
            if self._score_type != 'points':
                h_offs_extra += 60
            if p_count == 2:
                scale = 0.9
            elif p_count == 3:
                scale = 0.65
            elif p_count == 4:
                scale = 0.5

            # Make sure there's at least 10.
            while len(self._show_info['tops']) < 10:
                self._show_info['tops'].append([0, '-'])

            times: list[tuple[float, float]] = []
            for i in range(len(self._show_info['tops'])):
                times.insert(
                    random.randrange(0, len(times) + 1),
                    (base_delay + i * 0.05, base_delay + 0.4 + i * 0.05),
                )

            # Conundrum: We want to place line numbers to the
            # left of our score column based on the largest
            # score width. However scores may use Lstrs and thus
            # may have different widths in different languages.
            # We don't want to bake down the Lstrs we display
            # because then clients can't view scores in their
            # own language. So as a compromise lets measure
            # max-width based on baked down Lstrs but then
            # display regular Lstrs with max-width set based on
            # that. Hopefully that'll look reasonable for most
            # languages.
            max_score_width = 10.0
            for tval in self._show_info['tops']:
                score = int(tval[0])
                name_str = tval[1]
                if name_str != '-':
                    max_score_width = max(
                        max_score_width,
                        bui.get_string_width(
                            (
                                str(score)
                                if self._score_type == 'points'
                                else bs.timestring(
                                    (score * 10) / 1000.0
                                ).evaluate()
                            ),
                            suppress_warning=True,
                        ),
                    )

            for i, tval in enumerate(self._show_info['tops']):
                score = int(tval[0])
                name_str = tval[1]
                if self._name_str == name_str and self._score == score:
                    flash = True
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.6, 0.6, 0.6, 1.0)
                    tdelay1 = base_delay + 1.0
                    tdelay2 = base_delay + 1.0
                else:
                    flash = False
                    if self._name_str == name_str:
                        color0 = (0.6, 0.4, 0.1, 1.0)
                        color1 = (0.9, 1.0, 0.9, 1.0)
                    else:
                        color0 = (0.6, 0.4, 0.1, 1.0)
                        color1 = (0.6, 0.6, 0.6, 1.0)
                    tdelay1 = times[i][0]
                    tdelay2 = times[i][1]

                if name_str != '-':
                    sstr = (
                        str(score)
                        if self._score_type == 'points'
                        else bs.timestring((score * 10) / 1000.0)
                    )

                    # Line number.
                    Text(
                        str(i + 1),
                        position=(
                            ts_h_offs
                            + 20
                            + h_offs_extra
                            - max_score_width
                            - 8.0,
                            ts_height / 2
                            + -ts_height * (i + 1) / 10
                            + v_offs
                            - 30.0,
                        ),
                        scale=0.5,
                        h_align=Text.HAlign.RIGHT,
                        v_align=Text.VAlign.CENTER,
                        color=(0.3, 0.3, 0.3),
                        transition=Text.Transition.IN_LEFT,
                        transition_delay=tdelay1,
                    ).autoretain()

                    # Score.
                    Text(
                        sstr,
                        position=(
                            ts_h_offs + 20 + h_offs_extra,
                            ts_height / 2
                            + -ts_height * (i + 1) / 10
                            + v_offs
                            - 30.0,
                        ),
                        maxwidth=max_score_width,
                        h_align=Text.HAlign.RIGHT,
                        v_align=Text.VAlign.CENTER,
                        color=color0,
                        flash=flash,
                        transition=Text.Transition.IN_LEFT,
                        transition_delay=tdelay1,
                    ).autoretain()
                # Player name.
                Text(
                    bs.Lstr(value=name_str),
                    position=(
                        ts_h_offs + 35 + h_offs_extra,
                        ts_height / 2
                        + -ts_height * (i + 1) / 10
                        + v_offs_names
                        + v_offs
                        - 30.0,
                    ),
                    maxwidth=80.0 + 100.0 * len(self._playerinfos),
                    v_align=Text.VAlign.CENTER,
                    color=color1,
                    flash=flash,
                    scale=scale,
                    transition=Text.Transition.IN_LEFT,
                    transition_delay=tdelay2,
                ).autoretain()

    def _show_tips(self) -> None:
        from bascenev1lib.actor.tipstext import TipsText

        TipsText(offs_y=30).autoretain()

    def _update_tournament_time_remaining_text(self) -> None:
        if self._tournament_time_remaining is None:
            return
        self._tournament_time_remaining = max(
            0, self._tournament_time_remaining - 1
        )
        if self._tournament_time_remaining_text is not None:
            val = bs.timestring(
                self._tournament_time_remaining,
                centi=False,
            )
            self._tournament_time_remaining_text.node.text = val

    def _show_fail(self) -> None:
        ZoomText(
            bs.Lstr(resource='failText'),
            maxwidth=300,
            flash=False,
            color=(1.0, 0.1, 0.1),
            trailcolor=(0.8, 0.3, 0.3),
            trail=True,
            h_align='center',
            tilt_translate=0.11,
            position=(190 + -195, 40),
            jitter=0.3,
            scale=1.5,
        ).autoretain()
        if self._fail_message is not None:
            Text(
                self._fail_message,
                h_align=Text.HAlign.CENTER,
                position=(0, -100),
                maxwidth=300,
                color=(1, 1, 1, 0.5),
                transition=Text.Transition.FADE_IN,
                transition_delay=1.0,
            ).autoretain()
        bs.timer(0.35, bs.getsound('boo').play)
    

    def _show_score_val(self, offs_x: float) -> None:
        assert self._score_type is not None
        assert self._score is not None

        sesh = bs.getsession()
        players = sesh.sessionplayers

        center_x = 190 + offs_x
        y = -90
        spacing = 60
        n = len(players)

        for i, sessionplayer in enumerate(players):
            xpos = center_x + (i - (n - 1) / 2) * spacing

            Image(
                texture=sessionplayer.get_icon(),
                position=(xpos, y),
                scale=(50.0, 50.0),
                transition=Image.Transition.FADE_IN,
            ).autoretain()

        ZoomText(
            (
                str(self._score)
                if self._score_type == 'points'
                else bs.timestring((self._score * 10) / 1000.0)
            ),
            maxwidth=300,
            flash=False,
            color=(0.4, 1.0, 0.6),
            trailcolor=(0.5, 0.8, 0.6),
            trail=True,
            scale=1.4 if self._score_type == 'points' else 0.6,
            h_align='center',
            tilt_translate=0.11,
            position=(center_x, 40),
            jitter=1.0,
        ).autoretain()

        Text(
            (
                bs.Lstr(
                    value='${A}:',
                    subs=[('${A}', bs.Lstr(resource='finalScoreText'))],
                )
                if self._score_type == 'points'
                else bs.Lstr(
                    value='${A}:',
                    subs=[('${A}', bs.Lstr(resource='finalTimeText'))],
                )
            ),
            maxwidth=300,
            position=(center_x, 150),
            transition=Text.Transition.FADE_IN,
            h_align=Text.HAlign.CENTER,
            v_align=Text.VAlign.CENTER,
        ).autoretain()

        bs.timer(0.35, self._score_display_sound.play)
