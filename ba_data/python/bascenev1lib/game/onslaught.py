# Released under the MIT License. See LICENSE for details.
#
"""Provides Onslaught Co-op game."""

# Yes this is a long one..
# pylint: disable=too-many-lines

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import math
import random
import logging
from enum import Enum, unique
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.popuptext import PopupText
from babase._mgen.enums import InputType
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.bomb import TNTSpawner, Bomb
from bascenev1lib.actor.playerspaz import PlayerSpazHurtMessage
from bascenev1lib.actor.respawnicon import RespawnIcon
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.controlsguide import ControlsGuide
from bascenev1lib.actor.powerupbox import PowerupBox, PowerupBoxFactory
from bascenev1lib.actor.image_looped import LoopingImageAnimation
from bascenev1lib.actor.spazbot import (
    SpazBotDiedMessage,
    SpazBotSet,
    ChargerBot,
    BomberBot,
    BomberBotLite,
    BrawlerBot,
    BrawlerBotLite,
    TriggerBot,
    BomberBotStaticLite,
    TriggerBotStatic,
    BomberBotProStatic,
    TriggerBotPro,
    ExplodeyBot,
    BrawlerBotProShielded,
    ChargerBotProShielded,
    BomberBotPro,
    TriggerBotProShielded,
    BrawlerBotPro,
    BomberBotProShielded,
    LauncherBot
)
from bascenev1lib.actor.cutsceneplayer import CutscenePlayer
from bascenev1lib.dialog import DialogueManager

if TYPE_CHECKING:
    from typing import Any, Sequence
    from bascenev1lib.actor.spazbot import SpazBot


@dataclass
class Wave:
    """A wave of enemies."""

    entries: list[Spawn | Spacing | Delay | None]
    base_angle: float = 0.0


@dataclass
class Spawn:
    """A bot spawn event in a wave."""

    bottype: type[SpazBot] | str
    point: Point | None = None
    spacing: float = 5.0


@dataclass
class Spacing:
    """Empty space in a wave."""

    spacing: float = 5.0


@dataclass
class Delay:
    """A delay between events in a wave."""

    duration: float


class Preset(Enum):
    """Game presets we support."""

    TRAINING = 'training'
    TRAINING_EASY = 'training_easy'
    ROOKIE = 'rookie'
    ROOKIE_EASY = 'rookie_easy'
    PRO = 'pro'
    PRO_EASY = 'pro_easy'
    UBER = 'uber'
    UBER_EASY = 'uber_easy'
    ENDLESS = 'endless'
    ENDLESS_TOURNAMENT = 'endless_tournament'


@unique
class Point(Enum):
    """Points on the map we can spawn at."""

    LEFT_UPPER_MORE = 'bot_spawn_left_upper_more'
    LEFT_UPPER = 'bot_spawn_left_upper'
    TURRET_TOP_RIGHT = 'bot_spawn_turret_top_right'
    RIGHT_UPPER = 'bot_spawn_right_upper'
    TURRET_TOP_MIDDLE_LEFT = 'bot_spawn_turret_top_middle_left'
    TURRET_TOP_MIDDLE_RIGHT = 'bot_spawn_turret_top_middle_right'
    TURRET_TOP_LEFT = 'bot_spawn_turret_top_left'
    TOP_RIGHT = 'bot_spawn_top_right'
    TOP_LEFT = 'bot_spawn_top_left'
    TOP = 'bot_spawn_top'
    BOTTOM = 'bot_spawn_bottom'
    LEFT = 'bot_spawn_left'
    RIGHT = 'bot_spawn_right'
    RIGHT_UPPER_MORE = 'bot_spawn_right_upper_more'
    RIGHT_LOWER = 'bot_spawn_right_lower'
    RIGHT_LOWER_MORE = 'bot_spawn_right_lower_more'
    BOTTOM_RIGHT = 'bot_spawn_bottom_right'
    BOTTOM_LEFT = 'bot_spawn_bottom_left'
    TURRET_BOTTOM_RIGHT = 'bot_spawn_turret_bottom_right'
    TURRET_BOTTOM_LEFT = 'bot_spawn_turret_bottom_left'
    LEFT_LOWER = 'bot_spawn_left_lower'
    LEFT_LOWER_MORE = 'bot_spawn_left_lower_more'
    TURRET_TOP_MIDDLE = 'bot_spawn_turret_top_middle'
    BOTTOM_HALF_RIGHT = 'bot_spawn_bottom_half_right'
    BOTTOM_HALF_LEFT = 'bot_spawn_bottom_half_left'
    TOP_HALF_RIGHT = 'bot_spawn_top_half_right'
    TOP_HALF_LEFT = 'bot_spawn_top_half_left'


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


class Team(bs.Team[Player]):
    """Our team type for this game."""


