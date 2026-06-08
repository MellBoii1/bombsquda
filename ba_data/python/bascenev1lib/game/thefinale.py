# Released under the MIT License. See LICENSE for details.
#
"""
Defines The Finale coop level.
This is specifically just Last Stand with minor adjustments,
so i dunno lamafao!
"""

from __future__ import annotations

import random
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, override
from bascenev1lib.actor import spazbot
import bascenev1 as bs
import time
import babase as ba

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.bomb import TNTSpawner
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.powerupbox import PowerupBoxFactory, PowerupBox
from bascenev1lib.actor.overhead_text import OverheadText
from bascenev1lib.actor.particles import ConfettiParticle
from bascenev1lib.actor.nodejumper import ImageJumper
# Fuck it, ralsieBot is back. If we want hard...
# ..we GET HARD. 
from bascenev1lib.actor.spazbot import (
    SpazBotSet,
    SpazBotDiedMessage,
    BomberBot,
    BomberBotPro,
    BomberBotProShielded,
    BrawlerBot,
    BrawlerBotPro,
    BrawlerBotProShielded,
    TriggerBot,
    TriggerBotPro,
    TriggerBotProShielded,
    ChargerBot,
    StickyBot,
    ExplodeyBot,
    KNIGHTBot,
    RaymanBot,
    LauncherBot,
    ralsieBot,
    MelisoBot,
    BuddieBot,
)

if TYPE_CHECKING:
    from typing import Any, Sequence

    from bascenev1lib.actor.spazbot import SpazBot


@dataclass
class SpawnInfo:
    """Spawning info for a particular bot type."""

    spawnrate: float
    increase: float
    dincrease: float


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self):
        super().__init__()
        self.respawn_timer: bs.Timer = None
        self.respawn_icon: object = None



class Team(bs.Team[Player]):
    """Our team type for this game."""


