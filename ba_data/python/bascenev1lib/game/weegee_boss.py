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
from bascenev1lib.actor.bomb import BombFactory, Bomb
from bascenev1lib.actor.respawnicon import RespawnIcon
from bascenev1lib.actor.spazbot import SpazBot, SpazBotSet

if TYPE_CHECKING:
    from typing import Any, Sequence

class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.has_been_hurt = False
        self.respawn_wave = 0
    # FIXME: We shouldn't be using customdata here
    # (but need to update respawn funcs accordingly first).
    @property
    def respawn_timer(self) -> bs.Timer | None:
        """Type safe access to standard respawn timer."""
        val = self.customdata.get('respawn_timer', None)
        assert isinstance(val, (bs.Timer, type(None)))
        return val

    @respawn_timer.setter
    def respawn_timer(self, value: bs.Timer | None) -> None:
        self.customdata['respawn_timer'] = value

    @property
    def respawn_icon(self) -> RespawnIcon | None:
        """Type safe access to standard respawn icon."""
        val = self.customdata.get('respawn_icon', None)
        assert isinstance(val, (RespawnIcon, type(None)))
        return val

    @respawn_icon.setter
    def respawn_icon(self, value: RespawnIcon | None) -> None:
        self.customdata['respawn_icon'] = value

