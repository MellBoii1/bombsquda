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

from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence

class HangingBar(bs.Actor):
    """A sphere node that stays in place,
    and that can also be swung from."""
    def __init__(self, pos: tuple[float, float, float]):
        super().__init__()
        shared = SharedObjects.get()
        mesh = bs.getmesh('ball')
        tex = bs.gettexture('oil')
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'sphere',
                'body_scale': 0.8,
                'position': pos,
                'gravity_scale': 3,
                'mesh': mesh,
                'mesh_scale': 0.8,
                'shadow_size': 0.5,
                'color_texture': tex,
                'materials': (shared.object_material,),
            },
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
        self._connected_nodes = []
        self._update_timer = bs.Timer(0.01, self._update, repeat=True)
    
    def _update(self):
        for node in self._connected_nodes:
            if not node:
                return
            # if they're moving, impulse us in said direction.
            if abs(node.move_left_right) > 0 or abs(node.move_up_down) > 0:
                dir_x = node.move_left_right * 1.3
                dir_z = -node.move_up_down * 1.3
                pos = self.node.position
                force = 80
                self.node.handlemessage(
                    'impulse',
                    pos[0], pos[1], pos[2],
                    0, 0, 0,
                    force, force,
                    0, 0,
                    dir_x, 1.3, dir_z,
                )
        
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
        elif isinstance(msg, bs.PickedUpMessage):
            # a node grabbed us! let's keep track of em
            # so we can move around and stuff
            if msg.node not in self._connected_nodes:
                self._connected_nodes.append(msg.node)
        elif isinstance(msg, bs.DroppedMessage):
            # dropped us, lets remove em 3:
            if msg.node in self._connected_nodes:
                # ooh ya, we also apply extra impulse
                # to give them some height
                node = msg.node
                dir_x = node.move_left_right * 1.3
                dir_z = -node.move_up_down * 1.3
                pos = self.node.position
                force = 140
                node.handlemessage(
                    'impulse',
                    pos[0], pos[1] - 1, pos[2],
                    0, 0, 0,
                    force, force,
                    0, 0,
                    dir_x, 6, dir_z,
                )
                self._connected_nodes.remove(msg.node)
        else:
            return super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0

# ba_meta export bascenev1.GameActivity
class TestingActivity(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = 'Testing Grounds'
    description = 'Do not play please'

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['TestMap']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.default_music = bs.MusicType.MENU1

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_powerup_drops()
        y = 2.3
        xoffs = -0.5
        z = -0.5
        HangingBar((2 + xoffs, y, z)).autoretain()
        HangingBar((-2 + xoffs, y, z)).autoretain()
        HangingBar((5 + xoffs, y + y, z - 2)).autoretain()
        HangingBar((-5 + xoffs, y + y, z - 2)).autoretain()
        HangingBar((-7 + xoffs, y, z)).autoretain()
        HangingBar((7 + xoffs, y, z)).autoretain()
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self.spawn_player(player)
        else:
            return super().handlemessage(msg)
        return None
