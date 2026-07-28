# Released under the MIT License. See LICENSE for details.
#
"""Elimination mini-game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from bascenev1lib.actor.popuptext import PopupText
import babase as ba
import weakref
import logging
from typing import TYPE_CHECKING, override

import bascenev1 as bs
import random
import mellboii.mell_resources as mell

from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.smashspaz import SmashSpaz, _get_percent_color

if TYPE_CHECKING:
    from typing import Any, Sequence


class Icon(bs.Actor):
    """Creates in in-game icon on screen."""

    def __init__(
        self,
        player: Player,
        position: tuple[float, float],
        scale: float,
        *,
        show_lives: bool = True,
        show_death: bool = True,
        name_scale: float = 1.0,
        name_maxwidth: float = 115.0,
        flatness: float = 1.0,
        shadow: float = 1.0,
    ):
        super().__init__()

        self._player = weakref.ref(player)  # Avoid ref loops.
        self._show_lives = show_lives
        self._show_death = show_death
        self._name_scale = name_scale
        self._scale = 0
        self._percent_scale = name_scale + 0.1
        self._outline_tex = bs.gettexture('characterIconMask')
        self._allow_shakes = True

        icon = player.get_icon()
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': icon['texture'],
                'tint_texture': icon['tint_texture'],
                'tint_color': icon['tint_color'],
                'vr_depth': 400,
                'tint2_color': icon['tint2_color'],
                'mask_texture': self._outline_tex,
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': 'bottomCenter',
            },
        )
        self._name_text = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': bs.Lstr(value=player.getname()),
                'color': bs.safecolor(player.team.color),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'maxwidth': name_maxwidth,
                'shadow': shadow,
                'flatness': flatness,
                'h_attach': 'center',
                'v_attach': 'bottom',
            },
        )
        self._percent_text = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': '0%',
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 390,
                'shadow': shadow,
                'flatness': flatness,
                'h_attach': 'center',
                'v_attach': 'bottom',
            },
        )
        if self._show_lives:
            self._lives_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': 'x0',
                    'color': (1, 1, 0.5),
                    'h_align': 'left',
                    'vr_depth': 430,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'h_attach': 'center',
                    'v_attach': 'bottom',
                },
            )
        self.set_position_and_scale(position, scale)
        
    def set_position_and_scale(
        self, position: tuple[float, float], scale: float
    ) -> None:
        """(Re)position the icon."""
        assert self.node
        self.node.position = position
        self.node.scale = [70.0 * scale]
        self._scale = scale
        self._name_text.position = (position[0], position[1] + scale * 52.0)
        self._percent_text.position = (position[0], position[1] + scale * 73.0)
        self._name_text.scale = 1.0 * scale * self._name_scale
        self._percent_text.scale = 1.0 * scale * self._percent_scale
        if self._show_lives:
            self._lives_text.position = (
                position[0] + scale * 10.0,
                position[1] - scale * 43.0,
            )
            self._lives_text.scale = 1.0 * scale

    def update_for_lives(self) -> None:
        """Update for the target player's current lives."""
        player = self._player()
        lives = player.lives if player else 0
        scale = self._scale
        position = self.node.position
        self._percent_text.position = (position[0], position[1] + scale * 73.0)

        if self._show_lives:
            if lives > 0:
                self._lives_text.text = 'x' + str(lives - 1)
            else:
                self._lives_text.text = ''

        if lives == 0:
            self._name_text.opacity = 0.2
            assert self.node
            self.node.color = (0.7, 0.3, 0.3)
            self.node.opacity = 0.2
    
    def update_for_percentage(self):
        player = self._player()
        lives = player.lives if player else 0
        percent = player.actor.percentage if player and player.actor else 0
        color = _get_percent_color(percent)
        if lives > 0:
            self._percent_text.text = str(percent) + '%'
            self._percent_text.color = color
        else:
            self._percent_text.text = ''
            self._percent_text.color = color
    
    def shake_for_damage(self, amount: int = 50):
        if not self._allow_shakes:
            return
        self._allow_shakes = False
        player = self._player()
        percent = player.actor.percentage if player and player.actor else 0
        duration = 0.8
        intensity = amount / 10
        mell.shake_node(
            self._percent_text,
            duration=duration,
            interval=0.01,
            intensity=intensity,
            array_num=2,
        )
        def reallow():
            scale = self._scale
            position = self.node.position
            self._percent_text.position = (position[0], position[1] + scale * 73.0)
            self._allow_shakes = True
        bs.timer(duration, reallow)
        
        
        
    
    def handle_player_spawned(self) -> None:
        """Our player spawned; hooray!"""
        if not self.node:
            return
        self.node.opacity = 1.0
        self.update_for_lives()

    def handle_player_died(self) -> None:
        """Well poo; our player died."""
        if not self.node:
            return
        if self._show_death:
            bs.animate(
                self.node,
                'opacity',
                {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 1.0,
                    0.55: 0.2,
                },
            )
            duration = 1
            intensity = 8
            player = self._player()
            lives = player.lives if player else 0
            if lives == 0:
                duration += 1
                intensity += 4
            mell.shake_node(
                self.node,
                duration=duration,
                interval=0.01,
                intensity=intensity,
                array_num=2,
            )
            if lives == 0:
                list = mell.screams
                bs.getsound(random.choice(list)).play()
                bs.timer(0.6, self.update_for_lives)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
            return None
        return super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.lives = 0
        self.icons: list[Icon] = []


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.survival_seconds: int | None = None
        self.spawn_order: list[Player] = []