class HealthBar(bs.Actor):
    """An animated HP bar with name, icon, and percentage/HP text.
    Call :meth:`update_hitpoints` whenever
    its hp value changes; the bar will 
    animate to the new length and
    update its text automatically.
    """

    def __init__(
        self,
        hitpoints: int,
        max_hitpoints: int,
        name: str = '',
        icon_texture: str = 'weegee_icon1',
        position: tuple[float, float] = (0, -290),
        width: float = 500,
        height: float = 45,
    ):
        super().__init__()

        self._width = width
        self._height = height
        self._pos = position
        self._hitpoints = hitpoints
        self._max_hitpoints = max_hitpoints

        self._backing_tex = bs.gettexture('bar')
        self._bar_tex = bs.gettexture('bar')

        self._backing: bs.NodeActor | None = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'scale': (self._width, self._height),
                    'color': (0.1, 0.1, 0.1),
                    'texture': self._backing_tex,
                    'position': position,
                },
            )
        )
        self._bar: bs.NodeActor | None = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'color': (0.1, 0.9, 0.25),
                    'texture': self._bar_tex,
                    'position': position,
                },
            )
        )

        hp_percent = (hitpoints / max_hitpoints) * 100

        self._bar_hp_text = bs.newnode(
            'text',
            owner=self._bar.node,
            attrs={
                'scale': 1.4,
                'color': (0.65, 1, 0.7),
                'opacity': 0.8,
                'text': f'{hp_percent:.0f}%',
                'h_align': 'center',
                'v_align': 'center',
                'position': position,
            },
        )
        self._bar_accurate_hp_text = bs.newnode(
            'text',
            owner=self._bar.node,
            attrs={
                'scale': 0.9,
                'color': (0.4, 0.9, 0.5),
                'opacity': 0.5,
                'text': f'{hitpoints}/{max_hitpoints}',
                'h_align': 'center',
                'v_align': 'center',
                'position': (
                    position[0],
                    position[1] - self._height + 5,
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
                'text': name,
                'h_align': 'center',
                'v_align': 'center',
                'position': (
                    position[0] - (self._width * 0.5) + 90,
                    position[1] + self._height - 3,
                ),
            },
        )
        self._bar_icon = bs.newnode(
            'image',
            owner=self._bar.node,
            attrs={
                'texture': bs.gettexture(icon_texture),
                'scale': (80, 80),
                'position': (
                    position[0] - (self._width * 0.5) + 10,
                    position[1],
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
        self._bar_scale.connectattr('output', self._bar.node, 'scale')

        self._bar_position = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': -self._width / 2,
                'input1': position[1],
            },
        )
        self._bar_position.connectattr('output', self._bar.node, 'position')

        self._bar_width = self._width * (hitpoints / max_hitpoints)

        self._animate_in()
        self.set_length(self._bar_width, time=1)

    def _animate_in(self) -> None:
        assert self._backing is not None and self._bar is not None
        bs.animate(self._backing.node, 'opacity', {0: 0, 0.5: 1})
        bs.animate(self._bar_hp_text, 'opacity', {0: 0, 1: 1})
        bs.animate_array(
            self._bar_name_text,
            'position',
            2,
            {
                0: (-1200, self._bar_name_text.position[1]),
                0.8: self._bar_name_text.position,
            },
        )
        bs.animate_array(
            self._bar_icon,
            'position',
            2,
            {
                0: (-1200, self._bar_icon.position[1]),
                1: self._bar_icon.position,
            },
        )
        bs.animate(
            self._bar_accurate_hp_text,
            'opacity',
            {0: 0, 0.8: 0, 1.7: 1},
        )
        bs.animate(self._bar.node, 'opacity', {0: 0, 0.7: 1})

    def set_length(self, length: float, time: float = 0.2) -> None:
        """Animate the bar's fill."""
        if self._bar is None or self._bar_scale is None:
            return
        self._bar_width = length
        cur_x = self._bar_position.input0
        bs.animate(
            self._bar_position,
            'input0',
            {0: cur_x, time: -self._width / 2 + self._bar_width / 2},
        )
        bs.animate(
            self._bar_scale,
            'input0',
            {0: self._bar_scale.input0, time: length},
        )

    def update_hitpoints(self, hitpoints: int, max_hitpoints: int) -> None:
        """Update the displayed HP values."""
        self._hitpoints = hitpoints
        self._max_hitpoints = max_hitpoints
        self.set_length(self._width * (hitpoints / max_hitpoints))
        if self._bar_accurate_hp_text:
            self._bar_accurate_hp_text.text = (
                f'{hitpoints}/{max_hitpoints}'
            )
        if self._bar_hp_text:
            self._bar_hp_text.text = (
                f'{int((hitpoints / max_hitpoints) * 100)}%'
            )

    def exists(self) -> bool:
        return self._bar is not None

    def handlemessage(self, msg) -> None:
        if isinstance(msg, bs.DieMessage):
            self._backing = None
            self._bar = None
        else:
            super().handlemessage(msg)

class Weegee(bs.Actor):
    """WWEEEEGEEEEEHHHH"""
    def __init__(self):
        super().__init__()
        seshplrs = self.getactivity().session.sessionplayers
        # 6900
        self.hitpoints = self.max_hitpoints = (
            1 * len(seshplrs)
        )
        shared = SharedObjects.get()
        self._scale = scale = 13
        # this is our node, handles 
        # actual damage and stuff
        show_node = False
        self._dead = False
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
            if self.hitpoints < 0:
                self.hitpoints = 0
                if not self._dead:
                    self._dead = True
                    self.getactivity().weegee_beaten()
            # tell activitty to update the bar and such
            self.getactivity()._update_for_stats()
        else:
            return super().handlemessage(msg)
        return None

class WeegeeBossGame(bs.CoopGameActivity[Player, bs.Team]):
    """A gametype where you beat weegee. weegeee."""

    name = 'Weegee Boss'
    description = 'Defeat the Weegee boss.'
    # Print messages when players die since it matters here.
    announce_player_deaths = True
    suppress_zoomtext = True
    scoreconfig = bs.ScoreConfig(
        scoretype=bs.ScoreType.MILLISECONDS, version='B'
    )

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
        self._spawn_center = (0, 5, 1)
        self._hp_bar = None
        self._started = False
        self._starttime_ms = 0
        self._bots = SpazBotSet()
        self._win_sound = bs.getsound('score')
        self._attack_check_timer = None
        bs.getsound('music/weegee')
    
    def tp_spaz(self, spaz: bs.Node):
        pos = (0, 18, -13)
        spaz.handlemessage( 
            'stand',
            pos[0],
            pos[1],
            pos[2],
            90,
        )
    
    def on_begin(self):
        super().on_begin()
        def disable_players():
            for player in self.players:
                if not player.actor:
                    continue
                player.actor.disconnect_controls_from_player()
                if player.actor.node:
                    player.actor.node.is_area_of_interest = False
        disable_players()
    
    def on_transition_in(self):
        super().on_transition_in()
        self._weegee = Weegee()
        spaz = bs.newnode(
            'spaz',
            attrs={'style': 'ali'},
        )
        self._weegee.node.is_area_of_interest = False
        musics = [
            bs.MusicType.WEEGEE_IMPACT1,
            bs.MusicType.WEEGEE_IMPACT2,
            bs.MusicType.WEEGEE_IMPACT3,
            bs.MusicType.WEEGEE_IMPACT4,
        ]
        voiceline = bs.getsound('obey_weegee')
        bs.setmusic(random.choice(musics))
        bs.animate(
            spaz, 
            'area_of_interest_radius',
            {
                0: 5,
                0.5: 8,
                1: 4,
            },
        )
        self._tp_timer = bs.Timer(0.01, bs.Call(self.tp_spaz, spaz), repeat=True)
        time = 4
        bs.timer(time, voiceline.play)
        bs.timer(time + 5.1, self.start)
        bs.timer(time + 5.1, spaz.delete)
        def stop_timer():
            self._tp_timer = None
        bs.timer(time + 5.1, stop_timer)
        
    def start(self):
        for player in self.players:
            if not player.actor:
                continue
            player.actor.connect_controls_to_player()
            if player.actor.node:
                player.actor.node.is_area_of_interest = True
                player.actor.node.area_of_interest_radius = 9
        bs.setmusic(bs.MusicType.WEEGEE)
        self.suppress_zoomtext = False
        self._show_info()
        self._weegee.node.is_area_of_interest = True
        self._weegee.start_bouncy()
        self._starttime_ms = int(0 * 1000.0)
        self._time_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'top',
                    'h_attach': 'center',
                    'h_align': 'center',
                    'color': (1, 1, 0.5, 1),
                    'flatness': 0.5,
                    'shadow': 0.5,
                    'position': (0, -50),
                    'scale': 1.3,
                    'text': '',
                },
            )
        )
        self._time_text_input = bs.NodeActor(
            bs.newnode('timedisplay', attrs={'showsubseconds': True})
        )
        self.globalsnode.connectattr(
            'time', self._time_text_input.node, 'time2'
        )
        self._time_text_input.node.connectattr(
            'output', self._time_text.node, 'text'
        )
        self._attack_check_timer = bs.Timer(0.8, self._attack_check, repeat=True)
        self._hp_bar = HealthBar(
            self._weegee.hitpoints,
            self._weegee.max_hitpoints,
            name='Weegee',
            icon_texture='weegee_icon1',
        )
    
    def weegee_beaten(self):
        self.show_zoom_message(
            bs.Lstr(resource='victoryText'), scale=1.0, duration=4.0
        )
        bs.setmusic(bs.MusicType.COOP_VICTORY)
        bs.cameraflash()
        self._win_sound.play()
        self.celebrate(20.0)
        self._bots.stop_moving()
        self._time_text_timer = None
        self._final_time_ms = int(
            int(bs.time() * 1000.0) - self._starttime_ms
        )
        def do_explosion():
            fac = BombFactory.get()
            
            pos = self._weegee.node.position
            pos = (
                pos[0] + random.uniform(-1.2, 1.2),
                pos[1] + random.uniform(-5, 5),
                pos[2] + random.uniform(-0.2, 0.2),
            )
            sound = fac.random_explode_sound().play(volume=0.86, position=pos)
            explosion = bs.newnode(
                'explosion',
                attrs={
                    'position': pos,
                    'radius': 1.0,
                    'big': False,
                },
            )
            bs.timer(1.0, explosion.delete)
        i = 0
        bs.getsound('screams/scream1').play()
        for _ in range(160):
            bs.timer(i, do_explosion)
            i += 0.08
        msc = self._weegee.visual_node.mesh_scale
        bs.animate(
            self._weegee.visual_node,
            'mesh_scale',
            {
                0: msc,
                4: 0,
            }
        )
            
        self._time_text_input.node.timemax = self._final_time_ms
        self.do_end('victory', delay=5)
        
    def _update_for_stats(self):
        hp = self._weegee.hitpoints
        hp_max = self._weegee.max_hitpoints
        self._hp_bar.update_hitpoints(hp, hp_max)
    
    def _attack_check(self):
        attacks = [
            ('spawn_bots', 0.3),
            ('homing_bomb', 0.6),
        ]
        attack = random.choice(attacks)
        if random.random() < attack[1]: # get attack's chance
            attack = attack[0]
            if attack == 'spawn_bots':
                spawns = self._map.get_def_points('ffa_spawn')
                def spawn():
                    this_spawn = random.choice(spawns)
                    self._bots.spawn_bot(
                        SpazBot,
                        pos=this_spawn[:3],
                        spawn_time=1.6,
                    )
                for i in range(random.randrange(3, 5)):
                    bs.timer(i * 0.05, spawn)
            elif attack == 'homing_bomb':
                for _ in range(len(self.players)):
                    position = (
                        random.uniform(-4.3, 4.3),
                        random.uniform(5, 6),
                        random.uniform(-3.2, 3.2),
                    )
                    velocity = (
                        random.uniform(-0.6, 0.6),
                        random.uniform(-1.5, 0.8),
                        random.uniform(-0.6, 0.6),
                    )
                    Bomb(
                        bomb_type='homing', 
                        fuse_time=6,
                        position=position,
                        velocity=velocity,
                        blast_radius=2.5,
                        bomb_scale=1.45,
                    ).autoretain()
    
    @override
    def spawn_player(self, player: bs.Player):
        pos = (
            self._spawn_center[0] + random.uniform(-1.5, 1.5),
            self._spawn_center[1],
            self._spawn_center[2] + random.uniform(-1.5, 1.5),
        )
        spaz = self.spawn_player_spaz(
            player, 
            position=pos
        )
        return spaz
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            players = len(self.players)
            self.respawn_player(player, respawn_time=4 * players)
            bs.timer(0.1, self._checkroundover)
        else:
            return super().handlemessage(msg)
        return None
    
    @override
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        # Tell our bots to celebrate just to rub it in.
        assert self._bots is not None
        self._game_over = True
        self.do_end('defeat', delay=2.1)
    
    def do_end(self, outcome: str, delay: float = 0.5) -> None:
        """End the game with the specified outcome."""
        if outcome == 'defeat':
            delay = self.fade_to_red()
        score = (
            None if outcome == 'defeat' else int(self._final_time_ms // 10)
        )
        self.end(
            {
                'outcome': outcome,
                'score': score,
                'fail_message': None,
                'playerinfos': self.initialplayerinfos,
            },
            delay=delay,
        )

    def _checkroundover(self) -> None:
        """Potentially end the round based on the state of the game."""
        if self.has_ended():
            return
        if not any(player.is_alive() for player in self.teams[0].players):
            if len(self.players) > 1:
                bs.broadcastmessage( bs.Lstr(resource='clutchTimer') )
                def checkpartfuckin2():
                    if not any(player.is_alive() for player in self.teams[0].players):
                        text = (
                            bs.Lstr(resource='clutchTimerFail2')
                            if random.random() < 0.1 else
                            bs.Lstr(resource='clutchTimerFail')
                        )
                        bs.broadcastmessage(text)
                        self.end_game()
                        for player in self.players:
                            player.respawn_timer = None
                            player.respawn_icon = None
                    else:
                        bs.getsound('player_ready').play()
                bs.timer(3.5, checkpartfuckin2)
            else:
                if not any(player.is_alive() for player in self.teams[0].players):
                    self.end_game()
                    for player in self.players:
                        player.respawn_timer = None
                        player.respawn_icon = None