class TheFinaleGame(bs.CoopGameActivity[Player, Team]):
    """Slow motion how-long-can-you-last game."""

    name = 'The Finale'
    description = 'fucking parrying simulator'
    tips = [
        'theFinaleTip1',
        'theFinaleTip2',
        'theFinaleTip3',
        'theFinaleTip4',
    ]
    # Announce when players die (particularly VERY important here)
    announce_player_deaths = True
    # prevent gong from playing (i don't like it.)
    suppress_gong = True
    

    def __init__(self, settings: dict):
        settings['map'] = 'Football Stadium'
        super().__init__(settings)
        self._new_wave_sound = bs.getsound('scoreHit01')
        self._winsound = bs.getsound('score')
        self._cashregistersound = bs.getsound('cashRegister')
        self._spawn_center = (-5, 2.5, -5.14)
        self._tntspawnpos = (0, 5.5, 0.30)
        self._powerup_center = (0, 2, 0.0)
        self._powerup_spread = (7, 2)
        self._preset = str(settings.get('preset', 'default'))
        self._excludepowerups: list[str] = []
        self._scoreboard: Scoreboard | None = None
        self._score = 0
        self.points_to_win = 1300
        self._bots = SpazBotSet()
        self._dingsound = bs.getsound('dingSmall')
        self._dingsoundhigh = bs.getsound('dingSmallHigh')
        self._tntspawner: TNTSpawner | None = None
        self._bot_update_interval: float | None = None
        self._bot_update_timer: bs.Timer | None = None
        self._powerup_drop_timer = None
        self._alrdidach1 = False
        self._alrdidach2 = False
        self._alrdidach3 = False
        self._ended_in = None
        self.easymode = settings['easy_mode']
        self.win_music_override = bs.MusicType.VICTORYFINAL

        # For each bot type: [spawnrate, increase, d_increase]
        self._bot_spawn_types = {
            BomberBot: SpawnInfo(1.00, 0.00, 0.000),
            BomberBotPro: SpawnInfo(0.00, 0.05, 0.001),
            BomberBotProShielded: SpawnInfo(0.00, 0.02, 0.002),
            BrawlerBot: SpawnInfo(1.00, 0.00, 0.000),
            BrawlerBotPro: SpawnInfo(0.00, 0.05, 0.001),
            BrawlerBotProShielded: SpawnInfo(0.05, 0.02, 0.002),
            TriggerBot: SpawnInfo(0.30, 0.00, 0.000),
            TriggerBotPro: SpawnInfo(0.10, 0.05, 0.001),
            LauncherBot: SpawnInfo(0.10, 0.05, 0.001),
            TriggerBotProShielded: SpawnInfo(0.00, 0.02, 0.002),
            ChargerBot: SpawnInfo(0.40, 0.05, 0.000),
            RaymanBot: SpawnInfo(0.40, 0.05, 0.000),
            KNIGHTBot: SpawnInfo(0.00, 0.01, 0.01),
            StickyBot: SpawnInfo(0.10, 0.03, 0.001),
            ExplodeyBot: SpawnInfo(0.10, 0.02, 0.002),
            ralsieBot: SpawnInfo(0.10, 0.04, 0.002),
            MelisoBot: SpawnInfo(0.07, 0.03, 0.002),
            BuddieBot: SpawnInfo(0.15, 0.08, 0.0015),
        }

    @override
    def on_transition_in(self) -> None:
        # (Pylint bug?) pylint: disable=missing-function-docstring

        super().on_transition_in()
        self._scoreboard = Scoreboard(
            label=bs.Lstr(resource='scoreText'), score_split=0.5
        )

    @override
    def on_begin(self) -> None:
        super().on_begin()
        # Spit out a few powerups and start dropping more shortly.
        self._drop_powerups(standard_points=True)
        bs.timer(2.0, bs.WeakCall(self._start_powerup_drops))
        bs.timer(0.001, bs.WeakCall(self._start_bot_updates))
        self.setup_low_life_warning_sound()
        self._tntspawner = TNTSpawner(
            position=self._tntspawnpos, respawn_time=10.0
        )
        OverheadText(bs.Lstr(
            resource='finaleOverhead',
            subs=[
                    ('${NAME}', self.players[0].actor.node.name)
                ]
            )
        )
        random_musicas = [
            bs.MusicType.THEFINALE,
            bs.MusicType.FINALDESTINATION,
            bs.MusicType.WAR,
            bs.MusicType.EPIC_RACE,
            bs.MusicType.LAP4,
            bs.MusicType.LAP2,
            bs.MusicType.LAP3
            
        ]
        self.points_text = bs.newnode(
                'text',
                attrs={
                    'v_attach': 'top',
                    'h_attach': 'center',
                    'h_align': 'center',
                    'vr_depth': -10,
                    'color': (1, 1, 1),
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'position': (0, -40),
                    'scale': 1.3,
                    'text': '',
                },
            )
        ct = self.globalsnode.tint
        bs.animate_array(
            self.globalsnode, 
            'tint', 
            3,
            {
                0.4: (0, 0, 0),
                0.65: ct,
                0.9: (ct[0] * 1.5, ct[1] * 1.5, ct[2] * 1.5),
                1.1: ct,
            }
        )
        bs.animate(self.points_text, 'opacity',
            {
                1.1: 0,
                1.5: 1,
            }
        )
        bs.timer(0.9, lambda: bs.setmusic( random.choice( random_musicas ) ) )
        self._update_scores()

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        # (Pylint bug?) pylint: disable=missing-function-docstring
        pos = (
            self._spawn_center[0] + random.uniform(4, 4),
            self._spawn_center[1],
            self._spawn_center[2] + random.uniform(6, 3),
        )
        spaz = self.spawn_player_spaz(player, position=pos)
        bs.timer(0.22, lambda: spaz.gosuper(shouldntsetmusic=True))
        if self.easymode == True:
            spaz.impact_scale = 0.7
        return 

    def _start_bot_updates(self) -> None:
        time = (
            4.3 if self.easymode
            else 3.3
        )
        self._bot_update_interval = time - 0.3 * (len(self.players))
        if self._bot_update_interval <= 0:
            self._bot_update_interval = 1.2
        self._bot_update_timer = bs.Timer(
            self._bot_update_interval, bs.WeakCall(self._update_bots)
        )
        self._update_bots()
        if not self.easymode:
            self._update_bots()
            self._update_bots()
        if len(self.players) >= 2:
            self._update_bots()
            self._update_bots()
        if len(self.players) >= 4:
            self._update_bots()

    def _drop_powerup(self, index: int, poweruptype: str | None = None) -> None:
        if poweruptype is None:
            poweruptype = PowerupBoxFactory.get().get_random_powerup_type(
                excludetypes=self._excludepowerups
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
        self, standard_points: bool = False, force_first: str | None = None
    ) -> None:
        """Generic powerup drop."""
        from bascenev1lib.actor import powerupbox

        if standard_points:
            pts = self.map.powerup_spawn_points
            for i in range(len(pts)):
                bs.timer(
                    1.0 + i * 0.5,
                    bs.WeakCall(
                        self._drop_powerup, i, force_first if i == 0 else None
                    ),
                )
        else:
            drop_pt = (
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
                excludetypes=self._excludepowerups
            )
            # Drop one random one somewhere.
            powerupbox.PowerupBox(
                position=drop_pt,
                poweruptype=r
            ).autoretain()
            
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

    def do_end(self, outcome: str, delay: float = 0.0) -> None:
        """End the game."""
        if outcome == 'defeat':
            delay = self.fade_to_red()
        self._ended_in = outcome
        self.end(
            delay=delay,
            results={
                'outcome': outcome,
                'score': self._score,
                'playerinfos': self.initialplayerinfos,
            },
        )

    def _update_bots(self) -> None:
        assert self._bot_update_interval is not None
        self._bot_update_interval = max(0.45, self._bot_update_interval * 1.0)
        self._bot_update_timer = bs.Timer(
            self._bot_update_interval, bs.WeakCall(self._update_bots)
        )
        botspawnpts: list[Sequence[float]] = [
            [-9.0, 2.0, 0.14],
            [1.0, 0.0, -5.14],
            [8.0, 1.5, 1.14],
        ]
        dists = [1.0, 1.7, 0.7]
        playerpts: list[Sequence[float]] = []
        for player in self.players:
            try:
                if player.is_alive():
                    assert isinstance(player.actor, PlayerSpaz)
                    assert player.actor.node
                    playerpts.append(player.actor.node.position)
            except Exception:
                logging.exception('Error updating bots.')
        for i in range(3):
            for playerpt in playerpts:
                dists[i] += abs(playerpt[0] - botspawnpts[i][0])
            dists[i] += random.random() * 5.0  # Minor random variation.
        if dists[0] > dists[1] and dists[0] > dists[2]:
            spawnpt = botspawnpts[0]
        elif dists[1] > dists[2]:
            spawnpt = botspawnpts[1]
        else:
            spawnpt = botspawnpts[2]

        spawnpt = (
            spawnpt[0] + 3.0 * (random.random() - 0.5),
            spawnpt[1],
            2.0 * (random.random() - 0.5) + spawnpt[2],
        )

        # Normalize our bot type total and find a random number within that.
        total = 0.0
        for spawninfo in self._bot_spawn_types.values():
            total += spawninfo.spawnrate
        randval = random.random() * total

        # Now go back through and see where this value falls.
        total = 0
        bottype: type[SpazBot] | None = None
        for spawntype, spawninfo in self._bot_spawn_types.items():
            total += spawninfo.spawnrate
            if randval <= total:
                bottype = spawntype
                break
        spawn_time = 1.0
        assert bottype is not None
        self._bots.spawn_bot(bottype, pos=spawnpt, spawn_time=spawn_time)

        # After every spawn we adjust our ratios slightly to get more
        # difficult.
        for spawninfo in self._bot_spawn_types.values():
            spawninfo.spawnrate += spawninfo.increase
            spawninfo.increase += spawninfo.dincrease
    
    def _drop_confetti(
        self, position: Sequence[float], velocity: Sequence[float]
    ) -> None:
        actor = ConfettiParticle(position=position, spaz_type='').autoretain()
        actor.node.velocity = velocity
        

    def _drop_confetti_cluster(self) -> None:
        # Drop several bombs in series.
        delay = 0.0
        if random.random() < 0.13:
            bs.getsound('default_win').play()
        for _i in range(random.randrange(1, 3)):
            # Drop them somewhere within our bounds with velocity pointing
            # toward the opposite side.
            pos = (
                random.randint(-6, 6),
                5,
                random.randint(-9, 6),
            )
            dropdir = -1.0 if pos[0] > 0 else 1.0
            vel = (
                (-5.0 + random.random() * 50.0) * dropdir,
                random.uniform(-3.066, 2),
                random.randint(-3, 3),
            )
            self._drop_confetti(pos, vel)
    
    def _start_confetti_shower(self):
        bs.timer(0.06, self._drop_confetti_cluster, repeat=True)

    def _update_scores(self) -> None:
        score = self._score

        if score >= self.points_to_win:
            if not getattr(self, '_game_over', False):
                self._game_over = True
                self.show_zoom_message(
                    bs.Lstr(resource='victoryText'), scale=1.0, duration=3.0
                )
                self.celebrate(20.0)
                self._bot_update_timer = None
                self._bots.clearslowly()
                bs.cameraflash()
                for player in self.players:
                    player.actor.say()
                bs.setmusic(None)
                bs.getsound('finaleWin').play()
                for player in self.players:
                    if getattr(player.actor, 'earthchar', None):
                        time = 1.0
                        def do_it(time: int, node: bs.Node):
                            ImageJumper.jump_to_position(
                                node,
                                target_pos=node.position,
                                time=time,
                                height=150,
                            )
                        player.actor.earthchar.texture = player.actor.media['EBwin']
                        do_it(time=time, node=player.actor.earthchar)
                        self.ahhhtimers = []
                        self.ahhhtimers.append(
                            bs.Timer(
                                time + 0.01, 
                                bs.Call(
                                    do_it, 
                                    time=time, 
                                    node=player.actor.earthchar
                                ), 
                                repeat=True
                            )
                        )
                bs.timer(0.5, self._start_confetti_shower)
                time = 12.6
                self.do_end(delay=time, outcome='victory')
                bs.app.classic.ach.award_local_achievement('I am the BombSquad:tm:')
                self.points_text.text = 'yuo\'re winner :)'
                return
        assert self._scoreboard is not None
        self._scoreboard.set_team_value(self.teams[0], score, max_score=None)
        ptext_lstr = bs.Lstr(
            resource='finalePoints',
            subs=[
                ('${NUM}', str(self.points_to_win - self._score)),
            ],
        )
        self.points_text.text = ptext_lstr
        if score >= 650:
            if self._alrdidach2 == True:
                return
            self._alrdidach2 = True
            bs.app.classic.ach.award_local_achievement('The Halfway Mark')
            OverheadText(bs.Lstr(resource='finaleOverhead3'))
        if score >= 350:
            if self._alrdidach1 == True:
                return
            self._alrdidach1 = True
            bs.app.classic.ach.award_local_achievement('A Long Way')
            OverheadText(bs.Lstr(resource='finaleOverhead2'))

    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            player = msg.getplayer(Player)
            self.stats.player_was_killed(player)
            # Respawn them shortly.
            from bascenev1lib.actor.respawnicon import RespawnIcon
            assert self.initialplayerinfos is not None
            respawn_time = 7.0 * len(self.initialplayerinfos)
            player.respawn_timer = bs.Timer(
                respawn_time, bs.Call(self.spawn_player_if_exists, player)
            )
            player.respawn_icon = RespawnIcon(player, respawn_time)
            if self._ended_in != 'victory':
                bs.timer(0.1, self._checkroundover)
            super().handlemessage(msg)

        elif isinstance(msg, bs.PlayerScoredMessage):
            self._score += msg.score
            self._update_scores()
            super().handlemessage(msg)

        elif isinstance(msg, SpazBotDiedMessage):
            pts, importance = msg.spazbot.get_death_points(msg.how)
            target: Sequence[float] | None
            if msg.killerplayer:
                assert msg.spazbot.node
                target = msg.spazbot.node.position
                self.stats.player_scored(
                    msg.killerplayer,
                    pts,
                    target=target,
                    kill=True,
                    screenmessage=False,
                    importance=importance,
                )
                diesound = (
                    self._dingsound if importance == 1 else self._dingsoundhigh
                )
                diesound.play(volume=0.6)

            # Normally we pull scores from the score-set, but if there's no
            # player lets be explicit.
            else:
                self._score += pts
            self._update_scores()
            super().handlemessage(msg)
        else:
            super().handlemessage(msg)

    @override
    def end_game(self) -> None:
        # (Pylint bug?) pylint: disable=missing-function-docstring
        assert self._bots is not None
        self._bots.final_celebrate()
        bs.pushcall(bs.WeakCall(self.do_end, 'defeat', delay=2.1))

    def _checkroundover(self) -> None:
        """End the round if conditions are met."""
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
                bs.timer(4.5, checkpartfuckin2)
            else:
                if not any(player.is_alive() for player in self.teams[0].players):
                    self.end_game()
                    for player in self.players:
                        player.respawn_timer = None
                        player.respawn_icon = None