class OnslaughtGame(bs.CoopGameActivity[Player, Team]):
    """Co-op game where players try to survive attacking waves of enemies."""

    name = 'Onslaught'
    description = 'Defeat all enemies.'

    tips: list[str | bs.GameTip] = [
        'Hold any button to run.'
        '  (Trigger buttons work well if you have them)',
        'Try tricking enemies into killing eachother or running off cliffs.',
        'Try \'Cooking off\' bombs for a second or two before throwing them.',
        'It\'s easier to win with a friend or two helping.',
        'If you stay in one place, you\'re toast. Run and dodge to survive..',
        'Practice using your momentum to throw bombs more accurately.',
        'Your punches do much more damage if you are running or spinning.',
    ]

    # Show messages when players die since it matters here.
    announce_player_deaths = True
    
    # Prevent the Title message from popping up (it kinda makes the game a bit anticlimatic
    suppress_zoomtext = True
    # and also the controls guide (you know how to play right?)
    show_controls_guide = False

    def __init__(self, settings: dict):
        self._last_lap_triggered = None
        
        self._preset = Preset(settings.get('preset', 'training'))
        if self._preset in {
            Preset.TRAINING,
            Preset.TRAINING_EASY,
            Preset.PRO,
            Preset.PRO_EASY,
            Preset.ENDLESS,
            Preset.ENDLESS_TOURNAMENT,
        }:
            settings['map'] = 'Doom Shroom'
        else:
            settings['map'] = 'Courtyard'

        super().__init__(settings)

        self._new_wave_sound = bs.getsound('scoreHit01')
        self._winsound = bs.getsound('score')
        self._cashregistersound = bs.getsound('cashRegister')
        self._a_player_has_been_hurt = False
        self._player_has_dropped_bomb = False

        # FIXME: should use standard map defs.
        if settings['map'] == 'Doom Shroom':
            self._spawn_center = (0, 3, -5)
            self._tntspawnpos = (0.0, 3.0, -5.0)
            self._powerup_center = (0, 5, -3.6)
            self._powerup_spread = (6.0, 4.0)
        elif settings['map'] == 'Courtyard':
            self._spawn_center = (0, 3, -2)
            self._tntspawnpos = (0.0, 3.0, 2.1)
            self._powerup_center = (0, 5, -1.6)
            self._powerup_spread = (4.6, 2.7)
        else:
            raise RuntimeError('Unsupported map: ' + str(settings['map']))
        self._scoreboard: Scoreboard | None = None
        self._game_over = False
        self._wavenum = 0
        self._can_end_wave = True
        self._score = 0
        self._time_bonus = 0
        self._spawn_info_text: bs.NodeActor | None = None
        self._dingsound = bs.getsound('dingSmall')
        self._dingsoundhigh = bs.getsound('dingSmallHigh')
        self._have_tnt = False
        self._excluded_powerups: list[str] | None = None
        self._waves: list[Wave] = []
        self._tntspawner: TNTSpawner | None = None
        self._bots: SpazBotSet | None = None
        self._powerup_drop_timer: bs.Timer | None = None
        self._time_bonus_timer: bs.Timer | None = None
        self._time_bonus_text: bs.NodeActor | None = None
        self._flawless_bonus: int | None = None
        self._wave_text: bs.NodeActor | None = None
        self._wave_update_timer: bs.Timer | None = None
        self._throw_off_kills = 0
        self._land_mine_kills = 0
        self._tnt_kills = 0
        self.timebeforedeath = 60
        self.time_increase = 15
    
    @override
    def on_transition_in(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        super().on_transition_in()
        customdata = bs.getsession().customdata

        # Show special landmine tip on rookie preset.
        if self._preset in {Preset.ROOKIE, Preset.ROOKIE_EASY}:
            # Show once per session only (then we revert to regular tips).
            if not customdata.get('_showed_onslaught_landmine_tip', False):
                customdata['_showed_onslaught_landmine_tip'] = True
                self.tips = [
                    bs.GameTip(
                        'onslaughtMinesTip',
                        icon=bs.gettexture('powerupLandMines'),
                        sound=bs.getsound('ding'),
                    )
                ]

        # Show special tnt tip on pro preset.
        if self._preset in {Preset.PRO, Preset.PRO_EASY}:
            # Show once per session only (then we revert to regular tips).
            if not customdata.get('_showed_onslaught_tnt_tip', False):
                customdata['_showed_onslaught_tnt_tip'] = True
                self.tips = [
                    bs.GameTip(
                        'onslaughtTNTTip',
                        icon=bs.gettexture('tnt'),
                        sound=bs.getsound('ding'),
                    )
                ]

        # Show special curse tip on uber preset.
        if self._preset in {Preset.UBER, Preset.UBER_EASY}:
            # Show once per session only (then we revert to regular tips).
            if not customdata.get('_showed_onslaught_curse_tip', False):
                customdata['_showed_onslaught_curse_tip'] = True
                self.tips = [
                    bs.GameTip(
                        'onslaughtCurseTip',
                        icon=bs.gettexture('powerupCurse'),
                        sound=bs.getsound('ding'),
                    )
                ]

        self._spawn_info_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'position': (15, -130),
                    'h_attach': 'left',
                    'v_attach': 'top',
                    'scale': 0.55,
                    'color': (0.3, 0.8, 0.3, 1.0),
                    'text': '',
                },
            )
        )
        if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
            # Infinite onslaught → always start with LAP0
            bs.setmusic(bs.MusicType.LAP0)
        else:
            # Normal onslaught → pick from standard list
            music_choices = [
                bs.MusicType.ONSLAUGHT,
                bs.MusicType.ONSLAUGHT2,
            ]
            chosen_music = random.choice(music_choices)
            self.chosen_music = chosen_music
            bs.setmusic(chosen_music)
            
            self._scoreboard = Scoreboard(
                label=bs.Lstr(resource='scoreText'), score_split=0.5
            )
            
    def _format_time(self, seconds: int) -> str:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"
        
    def pizza_tick(self):
        self.timebeforedeath -= 1
        self.pizzatimertext.text = self._format_time(self.timebeforedeath)
        if self.timebeforedeath <= 10:
            self.pizzatimertext.color = (1, 0.1, 0.1)
            if self.timer_background:
                self.timer_background.frame_delay = 0.01
            bs.getsound('tick').play()
        else:
            self.pizzatimertext.color = (1, 1, 1)
        if self.timebeforedeath <= 0:
            self._start_bomb_shower()
            if self.timer_background:
                self.timer_background.frame_delay = 6
            def end():
                self.end_game()
                for player in self.players:
                    player.respawn_timer = None
                    player.respawn_icon = None
            bs.timer(0.5, end)
            bs.getsound('crazyOver').play()
            self.tickintimer = None

    def _drop_bomb(
        self, position: Sequence[float], velocity: Sequence[float]
    ) -> None:
        Bomb(position=position, velocity=velocity).autoretain()

    def _drop_bomb_cluster(self) -> None:
        # Drop several bombs in series.
        delay = 0.0
        for _i in range(random.randrange(1, 3)):
            # Drop them somewhere within our bounds with velocity pointing
            # toward the opposite side.
            pos = (
                -7.3 + 15.3 * random.random(),
                5,
                random.randint(-9, 6),
            )
            dropdir = -1.0 if pos[0] > 0 else 1.0
            vel = (
                (-5.0 + random.random() * 30.0) * dropdir,
                random.uniform(-3.066, -4.12),
                random.randint(-4, 3),
            )
            self._drop_bomb(pos, vel)
    
    def _start_bomb_shower(self):
        bs.timer(0.01, self._drop_bomb_cluster, repeat=True)
                
    def _show_pizzatime_sequence(self):
        # let's keep some easy to edit variables here
        size = 0.7
        POS_CENTER = (0, -700)
        POS_TEXT = (-10, -60)
        POS_IMAGE = (0, -650)
        FLOAT_DISTANCE = 2000
        ANIM_TIME = 3.0

        # spawn timer and spaz view offscreen
        self.timer_background = LoopingImageAnimation(
            prefix='evil_timer',
            frame_count=3,
            frame_delay=0.1,
            scale=(512 * size, 256 * size),
            position=POS_CENTER,
            attach='bottomCenter',
        )

        spaz = LoopingImageAnimation(
            prefix='timer_spazstare',
            frame_count=3,
            frame_delay=0.1,
            scale=(512 * size, 256 * size),
            position=POS_CENTER,
            attach='bottomCenter',
        )
        spaz.node.opacity = 0

        # keep them synced
        self.timer_background.node.connectattr('position', spaz.node, 'position')

        # show text
        self.pizzatimertext = bs.newnode('text', attrs={
            'text': self._format_time(self.timebeforedeath),
            'h_align': 'center',
            'v_attach': 'bottom',
            'position': POS_TEXT,
            'scale': size + 1.5,
            'color': (1, 1, 1),
            'shadow': 0.7,
            'flatness': 0.6,
            'opacity': 0,
        })


        # pizza time image!
        self._pizzatime_node = bs.newnode('image', attrs={
            'texture': bs.gettexture('pizzatime1'),
            'position': POS_IMAGE,
            'scale': (410 * size, 410 * size),
            'opacity': 1.0,
            'attach': 'center'
        })


        # texture swapper
        def swap_texture():
            if not self._pizzatime_node.exists():
                return
            tex1 = bs.gettexture('pizzatime1')
            tex2 = bs.gettexture('pizzatime2')
            self._pizzatime_node.texture = tex2 if self._pizzatime_node.texture == tex1 else tex1

        bs.timer(0.05, swap_texture, repeat=True)


        # float animation
        def float_up(node, start_pos):
            x, y = start_pos
            bs.animate_array(node, 'position', 2, {
                0.0: (x, y),
                ANIM_TIME: (x, y + FLOAT_DISTANCE),
            })
            bs.timer(ANIM_TIME, node.delete)

        float_up(self._pizzatime_node, POS_IMAGE)


        # main timer animation
        def pizzatimer():
            # move everything up
            bs.animate_array(self.pizzatimertext, 'position', 2, {
                0.0: POS_TEXT,
                0.5: (POS_TEXT[0], 10 * size),
            })

            bs.animate_array(self.timer_background.node, 'position', 2, {
                0.0: (0, -130 * size),
                0.5: (0, 30 * size),
            })

            # spaz fade
            def animate_spaz():
                bs.animate(spaz.node, 'opacity', {
                    0.0: 0,
                    0.5: 0.7,
                    1.4: 0.7,
                    1.8: 0,
                })

            # text blink + sound
            def animate_text():
                bs.getsound('kwarnin').play()
                bs.animate(self.pizzatimertext, 'opacity', {
                    0.0: 0,
                    0.2: 1,
                    0.4: 0,
                    0.6: 1,
                    0.8: 0,
                    1.0: 1,
                    1.2: 0,
                    1.4: 1,
                })
            bs.timer(0.7, animate_spaz)
            bs.timer(0.5, animate_text)
            self.tickintimer = bs.Timer(1.0, self.pizza_tick, repeat=True)


        bs.timer(ANIM_TIME, pizzatimer)

    
    @override
    def on_begin(self) -> None:
        super().on_begin()        
        self._scoreboard = Scoreboard(
        label=bs.Lstr(resource='scoreText'), score_split=0.5
    )
        if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
            self._show_pizzatime_sequence() # Time to get funkeh!
            for player in self.players:
                if player.character == 'Homer':
                    bs.setmusic(bs.MusicType.LAP0H)
        player_count = len(self.players)
        hard = self._preset not in {
            Preset.TRAINING_EASY,
            Preset.ROOKIE_EASY,
            Preset.PRO_EASY,
            Preset.UBER_EASY,
        }
        if self._preset in {Preset.TRAINING, Preset.TRAINING_EASY}:
            ControlsGuide(delay=3.0, lifespan=10.0, bright=True).autoretain()

            self._have_tnt = False
            self._excluded_powerups = ['curse', 'land_mines']
            self._waves = [
                Wave(
                    base_angle=195,
                    entries=[
                        Spawn(BomberBotLite, spacing=5),
                    ]
                    * player_count,
                ),
                Wave(
                    base_angle=130,
                    entries=[
                        Spawn(BrawlerBotLite, spacing=5),
                    ]
                    * player_count,
                ),
                Wave(
                    base_angle=195,
                    entries=[Spawn(BomberBotLite, spacing=10)]
                    * (player_count + 1),
                ),
                Wave(
                    base_angle=130,
                    entries=[
                        Spawn(BrawlerBotLite, spacing=10),
                    ]
                    * (player_count + 1),
                ),
                Wave(
                    base_angle=130,
                    entries=[
                        (
                            Spawn(BrawlerBotLite, spacing=5)
                            if player_count > 1
                            else None
                        ),
                        Spawn(BrawlerBotLite, spacing=5),
                        Spacing(30),
                        (
                            Spawn(BomberBotLite, spacing=5)
                            if player_count > 3
                            else None
                        ),
                        Spawn(BomberBotLite, spacing=5),
                        Spacing(30),
                        Spawn(BrawlerBotLite, spacing=5),
                        (
                            Spawn(BrawlerBotLite, spacing=5)
                            if player_count > 2
                            else None
                        ),
                    ],
                ),
                Wave(
                    base_angle=195,
                    entries=[
                        Spawn(TriggerBot, spacing=90),
                        (
                            Spawn(TriggerBot, spacing=90)
                            if player_count > 1
                            else None
                        ),
                    ],
                ),
            ]

        elif self._preset in {Preset.ROOKIE, Preset.ROOKIE_EASY}:
            self._have_tnt = False
            self._excluded_powerups = ['curse']
            self._waves = [
                Wave(
                    entries=[
                        (
                            Spawn(ChargerBot, Point.LEFT_UPPER_MORE)
                            if player_count > 2
                            else None
                        ),
                        Spawn(ChargerBot, Point.LEFT_UPPER),
                    ]
                ),
                Wave(
                    entries=[
                        Spawn(BomberBotStaticLite, Point.TURRET_TOP_RIGHT),
                        Spawn(BrawlerBotLite, Point.RIGHT_UPPER),
                        (
                            Spawn(BrawlerBotLite, Point.RIGHT_LOWER)
                            if player_count > 1
                            else None
                        ),
                        (
                            Spawn(
                                BomberBotStaticLite, Point.TURRET_BOTTOM_RIGHT
                            )
                            if player_count > 2
                            else None
                        ),
                    ]
                ),
                Wave(
                    entries=[
                        Spawn(BomberBotStaticLite, Point.TURRET_BOTTOM_LEFT),
                        Spawn(TriggerBot, Point.LEFT),
                        (
                            Spawn(TriggerBot, Point.LEFT_LOWER)
                            if player_count > 1
                            else None
                        ),
                        (
                            Spawn(TriggerBot, Point.LEFT_UPPER)
                            if player_count > 2
                            else None
                        ),
                    ]
                ),
                Wave(
                    entries=[
                        Spawn(BrawlerBotLite, Point.TOP_RIGHT),
                        (
                            Spawn(BrawlerBot, Point.TOP_HALF_RIGHT)
                            if player_count > 1
                            else None
                        ),
                        Spawn(BrawlerBotLite, Point.TOP_LEFT),
                        (
                            Spawn(BrawlerBotLite, Point.TOP_HALF_LEFT)
                            if player_count > 2
                            else None
                        ),
                        Spawn(BrawlerBot, Point.TOP),
                        Spawn(BomberBotStaticLite, Point.TURRET_TOP_MIDDLE),
                    ]
                ),
                Wave(
                    entries=[
                        Spawn(TriggerBotStatic, Point.TURRET_BOTTOM_LEFT),
                        Spawn(TriggerBotStatic, Point.TURRET_BOTTOM_RIGHT),
                        Spawn(TriggerBot, Point.BOTTOM),
                        (
                            Spawn(TriggerBot, Point.BOTTOM_HALF_RIGHT)
                            if player_count > 1
                            else None
                        ),
                        (
                            Spawn(TriggerBot, Point.BOTTOM_HALF_LEFT)
                            if player_count > 2
                            else None
                        ),
                    ]
                ),
                Wave(
                    entries=[
                        Spawn(BomberBotStaticLite, Point.TURRET_TOP_LEFT),
                        Spawn(BomberBotStaticLite, Point.TURRET_TOP_RIGHT),
                        Spawn(ChargerBot, Point.BOTTOM),
                        (
                            Spawn(ChargerBot, Point.BOTTOM_HALF_LEFT)
                            if player_count > 1
                            else None
                        ),
                        (
                            Spawn(ChargerBot, Point.BOTTOM_HALF_RIGHT)
                            if player_count > 2
                            else None
                        ),
                    ]
                ),
            ]

        elif self._preset in {Preset.PRO, Preset.PRO_EASY}:
            self._excluded_powerups = ['curse']
            self._have_tnt = True
            self._waves = [
                Wave(
                    base_angle=-50,
                    entries=[
                        (
                            Spawn(BrawlerBot, spacing=12)
                            if player_count > 3
                            else None
                        ),
                        Spawn(BrawlerBot, spacing=12),
                        Spawn(BomberBot, spacing=6),
                        (
                            Spawn(BomberBot, spacing=6)
                            if self._preset is Preset.PRO
                            else None
                        ),
                        (
                            Spawn(BomberBot, spacing=6)
                            if player_count > 1
                            else None
                        ),
                        Spawn(BrawlerBot, spacing=12),
                        (
                            Spawn(BrawlerBot, spacing=12)
                            if player_count > 2
                            else None
                        ),
                    ],
                ),
                Wave(
                    base_angle=180,
                    entries=[
                        (
                            Spawn(BrawlerBot, spacing=6)
                            if player_count > 3
                            else None
                        ),
                        (
                            Spawn(BrawlerBot, spacing=6)
                            if self._preset is Preset.PRO
                            else None
                        ),
                        Spawn(BrawlerBot, spacing=6),
                        Spawn(ChargerBot, spacing=45),
                        (
                            Spawn(ChargerBot, spacing=45)
                            if player_count > 1
                            else None
                        ),
                        Spawn(BrawlerBot, spacing=6),
                        (
                            Spawn(BrawlerBot, spacing=6)
                            if self._preset is Preset.PRO
                            else None
                        ),
                        (
                            Spawn(BrawlerBot, spacing=6)
                            if player_count > 2
                            else None
                        ),
                    ],
                ),
                Wave(
                    base_angle=0,
                    entries=[
                        Spawn(ChargerBot, spacing=30),
                        Spawn(TriggerBot, spacing=30),
                        Spawn(TriggerBot, spacing=30),
                        (
                            Spawn(TriggerBot, spacing=30)
                            if self._preset is Preset.PRO
                            else None
                        ),
                        (
                            Spawn(TriggerBot, spacing=30)
                            if player_count > 1
                            else None
                        ),
                        (
                            Spawn(TriggerBot, spacing=30)
                            if player_count > 3
                            else None
                        ),
                        Spawn(ChargerBot, spacing=30),
                    ],
                ),
                Wave(
                    base_angle=90,
                    entries=[
                        Spawn(LauncherBot, spacing=50),
                        (
                            Spawn(LauncherBot, spacing=50)
                            if self._preset is Preset.PRO
                            else None
                        ),
                        Spawn(LauncherBot, spacing=50),
                        (
                            Spawn(LauncherBot, spacing=50)
                            if player_count > 1
                            else None
                        ),
                        (
                            Spawn(LauncherBot, spacing=50)
                            if player_count > 3
                            else None
                        ),
                    ],
                ),
                Wave(
                    base_angle=0,
                    entries=[
                        Spawn(TriggerBot, spacing=72),
                        Spawn(TriggerBot, spacing=72),
                        (
                            Spawn(TriggerBot, spacing=72)
                            if self._preset is Preset.PRO
                            else None
                        ),
                        Spawn(TriggerBot, spacing=72),
                        Spawn(TriggerBot, spacing=72),
                        (
                            Spawn(TriggerBot, spacing=36)
                            if player_count > 2
                            else None
                        ),
                    ],
                ),
                Wave(
                    base_angle=30,
                    entries=[
                        Spawn(ChargerBotProShielded, spacing=50),
                        Spawn(ChargerBotProShielded, spacing=50),
                        (
                            Spawn(ChargerBotProShielded, spacing=50)
                            if self._preset is Preset.PRO
                            else None
                        ),
                        (
                            Spawn(ChargerBotProShielded, spacing=50)
                            if player_count > 1
                            else None
                        ),
                        (
                            Spawn(ChargerBotProShielded, spacing=50)
                            if player_count > 2
                            else None
                        ),
                    ],
                ),
            ]

        elif self._preset in {Preset.UBER, Preset.UBER_EASY}:
            # Show controls help in demo or arcade variants.
            variant = bs.app.env.variant
            vart = type(variant)
            arcade_or_demo = variant is vart.ARCADE or variant is vart.DEMO

            if arcade_or_demo:
                ControlsGuide(
                    delay=3.0, lifespan=10.0, bright=True
                ).autoretain()

            self._have_tnt = True
            self._excluded_powerups = []
            self._waves = [
                Wave(
                    entries=[
                        (
                            Spawn(
                                BomberBotProStatic, Point.TURRET_TOP_MIDDLE_LEFT
                            )
                            if hard
                            else None
                        ),
                        Spawn(
                            BomberBotProStatic, Point.TURRET_TOP_MIDDLE_RIGHT
                        ),
                        (
                            Spawn(BomberBotProStatic, Point.TURRET_TOP_LEFT)
                            if player_count > 2
                            else None
                        ),
                        Spawn(ExplodeyBot, Point.TOP_RIGHT),
                        Delay(4.0),
                        Spawn(ExplodeyBot, Point.TOP_LEFT),
                    ]
                ),
                Wave(
                    entries=[
                        Spawn(ChargerBot, Point.LEFT),
                        Spawn(ChargerBot, Point.RIGHT),
                        (
                            Spawn(ChargerBot, Point.RIGHT_UPPER_MORE)
                            if player_count > 2
                            else None
                        ),
                        Spawn(BomberBotProStatic, Point.TURRET_TOP_LEFT),
                        Spawn(BomberBotProStatic, Point.TURRET_TOP_RIGHT),
                    ]
                ),
                Wave(
                    entries=[
                        Spawn(TriggerBotPro, Point.TOP_RIGHT),
                        (
                            Spawn(TriggerBotPro, Point.RIGHT_UPPER_MORE)
                            if player_count > 1
                            else None
                        ),
                        Spawn(TriggerBotPro, Point.RIGHT_UPPER),
                        (
                            Spawn(TriggerBotPro, Point.RIGHT_LOWER)
                            if hard
                            else None
                        ),
                        (
                            Spawn(TriggerBotPro, Point.RIGHT_LOWER_MORE)
                            if player_count > 2
                            else None
                        ),
                        Spawn(TriggerBotPro, Point.BOTTOM_RIGHT),
                    ]
                ),
                Wave(
                    entries=[
                        Spawn(ChargerBotProShielded, Point.BOTTOM_RIGHT),
                        (
                            Spawn(ChargerBotProShielded, Point.BOTTOM)
                            if player_count > 2
                            else None
                        ),
                        Spawn(ChargerBotProShielded, Point.BOTTOM_LEFT),
                        (
                            Spawn(ChargerBotProShielded, Point.TOP)
                            if hard
                            else None
                        ),
                        Spawn(BomberBotProStatic, Point.TURRET_TOP_MIDDLE),
                    ]
                ),
                Wave(
                    entries=[
                        Spawn(ExplodeyBot, Point.LEFT_UPPER),
                        Delay(1.0),
                        Spawn(BrawlerBotProShielded, Point.LEFT_LOWER),
                        Spawn(BrawlerBotProShielded, Point.LEFT_LOWER_MORE),
                        Delay(4.0),
                        Spawn(ExplodeyBot, Point.RIGHT_UPPER),
                        Delay(1.0),
                        Spawn(BrawlerBotProShielded, Point.RIGHT_LOWER),
                        Spawn(BrawlerBotProShielded, Point.RIGHT_UPPER_MORE),
                        Delay(4.0),
                        Spawn(ExplodeyBot, Point.LEFT),
                        Delay(5.0),
                        Spawn(ExplodeyBot, Point.RIGHT),
                    ]
                ),
                Wave(
                    entries=[
                        Spawn(BomberBotProStatic, Point.TURRET_TOP_LEFT),
                        Spawn(BomberBotProStatic, Point.TURRET_TOP_RIGHT),
                        Spawn(BomberBotProStatic, Point.TURRET_BOTTOM_LEFT),
                        Spawn(BomberBotProStatic, Point.TURRET_BOTTOM_RIGHT),
                        (
                            Spawn(
                                BomberBotProStatic, Point.TURRET_TOP_MIDDLE_LEFT
                            )
                            if hard
                            else None
                        ),
                        (
                            Spawn(
                                BomberBotProStatic,
                                Point.TURRET_TOP_MIDDLE_RIGHT,
                            )
                            if hard
                            else None
                        ),
                    ]
                ),
            ]

        # We generate these on the fly in endless.
        elif self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
            self._have_tnt = True
            self._excluded_powerups = []
            self._waves = []

        else:
            raise RuntimeError(f'Invalid preset: {self._preset}')

        # FIXME: Should migrate to use setup_standard_powerup_drops().

        # Spit out a few powerups and start dropping more shortly.
        self._drop_powerups(
            standard_points=True,
            poweruptype=(
                'curse'
                if self._preset in [Preset.UBER, Preset.UBER_EASY]
                else (
                    'land_mines'
                    if self._preset in [Preset.ROOKIE, Preset.ROOKIE_EASY]
                    else None
                )
            ),
        )
        bs.timer(4.0, self._start_powerup_drops)

        # Our TNT spawner (if applicable).
        if self._have_tnt:
            self._tntspawner = TNTSpawner(position=self._tntspawnpos)

        self.setup_low_life_warning_sound()
        self._update_scores()
        self._bots = SpazBotSet()
        if self._preset in {Preset.TRAINING, Preset.TRAINING_EASY}:
            bs.setmusic(bs.MusicType.CUTSCENE1)

            self.cutscene_player = CutscenePlayer(
                cutscene_id=1,
                frame_times=[3, 6, 8, 23, 26],
                end_time=29,
                fade_duration=1.8
            )

            self._music_timer = bs.Timer(30.0, bs.Call(bs.setmusic, self.chosen_music))
            self._wave_timer = bs.Timer(30.0, self._start_updating_waves)
            self._input_timer = bs.Timer(30.0, self.givebackinput)

            self._enable_cutscene_skip()
            
        elif self._preset in {Preset.ROOKIE, Preset.ROOKIE_EASY}:
            bs.setmusic(bs.MusicType.CUTSCENE2)

            self.cutscene_player = CutscenePlayer(
                cutscene_id=2,
                frame_times=[2.0, 2.9, 5, 7.1, 10.2, 11.6, 12.7],
                end_time=13.4,
                fade_duration=0.5
            )
            self._tp_timer = bs.Timer(13.4, self.rookie_teleport)
            self._wave_timer = bs.Timer(16.7, self._start_updating_waves)
            self._input_timer = bs.Timer(15.0, self.givebackinput)
            self._music_timer = bs.Timer(15.0, bs.Call(bs.setmusic, self.chosen_music))

            self._enable_cutscene_skip()

        else:
            bs.timer(2.7, self._start_updating_waves)
            
    def rookie_teleport(self):
        for player in self.players:
            if not player.actor:
                continue
            if not player.actor.node:
                continue
            player.actor.handlemessage(
                bs.StandMessage(
                    (
                        random.randint(-1, 1),
                        10,
                        random.randint(-1, 1)
                    )
                )
            )

    def givebackinput(self):
        for player in self.players:
            player.actor.connect_controls_to_player()
    
    def _skip_cutscene(self, *args, **kwargs):
        # Only skip once
        if getattr(self, '_cutscene_skipped', False):
            return
        self._cutscene_skipped = True

        self._music_timer = None
        self._wave_timer = None
        self._input_timer = None
        self._tp_timer = None
        if self._preset in {Preset.ROOKIE, Preset.ROOKIE_EASY}:
            self.rookie_teleport()
        # Delete cutscene
        if hasattr(self, 'cutscene_player'):
            self.cutscene_player.stop()
        bs.getsound('swish').play()

        # Start gameplay immediately
        bs.setmusic(self.chosen_music)
        self._start_updating_waves()
        self.givebackinput()

    def _enable_cutscene_skip(self):
        # Listen to any button press from any player
        for player in self.players:
            try:
                player.resetinput()
                player.assigninput(
                    (
                        InputType.JUMP_PRESS,
                        InputType.BOMB_PRESS,
                        InputType.PICK_UP_PRESS,
                        InputType.PUNCH_PRESS,
                    ),
                    bs.Call(self._skip_cutscene)
                )
            except: 
                pass

    def _get_dist_grp_totals(self, grps: list[Any]) -> tuple[int, int]:
        totalpts = 0
        totaldudes = 0
        for grp in grps:
            for grpentry in grp:
                dudes = grpentry[1]
                totalpts += grpentry[0] * dudes
                totaldudes += dudes
        return totalpts, totaldudes
    
    def _get_distribution(
        self,
        target_points: int,
        min_dudes: int,
        max_dudes: int,
        group_count: int,
        max_level: int,
    ) -> list[list[tuple[int, int]]]:
        """Calculate a distribution of bad guys given some params."""
        # pylint: disable=too-many-positional-arguments
        max_iterations = 10 + max_dudes * 2

        groups: list[list[tuple[int, int]]] = []
        for _g in range(group_count):
            groups.append([])
        types = [1]
        if max_level > 1:
            types.append(2)
        if max_level > 2:
            types.append(3)
        if max_level > 3:
            types.append(4)
        for iteration in range(max_iterations):
            diff = self._add_dist_entry_if_possible(
                groups, max_dudes, target_points, types
            )

            total_points, total_dudes = self._get_dist_grp_totals(groups)
            full = total_points >= target_points

            if full:
                # Every so often, delete a random entry just to
                # shake up our distribution.
                if random.random() < 0.2 and iteration != max_iterations - 1:
                    self._delete_random_dist_entry(groups)

                # If we don't have enough dudes, kill the group with
                # the biggest point value.
                elif (
                    total_dudes < min_dudes and iteration != max_iterations - 1
                ):
                    self._delete_biggest_dist_entry(groups)

                # If we've got too many dudes, kill the group with the
                # smallest point value.
                elif (
                    total_dudes > max_dudes and iteration != max_iterations - 1
                ):
                    self._delete_smallest_dist_entry(groups)

                # Close enough.. we're done.
                else:
                    if diff == 0:
                        break

        return groups

    def _add_dist_entry_if_possible(
        self,
        groups: list[list[tuple[int, int]]],
        max_dudes: int,
        target_points: int,
        types: list[int],
    ) -> int:
        # See how much we're off our target by.
        total_points, total_dudes = self._get_dist_grp_totals(groups)
        diff = target_points - total_points
        dudes_diff = max_dudes - total_dudes

        # Add an entry if one will fit.
        value = types[random.randrange(len(types))]
        group = groups[random.randrange(len(groups))]
        if not group:
            max_count = random.randint(1, 6)
        else:
            max_count = 2 * random.randint(1, 3)
        max_count = min(max_count, dudes_diff)
        count = min(max_count, diff // value)
        if count > 0:
            group.append((value, count))
            total_points += value * count
            total_dudes += count
            diff = target_points - total_points
        return diff

    def _delete_smallest_dist_entry(
        self, groups: list[list[tuple[int, int]]]
    ) -> None:
        smallest_value = 9999
        smallest_entry = None
        smallest_entry_group = None
        for group in groups:
            for entry in group:
                if entry[0] < smallest_value or smallest_entry is None:
                    smallest_value = entry[0]
                    smallest_entry = entry
                    smallest_entry_group = group
        assert smallest_entry is not None
        assert smallest_entry_group is not None
        smallest_entry_group.remove(smallest_entry)

    def _delete_biggest_dist_entry(
        self, groups: list[list[tuple[int, int]]]
    ) -> None:
        biggest_value = 9999
        biggest_entry = None
        biggest_entry_group = None
        for group in groups:
            for entry in group:
                if entry[0] > biggest_value or biggest_entry is None:
                    biggest_value = entry[0]
                    biggest_entry = entry
                    biggest_entry_group = group
        if biggest_entry is not None:
            assert biggest_entry_group is not None
            biggest_entry_group.remove(biggest_entry)

    def _delete_random_dist_entry(
        self, groups: list[list[tuple[int, int]]]
    ) -> None:
        entry_count = 0
        for group in groups:
            for _ in group:
                entry_count += 1
        if entry_count > 1:
            del_entry = random.randrange(entry_count)
            entry_count = 0
            for group in groups:
                for entry in group:
                    if entry_count == del_entry:
                        group.remove(entry)
                        break
                    entry_count += 1

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        # We keep track of who got hurt each wave for score purposes.
        player.has_been_hurt = False
        pos = (
            self._spawn_center[0] + random.uniform(-1.5, 1.5),
            self._spawn_center[1],
            self._spawn_center[2] + random.uniform(-1.5, 1.5),
        )
        spaz = self.spawn_player_spaz(player, position=pos)
        if self._preset in {
            Preset.TRAINING_EASY,
            Preset.ROOKIE_EASY,
            Preset.PRO_EASY,
            Preset.UBER_EASY,
        }:
            spaz.impact_scale = 0.25
        spaz.add_dropped_bomb_callback(self._handle_player_dropped_bomb)
        return spaz

    def _handle_player_dropped_bomb(
        self, player: bs.Actor, bomb: bs.Actor
    ) -> None:
        del player, bomb  # Unused.
        self._player_has_dropped_bomb = True

    def _drop_powerup(self, index: int, poweruptype: str | None = None) -> None:
        poweruptype = PowerupBoxFactory.get().get_random_powerup_type(
            forcetype=poweruptype, excludetypes=self._excluded_powerups
        )
        if not poweruptype:
            return
        PowerupBox(
            position=self.map.powerup_spawn_points[index],
            poweruptype=poweruptype,
        ).autoretain()

    def _start_powerup_drops(self) -> None:
        self._powerup_drop_timer = bs.Timer(
            3.0, bs.WeakCall(self._drop_powerups), repeat=True
        )

    def _drop_powerups(
        self, standard_points: bool = False, poweruptype: str | None = None
    ) -> None:
        """Generic powerup drop."""
        if standard_points:
            points = self.map.powerup_spawn_points
            for i in range(len(points)):
                bs.timer(
                    1.0 + i * 0.5,
                    bs.WeakCall(
                        self._drop_powerup, i, poweruptype if i == 0 else None
                    ),
                )
        else:
            point = (
                self._powerup_center[0]
                + random.uniform(
                    -1.0 * self._powerup_spread[0],
                    1.0 * self._powerup_spread[0],
                ),
                self._powerup_center[1],
                self._powerup_center[2]
                + random.uniform(
                    -self._powerup_spread[1], self._powerup_spread[1]
                ),
            )
            r = PowerupBoxFactory.get().get_random_powerup_type(
                excludetypes=self._excluded_powerups
            )
            # Drop one random one somewhere.
            PowerupBox(
                position=point,
                poweruptype=r,
            ).autoretain()

    def do_end(self, outcome: str, delay: float = 0.5) -> None:
        """End the game with the specified outcome."""
        if outcome == 'defeat':
            delay = self.fade_to_red()
        score: int | None
        if self._wavenum >= 2:
            score = self._score
            fail_message = None
        else:
            score = None
            fail_message = bs.Lstr(resource='reachWave2Text')
        self.end(
            {
                'outcome': outcome,
                'score': score,
                'fail_message': fail_message,
                'playerinfos': self.initialplayerinfos,
            },
            delay=delay,
        )

    def _award_completion_achievements(self) -> None:
        pass

    def _update_waves(self) -> None:
        # If we have no living bots, go to the next wave.
        assert self._bots is not None
        if (
            self._can_end_wave
            and not self._bots.have_living_bots()
            and not self._game_over
        ):
            self._can_end_wave = False
            self._time_bonus_timer = None
            self._time_bonus_text = None
            if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
                won = False
            else:
                won = self._wavenum == len(self._waves)

            base_delay = 4.0 if won else 0.0

            # Reward time bonus.
            if self._time_bonus > 0:
                bs.timer(0, self._cashregistersound.play)
                bs.timer(
                    base_delay,
                    bs.WeakCall(self._award_time_bonus, self._time_bonus),
                )
                base_delay += 1.0

            # Reward flawless bonus.
            if self._wavenum > 0:
                have_flawless = False
                for player in self.players:
                    if player.is_alive() and not player.has_been_hurt:
                        have_flawless = True
                        bs.timer(
                            base_delay,
                            bs.WeakCall(self._award_flawless_bonus, player),
                        )
                    player.has_been_hurt = False  # reset
                if have_flawless:
                    base_delay += 1.0

            if won:
                self.show_zoom_message(
                    bs.Lstr(resource='victoryText'), scale=1.0, duration=4.0
                )
                self.celebrate(20.0)
                self._award_completion_achievements()
                bs.timer(base_delay, bs.WeakCall(self._award_completion_bonus))
                base_delay += 0.85
                self._winsound.play()
                bs.cameraflash()
                bs.setmusic(bs.MusicType.COOP_VICTORY)
                self._game_over = True

                # Can't just pass delay to do_end because our extra bonuses
                # haven't been added yet (once we call do_end the score
                # gets locked in).
                bs.timer(base_delay, bs.WeakCall(self.do_end, 'victory'))
                return
            # Short celebration after waves.
            if self._wavenum > 1:
                self.celebrate(0.5)
            bs.timer(base_delay, bs.WeakCall(self._start_next_wave))
            if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
                self.tickintimer = None
                self.timebeforedeath += self.time_increase
                self.timer_background.frame_delay = 0.05
                bs.getsound('warTimerUp').play()
                self.pizzatimertext.color = (0.1, 0.9, 0.1)
                self.pizzatimertext.text = self._format_time(self.timebeforedeath)
                def reset():
                    self.timer_background.frame_delay = 0.1
                    self.tickintimer = bs.Timer(1.0, self.pizza_tick, repeat=True)
                bs.timer(0.7, reset)
            self._wavenum += 1

        # Check milestone every 10 waves starting at 20
        if self._wavenum >= 20 and self._wavenum % 10 == 0:
            lap_num = (self._wavenum // 10) - 1  # 20->2, 30->3, etc.
        
            # Only trigger if we haven't already done this lap
            if lap_num != self._last_lap_triggered and lap_num <= 10:
                self._last_lap_triggered = lap_num
                
                bs.getsound("newlapsound").play()
                
                start_pos = (0, 700)
                center_pos = (0, 250)  # visible position
                end_pos = (0, 700)     # back offscreen


                # Show texture oFFscreen
                self._lap_tex = bs.newnode('image',
                    attrs={
                        'texture': bs.gettexture(f"lap{lap_num}"),
                        'position': start_pos,
                        'scale': (400, 400),
                        'opacity': 1.0,
                        'attach': 'center'
                    })
                # this is the animation
                bs.animate_array(self._lap_tex, 'position', 2, {
                    0.0: start_pos,     # the position where we start, basically offscreen
                    3.5: center_pos,    # slide down to the center
                    2.5: center_pos,    # stay for a second
                    4.5: end_pos        # and then we slide back to the start position
                })
                # Delete after animation finishes
                bs.timer(5.1, self._lap_tex.delete)
                music_type = getattr(bs.MusicType, f"LAP{lap_num}") 
                bs.setmusic(music_type)

    def _award_completion_bonus(self) -> None:
        self._cashregistersound.play()
        for player in self.players:
            try:
                if player.is_alive():
                    assert self.initialplayerinfos is not None
                    self.stats.player_scored(
                        player,
                        int(100 / len(self.initialplayerinfos)),
                        scale=1.4,
                        color=(0.6, 0.6, 1.0, 1.0),
                        title=bs.Lstr(resource='completionBonusText'),
                        screenmessage=False,
                    )
            except Exception:
                logging.exception('error in _award_completion_bonus')

    def _award_time_bonus(self, bonus: int) -> None:
        self._cashregistersound.play()
        PopupText(
            bs.Lstr(
                value='+${A} ${B}',
                subs=[
                    ('${A}', str(bonus)),
                    ('${B}', bs.Lstr(resource='timeBonusText')),
                ],
            ),
            color=(1, 1, 0.5, 1),
            scale=1.0,
            position=(0, 3, -1),
        ).autoretain()
        self._score += self._time_bonus
        self.session._total_score += self._time_bonus
        self.session._update_for_arcade()
        self._update_scores()

    def _award_flawless_bonus(self, player: Player) -> None:
        self._cashregistersound.play()
        try:
            if player.is_alive():
                assert self._flawless_bonus is not None
                self.stats.player_scored(
                    player,
                    self._flawless_bonus,
                    scale=1.2,
                    color=(0.6, 1.0, 0.6, 1.0),
                    title=bs.Lstr(resource='flawlessWaveText'),
                    screenmessage=False,
                )
        except Exception:
            logging.exception('error in _award_flawless_bonus')

    def _start_time_bonus_timer(self) -> None:
        self._time_bonus_timer = bs.Timer(
            1.0, bs.WeakCall(self._update_time_bonus), repeat=True
        )

    def _update_player_spawn_info(self) -> None:
        # If we have no living players lets just blank this.
        assert self._spawn_info_text is not None
        assert self._spawn_info_text.node
        if not any(player.is_alive() for player in self.teams[0].players):
            self._spawn_info_text.node.text = ''
        else:
            text: str | bs.Lstr = ''
            for player in self.players:
                if not player.is_alive() and (
                    self._preset in [Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT]
                    or (player.respawn_wave <= len(self._waves))
                ):
                    rtxt = bs.Lstr(
                        resource='onslaughtRespawnText',
                        subs=[
                            ('${PLAYER}', player.getname()),
                        ],
                    )
                    text = bs.Lstr(
                        value='${A}${B}\n',
                        subs=[
                            ('${A}', text),
                            ('${B}', rtxt),
                        ],
                    )
            self._spawn_info_text.node.text = text

    def _respawn_players_for_wave(self) -> None:
        # Respawn applicable players.
        for player in self.players:
            if (
                not player.is_alive()
            ):
                self.spawn_player(player)
        self._update_player_spawn_info()

    def _setup_wave_spawns(self, wave: Wave) -> None:
        tval = 0.0
        dtime = 0.2
        if self._wavenum == 1:
            spawn_time = 3.973
            tval += 0.5
        else:
            spawn_time = 2.648

        bot_angle = wave.base_angle
        self._time_bonus = 0
        self._flawless_bonus = 0
        for info in wave.entries:
            if info is None:
                continue
            if isinstance(info, Delay):
                spawn_time += info.duration
                continue
            if isinstance(info, Spacing):
                bot_angle += info.spacing
                continue
            bot_type_2 = info.bottype
            if bot_type_2 is not None:
                assert not isinstance(bot_type_2, str)
                self._time_bonus += bot_type_2.points_mult * 20
                self._flawless_bonus += bot_type_2.points_mult * 5

            # If its got a position, use that.
            point = info.point
            if point is not None:
                assert bot_type_2 is not None
                spcall = bs.WeakCall(
                    self.add_bot_at_point, point, bot_type_2, spawn_time
                )
                bs.timer(tval, spcall)
                tval += dtime
            else:
                spacing = info.spacing
                bot_angle += spacing * 0.5
                if bot_type_2 is not None:
                    tcall = bs.WeakCall(
                        self.add_bot_at_angle, bot_angle, bot_type_2, spawn_time
                    )
                    bs.timer(tval, tcall)
                    tval += dtime
                bot_angle += spacing * 0.5

        # We can end the wave after all the spawning happens.
        bs.timer(
            tval + spawn_time - dtime + 0.01,
            bs.WeakCall(self._set_can_end_wave),
        )

    def _start_next_wave(self) -> None:
        # This can happen if we beat a wave as we die.
        # We don't wanna respawn players and whatnot if this happens.
        if self._game_over:
            return

        if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
            wave = self._generate_random_wave()
        else:
            wave = self._waves[self._wavenum - 1]
        self._setup_wave_spawns(wave)
        self._update_wave_ui_and_bonuses()
        bs.timer(0.4, self._new_wave_sound.play)

    def _update_wave_ui_and_bonuses(self) -> None:
        self.show_zoom_message(
            bs.Lstr(
                value='${A} ${B}',
                subs=[
                    ('${A}', bs.Lstr(resource='waveText')),
                    ('${B}', str(self._wavenum)),
                ],
            ),
            scale=1.0,
            duration=1.0,
            trail=True,
        )

        # Reset our time bonus.
        tbtcolor = (1, 1, 0, 1)
        tbttxt = bs.Lstr(
            value='${A}: ${B}',
            subs=[
                ('${A}', bs.Lstr(resource='timeBonusText')),
                ('${B}', str(self._time_bonus)),
            ],
        )
        self._time_bonus_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'top',
                    'h_attach': 'center',
                    'h_align': 'center',
                    'vr_depth': -30,
                    'color': tbtcolor,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'position': (0, -60),
                    'scale': 0.8,
                    'text': tbttxt,
                },
            )
        )

        bs.timer(5.0, bs.WeakCall(self._start_time_bonus_timer))
        wtcolor = (1, 1, 1, 1)
        wttxt = bs.Lstr(
            value='${A} ${B}',
            subs=[
                ('${A}', bs.Lstr(resource='waveText')),
                (
                    '${B}',
                    str(self._wavenum)
                    + (
                        ''
                        if self._preset
                        in [Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT]
                        else ('/' + str(len(self._waves)))
                    ),
                ),
            ],
        )
        self._wave_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'top',
                    'h_attach': 'center',
                    'h_align': 'center',
                    'vr_depth': -10,
                    'color': wtcolor,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'position': (0, -40),
                    'scale': 1.3,
                    'text': wttxt,
                },
            )
        )

    def _bot_levels_for_wave(self) -> list[list[type[SpazBot]]]:
        level = self._wavenum
        bot_types = [
            BomberBot,
            BrawlerBot,
            TriggerBot,
            ChargerBot,
            BomberBotPro,
            BrawlerBotPro,
            TriggerBotPro,
            BomberBotProShielded,
            ExplodeyBot,
            ChargerBotProShielded,
            LauncherBot,
            BrawlerBotProShielded,
            TriggerBotProShielded,
        ]
        if level > 5:
            bot_types += [
                ExplodeyBot,
                TriggerBotProShielded,
                BrawlerBotProShielded,
                ChargerBotProShielded,
            ]
        if level > 7:
            bot_types += [
                ExplodeyBot,
                TriggerBotProShielded,
                BrawlerBotProShielded,
                ChargerBotProShielded,
            ]
        if level > 10:
            bot_types += [
                TriggerBotProShielded,
                TriggerBotProShielded,
                TriggerBotProShielded,
                TriggerBotProShielded,
            ]
        if level > 13:
            bot_types += [
                TriggerBotProShielded,
                TriggerBotProShielded,
                TriggerBotProShielded,
                TriggerBotProShielded,
            ]
        bot_levels = [
            [b for b in bot_types if b.points_mult == 1],
            [b for b in bot_types if b.points_mult == 2],
            [b for b in bot_types if b.points_mult == 3],
            [b for b in bot_types if b.points_mult == 4],
        ]

        # Make sure all lists have something in them
        if not all(bot_levels):
            raise RuntimeError('Got empty bot level')
        return bot_levels

    def _add_entries_for_distribution_group(
        self,
        group: list[tuple[int, int]],
        bot_levels: list[list[type[SpazBot]]],
        all_entries: list[Spawn | Spacing | Delay | None],
    ) -> None:
        entries: list[Spawn | Spacing | Delay | None] = []
        for entry in group:
            bot_level = bot_levels[entry[0] - 1]
            bot_type = bot_level[random.randrange(len(bot_level))]
            rval = random.random()
            if rval < 0.5:
                spacing = 10.0
            elif rval < 0.9:
                spacing = 20.0
            else:
                spacing = 40.0
            split = random.random() > 0.3
            for i in range(entry[1]):
                if split and i % 2 == 0:
                    entries.insert(0, Spawn(bot_type, spacing=spacing))
                else:
                    entries.append(Spawn(bot_type, spacing=spacing))
        if entries:
            all_entries += entries
            all_entries.append(Spacing(40.0 if random.random() < 0.5 else 80.0))

    def _generate_random_wave(self) -> Wave:
        level = self._wavenum
        bot_levels = self._bot_levels_for_wave()

        target_points = level * 3 - 2
        min_dudes = min(1 + level // 3, 10)
        max_dudes = min(10, level + 1)
        max_level = (
            4 if level > 6 else (3 if level > 3 else (2 if level > 2 else 1))
        )
        group_count = 3
        distribution = self._get_distribution(
            target_points, min_dudes, max_dudes, group_count, max_level
        )
        all_entries: list[Spawn | Spacing | Delay | None] = []
        for group in distribution:
            self._add_entries_for_distribution_group(
                group, bot_levels, all_entries
            )
        angle_rand = random.random()
        if angle_rand > 0.75:
            base_angle = 130.0
        elif angle_rand > 0.5:
            base_angle = 210.0
        elif angle_rand > 0.25:
            base_angle = 20.0
        else:
            base_angle = -30.0
        base_angle += (0.5 - random.random()) * 20.0
        wave = Wave(base_angle=base_angle, entries=all_entries)
        return wave

    def add_bot_at_point(
        self, point: Point, spaz_type: type[SpazBot], spawn_time: float = 1.0
    ) -> None:
        """Add a new bot at a specified named point."""
        if self._game_over:
            return
        assert isinstance(point.value, str)
        pointpos = self.map.defs.points[point.value]
        assert self._bots is not None
        self._bots.spawn_bot(spaz_type, pos=pointpos, spawn_time=spawn_time)

    def add_bot_at_angle(
        self, angle: float, spaz_type: type[SpazBot], spawn_time: float = 1.0
    ) -> None:
        """Add a new bot at a specified angle (for circular maps)."""
        if self._game_over:
            return
        angle_radians = angle / 57.2957795
        xval = math.sin(angle_radians) * 1.06
        zval = math.cos(angle_radians) * 1.06
        point = (xval / 0.125, 2.3, (zval / 0.2) - 3.7)
        assert self._bots is not None
        self._bots.spawn_bot(spaz_type, pos=point, spawn_time=spawn_time)

    def _update_time_bonus(self) -> None:
        self._time_bonus = int(self._time_bonus * 0.93)
        if self._time_bonus > 0 and self._time_bonus_text is not None:
            assert self._time_bonus_text.node
            self._time_bonus_text.node.text = bs.Lstr(
                value='${A}: ${B}',
                subs=[
                    ('${A}', bs.Lstr(resource='timeBonusText')),
                    ('${B}', str(self._time_bonus)),
                ],
            )
        else:
            self._time_bonus_text = None

    def _start_updating_waves(self) -> None:
        self._wave_update_timer = bs.Timer(
            2.0, bs.WeakCall(self._update_waves), repeat=True
        )

    def _update_scores(self) -> None:
        score = self._score
        assert self._scoreboard is not None
        self._scoreboard.set_team_value(self.teams[0], score, max_score=None)

    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, PlayerSpazHurtMessage):
            msg.spaz.getplayer(Player, True).has_been_hurt = True
            self._a_player_has_been_hurt = True

        elif isinstance(msg, bs.PlayerScoredMessage):
            self._score += msg.score
            self.session._total_score += msg.score
            self.session._update_for_arcade()
            self._update_scores()
            super().handlemessage(msg)

        elif isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            player = msg.getplayer(Player)
            self.respawn_player(player)
            self._a_player_has_been_hurt = True

            # Make note with the player when they can respawn:
            if self._wavenum < 10:
                player.respawn_wave = max(2, self._wavenum + 1)
            elif self._wavenum < 15:
                player.respawn_wave = max(2, self._wavenum + 2)
            else:
                player.respawn_wave = max(2, self._wavenum + 3)
            # Penalty of a few secs if in infinite onslaught
            if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
                self.tickintimer = None
                self.timebeforedeath -= 15
                self.timer_background.frame_delay = 0.03
                bs.getsound('s3kb2').play()
                self.pizzatimertext.color = (0.9, 0.1, 0.1)
                self.pizzatimertext.text = self._format_time(self.timebeforedeath)
                def reset():
                    self.timer_background.frame_delay = 0.1
                    self.tickintimer = bs.Timer(1.0, self.pizza_tick, repeat=True)
                bs.timer(0.8, reset)
                return
            bs.timer(0.1, self._checkroundover)

        elif isinstance(msg, SpazBotDiedMessage):
            pts, importance = msg.spazbot.get_death_points(msg.how)
            if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
                self.tickintimer = None
                self.timebeforedeath += self.time_increase * 0.15 + importance
                self.timebeforedeath = int(self.timebeforedeath)
                self.timer_background.frame_delay = 0.03
                bs.getsound('ding').play()
                self.pizzatimertext.color = (0.1, 0.9, 0.1)
                self.pizzatimertext.text = self._format_time(self.timebeforedeath)
                def reset():
                    self.timer_background.frame_delay = 0.1
                    self.pizza_tick()
                    self.tickintimer = bs.Timer(1.0, self.pizza_tick, repeat=True)
                bs.timer(0.3, reset)
            if msg.killerplayer is not None:
                self._handle_kill_achievements(msg)
                target: Sequence[float] | None
                if msg.spazbot.node:
                    target = msg.spazbot.node.position
                else:
                    target = None

                killerplayer = msg.killerplayer
                self.stats.player_scored(
                    killerplayer,
                    pts,
                    target=target,
                    kill=True,
                    screenmessage=False,
                    importance=importance,
                )
                dingsound = (
                    self._dingsound if importance == 1 else self._dingsoundhigh
                )
                dingsound.play(volume=0.6)

            # Normally we pull scores from the score-set, but if there's
            # no player lets be explicit.
            else:
                self._score += pts
            self._update_scores()
            super().handlemessage(msg)
        else:
            super().handlemessage(msg)

    def _handle_kill_achievements(self, msg: SpazBotDiedMessage) -> None:
        if self._preset in {Preset.TRAINING, Preset.TRAINING_EASY}:
            self._handle_training_kill_achievements(msg)
        elif self._preset in {Preset.ROOKIE, Preset.ROOKIE_EASY}:
            self._handle_rookie_kill_achievements(msg)
        elif self._preset in {Preset.PRO, Preset.PRO_EASY}:
            self._handle_pro_kill_achievements(msg)
        elif self._preset in {Preset.UBER, Preset.UBER_EASY}:
            self._handle_uber_kill_achievements(msg)

    def _handle_uber_kill_achievements(self, msg: SpazBotDiedMessage) -> None:
        # Uber mine achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'land_mine'):
            self._land_mine_kills += 1

        # Uber tnt achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'tnt'):
            self._tnt_kills += 1

    def _handle_pro_kill_achievements(self, msg: SpazBotDiedMessage) -> None:
        # TNT achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'tnt'):
            self._tnt_kills += 1

    def _handle_rookie_kill_achievements(self, msg: SpazBotDiedMessage) -> None:
        # Land-mine achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'land_mine'):
            self._land_mine_kills += 1

    def _handle_training_kill_achievements(
        self, msg: SpazBotDiedMessage
    ) -> None:
        # Toss-off-map achievement:
        if msg.spazbot.last_attacked_type == ('picked_up', 'default'):
            self._throw_off_kills += 1

    def _set_can_end_wave(self) -> None:
        self._can_end_wave = True

    @override
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        # Tell our bots to celebrate just to rub it in.
        assert self._bots is not None
        self._bots.final_celebrate()
        self._game_over = True
        self.do_end('defeat', delay=2.1)

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
                bs.timer(2.0, checkpartfuckin2)
            else:
                if not any(player.is_alive() for player in self.teams[0].players):
                    self.end_game()
                    for player in self.players:
                        player.respawn_timer = None
                        player.respawn_icon = None
