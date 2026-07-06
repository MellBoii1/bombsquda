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
import math
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.spaz import Spaz

if TYPE_CHECKING:
    from typing import Any, Sequence

class Weegee(bs.Actor):
    """WWEEEEGEEEEEHHHH"""
    def __init__(self):
        super().__init__()
        seshplrs = self.getactivity().session.sessionplayers
        self.hitpoints = self.max_hitpoints = (
            6900 * len(seshplrs)
        )
        shared = SharedObjects.get()
        self._scale = scale = 13
        # this is our node, handles 
        # actual damage and stuff
        show_node = False
        self.node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'crate',
                'body_scale': scale,
                'mesh_scale': scale if show_node else 0,
                'mesh': bs.getmesh('tnt'),
                'color_texture': bs.gettexture('white'),
                'materials': [
                    shared.object_material, 
                    shared.no_object_footing_collide_mat, # don't collide with footing and objects
                    shared.disallow_pickup_material, # DONT FUCKIN ALLOW PICKUPs
                ], 
                'is_area_of_interest': True,
                'shadow_size': 0,
            }
        )
        # visual node.
        # just stays there and looks cool (no logic
        # except for animations)
        self.visual_node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'puck',
                'body_scale': 1,
                'mesh_scale': scale + 3,
                'mesh': bs.getmesh('weegee'),
                'color_texture': bs.gettexture('weegee'),
                'materials': [shared.object_material, shared.non_collide_mat],
                'shadow_size': 0,
            }
        )
        pos = (0, 5, -15)
        # we rely on a combine to keep our position static.
        # by using connectattr, we don't rely on a timer to keep
        # resetting the position (game does it every sim-update)
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
        self.combine.connectattr('output', self.visual_node, 'position')
        self.start_bouncy()
    
    def start_bouncy(self):
        bs.animate(
            self.visual_node,
            'mesh_scale',
            {
                0: self._scale,
                0.06: self._scale - 3.5,
                0.13: self._scale - 4,
                0.38: self._scale,
            },
            loop=True,
        )
        
    def handlemessage(self, msg):
        if isinstance(msg, bs.HitMessage):
            damage = 0
            # punches hit us weaker
            iscale = 0.5 if msg.hit_type == 'punch' else 1
            if not msg.flat_damage:
                # "code from bombgeon
                # i already knew this method but i had a problem
                # still thanks to gummy for figuring this out"
                # yeah thanks efro for fucking hardcoding damage
                # --------------------------------------------
                # this is SO impractical dude.
                calculator = bs.newnode(
                    'spaz', 
                    attrs={
                        'style': 'ali', # .. so we dont see the eyes.
                        'is_area_of_interest': False, # Dont wanna take that chance
                    }
                )
                # calculate a good enough position based on distance
                center = self.node.position
                dx = abs(msg.pos[0] - center[0])
                dy = abs(msg.pos[1] - center[1])
                dz = abs(msg.pos[2] - center[2])
                dist = math.sqrt(dx + dy + dz)
                # bit of leeway so damage isnt too random
                leeway_scale = 0.2
                pos = (
                    msg.pos[0] + (dist * leeway_scale),
                    msg.pos[1] + (dist * leeway_scale),
                    msg.pos[2] + (dist * leeway_scale),
                )
                # bombs need a position i guess ???    
                calculator.handlemessage( 
                    'stand',
                    pos[0],
                    pos[1],
                    pos[2],
                    90,
                )
                
                # damage, yadda yadda
                calculator.handlemessage(
                    'impulse',
                    msg.pos[0],
                    msg.pos[1],
                    msg.pos[2],
                    msg.velocity[0],
                    msg.velocity[1],
                    msg.velocity[2],
                    msg.magnitude * iscale,
                    msg.velocity_magnitude * iscale,
                    msg.radius,
                    1,
                    msg.force_direction[0],
                    msg.force_direction[1],
                    msg.force_direction[2],
                )
                # Uh-uh give us the damage and ur done pally
                damage = 0.22 * calculator.damage
                calculator.delete()
            else:
                damage = msg.flat_damage
            # update hp
            self.hitpoints -= int(damage)
            # tell activitty to update the bar and such
            self.getactivity()._update_for_stats()
        else:
            return super().handlemessage(msg)
        return None

class Player(bs.Player['Team']):
    """Our player type for this game."""
    def __init__(self) -> None:
        self.lives: int = 3