# ba_meta export bascenev1.GameActivity
class SmashBrosGame(bs.TeamGameActivity[Player, Team]):
    """Game type where the last one alive wins. Spazzes gain percentage 
    instead of damage, and increase impulse scale. Based on Super Smash Bros.."""

    name = 'Super Smash Bros.'
    description = 'Knock your enemies offscreen.'
    scoreconfig = bs.ScoreConfig(
        label='Survived', scoretype=bs.ScoreType.SECONDS, none_is_winner=True
    )
    # Show messages when players die since it's meaningful here.
    announce_player_deaths = True

    allow_mid_activity_joins = False

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(
                'Lives Per Player',
                default=1,
                min_value=1,
                max_value=10,
                increment=1,
            ),
            bs.IntChoiceSetting(
                'Time Limit',
                choices=[
                    ('None', 0),
                    ('1 Minute', 60),
                    ('2 Minutes', 120),
                    ('5 Minutes', 300),
                    ('10 Minutes', 600),
                    ('20 Minutes', 1200),
                ],
                default=0,
            ),
            bs.FloatChoiceSetting(
                'Respawn Times',
                choices=[
                    ('Shorter', 0.25),
                    ('Short', 0.5),
                    ('Normal', 1.0),
                    ('Long', 2.0),
                    ('Longer', 4.0),
                ],
                default=1.0,
            ),
            bs.BoolSetting('Epic Mode', default=False),
        ]
        if issubclass(sessiontype, bs.DualTeamSession):
            settings.append(
                bs.BoolSetting('Balance Total Lives', default=False)
            )
        return settings

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        assert bs.app.classic is not None
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._start_time: float | None = None
        self._vs_text: bs.Actor | None = None
        self._round_end_timer: bs.Timer | None = None
        self._epic_mode = bool(settings['Epic Mode'])
        self._lives_per_player = int(settings['Lives Per Player'])
        self._time_limit = float(settings['Time Limit'])
        self._balance_total_lives = bool(
            settings.get('Balance Total Lives', False)
        )

        # Base class overrides:
        self.slow_motion = self._epic_mode
        self.danger_icon_left = None
        self.danger_icon_right = None
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SURVIVAL
        )
        self._ffa_icon_scale = 0.8
        self._teams_icon_scale = 0.7

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        return (
            'Knock your enemies offscreen. Last team alive wins.'
            if isinstance(self.session, bs.DualTeamSession)
            else 'Knock your enemies offscreen. Last one alive wins.'
        )

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        return (
            'last team alive wins'
            if isinstance(self.session, bs.DualTeamSession)
            else 'last one alive wins'
        )

    @override
    def on_player_join(self, player: Player) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        player.lives = self._lives_per_player
        self.set_player_config(player)
        
        # Create our icon and spawn.
        player.icons = [Icon(player, position=(0, 50), scale=self._ffa_icon_scale)]
        if player.lives > 0:
            self.spawn_player(player)

        # Don't waste time doing this until begin.
        if self.has_begun():
            self._update_icons()

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self._start_time = bs.time()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        # If balance-team-lives is on, add lives to the smaller team until
        # total lives match.
        if (
            isinstance(self.session, bs.DualTeamSession)
            and self._balance_total_lives
            and self.teams[0].players
            and self.teams[1].players
        ):
            if self._get_total_team_lives(
                self.teams[0]
            ) < self._get_total_team_lives(self.teams[1]):
                lesser_team = self.teams[0]
                greater_team = self.teams[1]
            else:
                lesser_team = self.teams[1]
                greater_team = self.teams[0]
            add_index = 0
            while self._get_total_team_lives(
                lesser_team
            ) < self._get_total_team_lives(greater_team):
                lesser_team.players[add_index].lives += 1
                add_index = (add_index + 1) % len(lesser_team.players)

        self._update_icons()

        # We could check game-over conditions at explicit trigger points,
        # but lets just do the simple thing and poll it.
        bs.timer(1.0, self._update, repeat=True)

    def _update_icons(self) -> None:
        # pylint: disable=too-many-branches

        # In free-for-all mode, everyone is just lined up along the bottom.
        if isinstance(self.session, bs.FreeForAllSession):
            count = len(self.teams)
            x_offs = 85
            xval = x_offs * (count - 1) * -0.5
            for team in self.teams:
                if len(team.players) == 1:
                    player = team.players[0]
                    for icon in player.icons:
                        icon.set_position_and_scale((xval, 30), self._ffa_icon_scale)
                        icon.update_for_lives()
                    xval += x_offs

        # In teams mode we split up teams.
        else:
            for team in self.teams:
                if team.id == 0:
                    xval = -50
                    x_offs = -85
                else:
                    xval = 50
                    x_offs = 85
                for player in team.players:
                    for icon in player.icons:
                        icon.set_position_and_scale((xval, 30), self._teams_icon_scale)
                        icon.update_for_lives()
                    xval += x_offs
                        
    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        """Spawn a player (override)."""
        player.playerspaztype = SmashSpaz
        actor = self.spawn_player_spaz(player)
        # We make grab a bit longer to kinda prevent GPS
        actor._pickup_cooldown = 2500
        bs.timer(0.3, bs.Call(self._print_lives, player))

        # If we have any icons, update their state.
        for icon in player.icons:
            icon.handle_player_spawned()
        return actor

    def _print_lives(self, player: Player) -> None:
        from bascenev1lib.actor import popuptext

        # We get called in a timer so it's possible our player has left/etc.
        if not player or not player.is_alive() or not player.node:
            return

        popuptext.PopupText(
            'x' + str(player.lives - 1),
            color=(1, 1, 0, 1),
            offset=(0, -0.8, 0),
            random_offset=0.0,
            scale=1.8,
            position=player.node.position,
        ).autoretain()

    @override
    def on_player_leave(self, player: Player) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        super().on_player_leave(player)
        player.icons = []

        # Update icons in a moment since our team will be gone from the
        # list then.
        bs.timer(0, self._update_icons)

        # If the player to leave was the last in spawn order and had
        # their final turn currently in-progress, mark the survival time
        # for their team.
        if self._get_total_team_lives(player.team) == 0:
            assert self._start_time is not None
            player.team.survival_seconds = int(bs.time() - self._start_time)

    def _get_total_team_lives(self, team: Team) -> int:
        return sum(player.lives for player in team.players)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player: Player = msg.getplayer(Player)

            player.lives -= 1
            if player.lives < 0:
                logging.exception(
                    "Got lives < 0 in Elim; this shouldn't happen.",
                )
                player.lives = 0

            # If we have any icons, update their state.
            for icon in player.icons:
                icon.handle_player_died()


            # If we hit zero lives, we're dead (and our team might be too).
            if player.lives == 0:
                
                # If the whole team is now dead, mark their survival time.
                if self._get_total_team_lives(player.team) == 0:
                    assert self._start_time is not None
                    player.team.survival_seconds = int(
                        bs.time() - self._start_time
                    )
                death_sound = SpazFactory.get().single_player_death_sound
                if isinstance(death_sound, tuple):
                    random.choice(death_sound).play()  # pick a random one
                else:
                    death_sound.play()
                    
            else:
                # Otherwise, in regular mode, respawn.
                self.respawn_player(player)

    def _update(self) -> None:
        # If we're down to 1 or fewer living teams, start a timer to end
        # the game (allows the dust to settle and draws to occur if deaths
        # are close enough).
        if len(self._get_living_teams()) < 2:
            self._round_end_timer = bs.Timer(0.5, self.end_game)

    def _get_living_teams(self) -> list[Team]:
        return [
            team
            for team in self.teams
            if len(team.players) > 0
            and any(player.lives > 0 for player in team.players)
        ]

    @override
    def end_game(self) -> None:
        """End the game."""
        if self.has_ended():
            return
        results = bs.GameResults()
        self._vs_text = None  # Kill our 'vs' if its there.
        for team in self.teams:
            results.set_team_score(team, team.survival_seconds)
        self.end(results=results)
