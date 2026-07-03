# Released under the MIT License. See LICENSE for details.
#
"""DeathMatch game and support classes."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1 as bs
import random
import time
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence

class Weegee(bs.Actor):
    """WWEEEEGEEEEEHHHH"""
    def __init__(self, pos: tuple[float, float, float]):
        super().__init__()
        self._mesh_scale = 8
        shared = SharedObjects.get()
        self.node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'body_scale': 1.3,
                'mesh': bs.getmesh('weegee'),
                'mesh_scale': self._mesh_scale,
                'color_texture': bs.gettexture('weegee'),
                'shadow_size': 0,
                'gravity_scale': 5,
                'materials': [shared.object_material, shared.no_object_collide_mat,],
                'position': (0, 5, 0),
            }
        )
        # we rely on a combine to keep our position static.
        # by using connectattr, we don't rely on a timer to keep
        # resetting the position, and it's also safer for us
        self.combine = bs.newnode(
            'combine', 
            owner=self.node, 
            attrs={
                'size': 3,
                'input0': pos[0],
                'input1': pos[1],
                'input2': pos[2],
            }
        )
        self.combine.connectattr('output', self.node, 'position')
    
    def start_bouncy(self):
        bs.animate(
            self.node, 
            'mesh_scale',
            {
                0: self._mesh_scale,
                0.1: self._mesh_scale - 0.7,
                0.34: self._mesh_scale,
                0.5: self._mesh_scale,
            },
            loop=True,
        )
    
    def handlemessage(self, msg):
        if isinstance(msg, bs.HitMessage):
            print('heeet masag')
        else:
            return super().handlemessage(msg)
        return None

class Player(bs.Player['Team']):
    """Our player type for this game."""
    def __init__(self) -> None:
        self.lives: int = 3

# _ba_meta export bascenev1.GameActivity
class WeegeeBossGame(bs.GameActivity[Player, bs.Team]):
    """A gametype where you beat weegee. weegeee."""

    name = 'Weegee Boss'
    description = 'Defeat the Weegee boss.'
    # Print messages when players die since it matters here.
    announce_player_deaths = True
    suppress_zoomtext = True

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Weegee\'s Tower of Doom']

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        return 'defeat weegee'

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._weegee: Weegee | None = None
        self.default_music = None
    
    def on_transition_in(self):
        super().on_transition_in()
        self._weegee = Weegee(
            (0, 7, -12),
        )
        self._weegee.start_bouncy()
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self.respawn_player(player)
        else:
            return super().handlemessage(msg)
        return None
    
    @override
    def spawn_player_spaz(
        self,
        player: PlayerT,
        position: Sequence[float] | None = None,
        angle: float | None = None,
    ) -> PlayerSpaz:
        if position is None:
            position = self.map.get_flag_position(None)
        return super().spawn_player_spaz(player, position, angle)

    @override
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