# _ba_meta export bascenev1.GameActivity
class WeegeeBossGame(bs.TeamGameActivity[Player, bs.Team]):
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
        self._hp_bar = None
        self._bar_tex = self._backing_tex = bs.gettexture('bar')
        barscale = 1
        self._width = 500 
        self._height = 45 * barscale
        self._bar = None
        self.default_music = None
    
    def on_transition_in(self):
        super().on_transition_in()
        self._weegee = Weegee()
        self.create_bar()
    
    def create_bar(self):
        pos = (0, -290)
        self._pos = pos
        self._backing = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'scale': (self._width, self._height),
                    'color': (0.1, 0.1, 0.1),
                    'texture': self._backing_tex,
                    'position': pos,
                },
            )
        )
        self._bar = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'color': (0.1, 0.9, 0.25),
                    'texture': self._bar_tex,
                    'position': pos,
                },
            )
        )        
        hp = self._weegee.hitpoints
        hp_max = self._weegee.max_hitpoints
        hp_percent = (hp / hp_max) * 100
        self._bar_hp_text = bs.newnode(
            'text',
            owner=self._bar.node,
            attrs={
                'scale': 1.4,
                'color': (0.65, 1, 0.7),
                'opacity': 0.8,
                'text': f'{hp_percent}%',
                'h_align': 'center',
                'v_align': 'center',
                'position': pos,
            },
        )
        self._bar_accurate_hp_text = bs.newnode(
            'text',
            owner=self._bar.node,
            attrs={
                'scale': 0.9,
                'color': (0.4, 0.9, 0.5),
                'opacity': 0.5,
                'text': f'{hp}/{hp_max}',
                'h_align': 'center',
                'v_align': 'center',
                'position': (
                    pos[0], 
                    pos[1] - self._height + 5,
                ),
            },
        )
        self._bar_name_text = bs.newnode(
            'text',
            owner=self._bar.node,
            attrs={
                'scale': 1.1,
                'color': (0.4, 1.1, 0.65),
                'opacity': 1.0,
                'text': 'Weegee',
                'h_align': 'center',
                'v_align': 'center',
                'position': (
                    pos[0] - (self._width * 0.5) + 90, 
                    pos[1] + self._height - 3,
                ),
            },
        )
        self._bar_icon = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('weegee_icon1'),
                'scale': (80, 80),
                'position': (
                    pos[0] - (self._width * 0.5) + 10, 
                    pos[1],
                ),
            },
        )
        self._bar_scale = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': 0,
                'input1': self._height,
            },
        )
        assert self._bar.node
        self._bar_scale.connectattr('output', self._bar.node, 'scale')
        self._bar_position = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': -self._width / 2,
                'input1': pos[1],
            },
        )
        self._bar_position.connectattr('output', self._bar.node, 'position')
        val = self._width * (hp / hp_max)
        bs.animate(
            self._backing.node,
            'opacity',
            {
                0: 0,
                0.5: 1,
            }
        )
        bs.animate(
            self._bar_hp_text,
            'opacity',
            {
                0: 0,
                1: 1,
            }
        )
        bs.animate_array(
            self._bar_name_text,
            'position', 2,
            {
                0: (-1200, self._bar_name_text.position[1]),
                0.8: self._bar_name_text.position,
            }
        )
        bs.animate_array(
            self._bar_icon,
            'position', 2,
            {
                0: (-1200, self._bar_icon.position[1]),
                1: self._bar_icon.position,
            }
        )
        bs.animate(
            self._bar_accurate_hp_text,
            'opacity',
            {
                0: 0,
                0.8: 0,
                1.7: 1,
            }
        )        
        bs.animate(
            self._bar.node,
            'opacity',
            {
                0: 0,
                0.7: 1,
            }
        )
        self.set_bar_length(val, time=1)
    
    def set_bar_length(self, length: int | float, time: int = 0.2):
        if self._bar is None:
            self.create_bar()
        if self._bar_scale is not None:
            self._bar_width = length
            cur_x = self._bar_position.input0
            bs.animate(
                self._bar_position,
                'input0',
                {
                    0: cur_x, 
                    time: -self._width / 2 + self._bar_width / 2
                },
            )
            bs.animate(
                self._bar_scale, 
                'input0',
                {
                    0: self._bar_scale.input0,
                    time: length,
                }
            )
    
    def _update_for_stats(self):
        hp = self._weegee.hitpoints
        hp_max = self._weegee.max_hitpoints
        self.set_bar_length(
            self._width * (hp / hp_max)
        )
        self._bar_accurate_hp_text.text = f'{hp}/{hp_max}'
        self._bar_hp_text.text = str(
            int( (hp / hp_max) * 100) 
        ) + '%'
    
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
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
