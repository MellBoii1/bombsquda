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
from .weegee_healthbar import HealthBar
from .weegee_actor import Weegee

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

class WeegeeBossGame(bs.CoopGameActivity[Player, bs.Team]):
    """A gametype where you beat weegee. weegeee."""

    name = 'Weegee Boss'
    # note: should remove keyword 'boss' here?? 
    # sounds really monotone and unnecessary
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
            elif attack == 'toasters':
                for _ in range(len(self.players)):
                    position = (
                        random.uniform(-4.3, 4.3),
                        random.uniform(6, 8),
                        random.uniform(-3.2, 3.2),
                    )
    
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
