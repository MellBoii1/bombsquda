# Released under the MIT License. See LICENSE for details.
#
"""Elimination mini-game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import weakref
import logging
from typing import TYPE_CHECKING, override
import random

import bascenev1 as bs
import mellboii.mell_resources as mell

from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.nodejumper import ImageJumper

if TYPE_CHECKING:
    from typing import Any, Sequence

class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.lives = 0


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.survival_seconds: int | None = None
        self.spawn_order: list[Player] = []
        self._has_been_eliminated = False


# ba_meta export bascenev1.GameActivity
class EliminationEX(bs.TeamGameActivity[Player, Team]):
    """Game type where last player(s) left alive win."""

    name = 'Elimination EX'
    description = 'Last remaining alive wins. Protect your team.'
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
        return settings

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession)

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
        self._allows_team0_updates = True
        self._allows_team1_updates = True
        self._solo_mode = False

        # Base class overrides:
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SURVIVAL
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        return 'Last team with everyone alive wins.'

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        return 'last team with everyone alive wins'

    @override
    def on_player_join(self, player: Player) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        player.lives = self._lives_per_player
        self.set_player_config(player)

        if self._solo_mode:
            player.team.spawn_order.append(player)
            self._update_solo_mode()
        else:
            # Create our icon and spawn.
            if player.lives > 0:
                self.spawn_player(player)

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

        self._create_icons()

        # We could check game-over conditions at explicit trigger points,
        # but lets just do the simple thing and poll it.
        bs.timer(1.0, self._update, repeat=True)

    def _update_solo_mode(self) -> None:
        # For both teams, find the first player on the spawn order list with
        # lives remaining and spawn them if they're not alive.
        for team in self.teams:
            # Prune dead players from the spawn order.
            team.spawn_order = [p for p in team.spawn_order if p]
            for player in team.spawn_order:
                assert isinstance(player, Player)
                if player.lives > 0:
                    if not player.is_alive():
                        self.spawn_player(player)
                    break
                    
    def _create_team_ui(self, team, x_pos: float, align: str):
        scale = (80, 80)
        text_scale = 1.0

        tex = bs.gettexture(team.earthboundling)

        # Direction: left side (-1) or right side (+1)
        dir_mult = -1 if x_pos < 0 else 1

        # Base positions
        icon_y = scale[1]
        name_offset_y = 30
        lives_offset_y = -30

        name_offset_x = 50 * dir_mult
        lives_offset_x = 80 * -dir_mult

        # Icon
        icon = bs.newnode('image', attrs={
            'texture': tex,
            'position': (x_pos, icon_y),
            'scale': scale,
            'opacity': 0.5,
            'absolute_scale': True,
            'attach': 'bottomCenter',
        })

        # Name (above, slightly outward)
        name = bs.newnode("text", attrs={
            "text": team.name,
            "position": (x_pos + name_offset_x, icon_y + name_offset_y),
            "scale": text_scale,
            "h_attach": "center",
            "v_attach": "bottom",
            "h_align": align,
            "color": team.color,
            "maxwidth": 250,
        })

        # Lives (next to name)
        lives = bs.newnode("text", attrs={
            "text": f'x{team.players[0].lives}',
            "position": (x_pos + lives_offset_x, icon_y + lives_offset_y),
            "scale": 1.5,
            "h_attach": "center",
            "v_attach": "bottom",
            "h_align": align,
            "color": team.color,
        })

        return icon, name, lives


    def _create_icons(self) -> None:
        # Left team
        if self.teams[0] and self.teams[0].players:
            self.team1eb, self.team1name, self.team1lives = self._create_team_ui(
                self.teams[0],
                x_pos=-250,
                align="left"
            )
        if self.teams[1] and self.teams[1].players:
            # Right team
            self.team2eb, self.team2name, self.team2lives = self._create_team_ui(
                self.teams[1],
                x_pos=250,
                align="right"
            )
        
        
    def _get_spawn_point(self, player: Player) -> bs.Vec3 | None:
        del player  # Unused.

        # In solo-mode, if there's an existing live player on the map, spawn at
        # whichever spot is farthest from them (keeps the action spread out).
        if self._solo_mode:
            living_player = None
            living_player_pos = None
            for team in self.teams:
                for tplayer in team.players:
                    if tplayer.is_alive():
                        assert tplayer.node
                        ppos = tplayer.node.position
                        living_player = tplayer
                        living_player_pos = ppos
                        break
            if living_player:
                assert living_player_pos is not None
                player_pos = bs.Vec3(living_player_pos)
                points: list[tuple[float, bs.Vec3]] = []
                for team in self.teams:
                    start_pos = bs.Vec3(self.map.get_start_position(team.id))
                    points.append(
                        ((start_pos - player_pos).length(), start_pos)
                    )
                # Hmm.. we need to sort vectors too?
                points.sort(key=lambda x: x[0])
                return points[-1][1]
        return None

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        """Spawn a player (override)."""
        actor = self.spawn_player_spaz(player, self._get_spawn_point(player))
        if not self._solo_mode:
            bs.timer(0.3, bs.Call(self._print_lives, player))
        return actor

    def _print_lives(self, player: Player) -> None:
        from bascenev1lib.actor import popuptext

        # We get called in a timer so it's possible our player has left/etc.
        if not player or not player.is_alive() or not player.node:
            return

    @override
    def on_player_leave(self, player: Player) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        super().on_player_leave(player)
        player.icons = []

        # Remove us from spawn-order.
        if self._solo_mode:
            if player in player.team.spawn_order:
                player.team.spawn_order.remove(player)

        # If the player to leave was the last in spawn order and had
        # their final turn currently in-progress, mark the survival time
        # for their team.
        if self._get_total_team_lives(player.team) == 0:
            assert self._start_time is not None
            player.team.survival_seconds = int(bs.time() - self._start_time)

    def _get_total_team_lives(self, team: Team) -> int:
        return sum(player.lives for player in team.players)
    
    def _update_icons(self, player: Player):
        if player.team == self.teams[0]:
            # We allow for updating the text, since it's crucial.
            self.team1lives.text = f'x{self.teams[0].players[0].lives}'
            if not self._allows_team0_updates:
                return
            # Anything around here could be recalled, which is why we prevent that.
            self._allows_team0_updates = False
            duration = 1
            intensity = 8
            if player.lives == 0:
                duration += 1
                intensity += 4
                list = mell.screams
                bs.getsound(random.choice(list)).play()
                self.team1eb.texture = bs.gettexture(f'{player.team.earthboundling}_lose')
                ImageJumper.jump_image(self.team1eb)
            mell.shake_node(
                self.team1lives,
                duration=duration,
                interval=0.01,
                intensity=8,
                array_num=2,
            )
            def reallow():
                self._allows_team0_updates = True
            bs.timer(duration, reallow)
        else:
            self.team2lives.text = f'x{self.teams[1].players[0].lives}'
            if not self._allows_team1_updates:
                return
            duration = 1
            intensity = 8
            if player.lives == 0:
                duration += 1
                intensity += 4
                list = mell.screams
                bs.getsound(random.choice(list)).play()
                self.team2eb.texture = bs.gettexture(f'{player.team.earthboundling}_lose')
                ImageJumper.jump_image(self.team2eb)
            mell.shake_node(
                self.team2lives,
                duration=duration,
                interval=0.01,
                intensity=intensity,
                array_num=2,
            )
            def reallow():
                self._allows_team1_updates = True
            bs.timer(duration, reallow)


    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player: Player = msg.getplayer(Player)

            player.lives -= 1
            if player.lives < 0:
                logging.exception(
                    "Got lives < 0 in Elim; this shouldn't happen. solo: %s",
                    self._solo_mode,
                )
                player.lives = 0

            # Play big death sound on our last death
            # or for every one in solo mode.
            if self._solo_mode or player.lives == 0:
                death_sound = SpazFactory.get().single_player_death_sound
                if isinstance(death_sound, tuple):
                    random.choice(death_sound).play()  # pick a random one
                else:
                    death_sound.play()

            def _kill_teammates():
                for teammate in player.team.players:
                    if teammate is not player and teammate.is_alive():
                        if teammate.actor:
                            teammate.actor.handlemessage(bs.DieMessage())
            # add delay to attempt to stop infinite recursion...
            bs.timer(0.01, _kill_teammates)
            
            self._update_icons(player)
            
            if player.lives == 0:
                if not player.team._has_been_eliminated:
                    player.team._has_been_eliminated = True
                    # Mark team survival time
                    assert self._start_time is not None
                    player.team.survival_seconds = int(bs.time() - self._start_time)
            else:
                # Otherwise, in regular mode, respawn.
                if not self._solo_mode:
                    self.respawn_player(player)

            # In solo, put ourself at the back of the spawn order.
            if self._solo_mode:
                player.team.spawn_order.remove(player)
                player.team.spawn_order.append(player)

    def _update(self) -> None:
        if self._solo_mode:
            # For both teams, find the first player on the spawn order
            # list with lives remaining and spawn them if they're not alive.
            for team in self.teams:
                # Prune dead players from the spawn order.
                team.spawn_order = [p for p in team.spawn_order if p]
                for player in team.spawn_order:
                    assert isinstance(player, Player)
                    if player.lives > 0:
                        if not player.is_alive():
                            self.spawn_player(player)
                        break

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
        for team in self.teams:
            results.set_team_score(team, team.survival_seconds)
        self.end(results=results)
