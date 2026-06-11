# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to co-op games."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, override

import babase

import _bascenev1
from bascenev1._gameactivity import GameActivity
import fromgoverhaul.mell_resources as mell
import bascenev1 as bs
import random
import babase as ba
import json
import urllib.request
import urllib.parse
import math
from babase._logging import squdalog
SERVER = mell.server

if TYPE_CHECKING:
    from typing import Sequence

    from bascenev1lib.actor.playerspaz import PlayerSpaz

    import bascenev1


# Note: Need to suppress an undefined variable here because our pylint
# plugin clears type-arg declarations (which we don't require to be
# present at runtime) but keeps parent type-args (which we sometimes use
# at runtime).


class CoopGameActivity[PlayerT: bs.Player, TeamT: bs.Team](
    GameActivity[PlayerT, TeamT]  # pylint: disable=undefined-variable
):
    """Base class for cooperative-mode games."""

    # We can assume our session is a CoopSession.
    session: bascenev1.CoopSession

    @override
    @classmethod
    def supports_session_type(
        cls, sessiontype: type[bascenev1.Session]
    ) -> bool:
        from bascenev1._coopsession import CoopSession

        return issubclass(sessiontype, CoopSession)

    def __init__(self, settings: dict):
        super().__init__(settings)

        # Cache these for efficiency.
        self._achievements_awarded: set[str] = set()

        self._life_warning_beep: bascenev1.Actor | None = None
        self._life_warning_beep_timer: bascenev1.Timer | None = None
        self._warn_beeps_sound = _bascenev1.getsound('warnBeeps')
        self.ultrameter = None

    @override
    def on_begin(self) -> None:
        super().on_begin()

        # Show achievements remaining.

        variant = babase.app.env.variant
        vart = type(variant)
        arcade_or_demo = variant is vart.ARCADE or variant is vart.DEMO

        if not arcade_or_demo:
            _bascenev1.timer(
                3.8, babase.WeakCall(self._show_remaining_achievements)
            )
        self._sb_lasthittype = None
        self._sb_lastsubhittype = None
        meter_type = babase.app.config.get('squda_ultrameter')
        self.doultrameter = meter_type != 'disabled'
        if self.doultrameter:
            from bascenev1lib.actor.ultrakillmeter import UltrakillMeter
            self.ultrameter = UltrakillMeter(compact = meter_type == 'basic')

        # Preload achievement images in case we get some.
        _bascenev1.timer(2.0, babase.WeakCall(self._preload_achievements))
        if self.hardmode:
            musics = [
                bs.MusicType.HARDMODE1,
                bs.MusicType.HARDMODE2,
                bs.MusicType.HARDMODE3,
            ]
            bs.setmusic(random.choice(musics))

    # "FIXME: this is now redundant with activityutils.getscoreconfig();
    #  need to kill this."
    # #stopkillingfunctions
    # #andalsostopmakingredundantfunctions
    def get_score_type(self) -> str:
        """
        Return the score unit this co-op game uses ('point', 'seconds', etc.)
        """
        return 'points'

    def _get_coop_level_name(self) -> str:
        assert self.session.campaign is not None
        return self.session.campaign.name + ':' + str(self.settings_raw['name'])

    def celebrate(self, duration: float) -> None:
        """Tells all existing player-controlled characters to celebrate.

        Can be useful in co-op games when the good guys score or complete
        a wave.
        duration is given in seconds.
        """
        from bascenev1._messages import CelebrateMessage

        for player in self.players:
            if player.actor:
                player.actor.handlemessage(CelebrateMessage(duration))

    def _preload_achievements(self) -> None:
        assert babase.app.classic is not None
        achievements = babase.app.classic.ach.achievements_for_coop_level(
            self._get_coop_level_name()
        )
        for ach in achievements:
            ach.get_icon_texture(True)

    def _show_remaining_achievements(self) -> None:
        # pylint: disable=cyclic-import
        from bascenev1lib.actor.text import Text

        assert babase.app.classic is not None
        ts_h_offs = 30
        v_offs = -200
        achievements = [
            a
            for a in babase.app.classic.ach.achievements_for_coop_level(
                self._get_coop_level_name()
            )
            if not a.complete
        ]
        vrmode = babase.app.env.vr
        if achievements:
            Text(
                babase.Lstr(resource='achievementsRemainingText'),
                host_only=True,
                position=(ts_h_offs - 10 + 40, v_offs - 10),
                transition=Text.Transition.FADE_IN,
                scale=1.1,
                h_attach=Text.HAttach.LEFT,
                v_attach=Text.VAttach.TOP,
                color=(1, 1, 1.2, 1) if vrmode else (0.8, 0.8, 1.0, 1.0),
                flatness=1.0 if vrmode else 0.6,
                shadow=1.0 if vrmode else 0.5,
                transition_delay=0.0,
                transition_out_delay=1.3 if self.slow_motion else 4.0,
            ).autoretain()
            hval = 70
            vval = -50
            tdelay = 0.0
            for ach in achievements:
                tdelay += 0.05
                ach.create_display(
                    hval + 40,
                    vval + v_offs,
                    0 + tdelay,
                    outdelay=1.3 if self.slow_motion else 4.0,
                    style='in_game',
                )
                vval -= 55

    @override
    def spawn_player_spaz(
        self,
        player: PlayerT,
        position: Sequence[float] = (0.0, 0.0, 0.0),
        angle: float | None = None,
    ) -> PlayerSpaz:
        """Spawn and wire up a standard player spaz."""
        spaz = super().spawn_player_spaz(player, position, angle)

        # Deaths are noteworthy in co-op games.
        spaz.play_big_death_sound = True
        spaz.broadcast_death = True
        return spaz

    def _award_achievement(
        self, achievement_name: str, sound: bool = True
    ) -> None:
        """Award an achievement.

        Returns True if a banner will be shown;
        False otherwise
        """

        classic = babase.app.classic
        plus = babase.app.plus
        if classic is None or plus is None:
            logging.warning(
                '_award_achievement is a no-op without classic and plus.'
            )
            return

        if achievement_name in self._achievements_awarded:
            return

        ach = classic.ach.get_achievement(achievement_name)

        # If we're in the easy campaign and this achievement is hard-mode-only,
        # ignore it.
        try:
            campaign = self.session.campaign
            assert campaign is not None
            if ach.hard_mode_only and campaign.name == 'Easy':
                return
        except Exception:
            logging.exception('Error in _award_achievement.')

        # If we haven't awarded this one, check to see if we've got it.
        # If not, set it through the game service *and* add a transaction
        # for it.
        if not ach.complete:
            self._achievements_awarded.add(achievement_name)

            # Report new achievements to the game-service.
            plus.report_achievement(achievement_name)

            # Now bring up a celebration banner.
            ach.announce_completion(sound=sound)

    def fade_to_red(self):
        """Fade the screen to red; (such as when the good guys have lost)."""
        from bascenev1 import _gameutils
        
        player1 = self.players[0]
        assert isinstance(player1, ba.Player)
        p1name = player1.getname()
        
        bs.broadcastmessage(
            bs.Lstr(
                resource='coopPlayerLost',
                subs=[('${NAME}', p1name)],
            ), 
            color=(1.0,0.1,0.1),
        )
        bs.setmusic(bs.MusicType.COOP_LOSS, show_playing=False)

        c_existing = self.globalsnode.tint
        cnode = _bascenev1.newnode(
            'combine',
            attrs={
                'input0': c_existing[0],
                'input1': c_existing[1],
                'input2': c_existing[2],
                'size': 3,
            },
        )
        _gameutils.animate(cnode, 'input1', {0: c_existing[1], 2.0: 0})
        _gameutils.animate(cnode, 'input2', {0: c_existing[2], 2.0: 0})
        cnode.connectattr('output', self.globalsnode, 'tint')
        delay = 4
        return delay

    def setup_low_life_warning_sound(self) -> None:
        """Set up a beeping noise to play when any players are near death."""
        self._life_warning_beep = None
        self._life_warning_beep_timer = _bascenev1.Timer(
            1.0, babase.WeakCall(self._update_life_warning), repeat=True
        )

    def _update_life_warning(self) -> None:
        # Beep continuously if anyone is close to death.
        should_beep = False
        for player in self.players:
            if player.is_alive():
                # FIXME: Should abstract this instead of
                #  reading hitpoints directly.
                maxhp = getattr(player.actor, 'hitpoints_max', 999)
                hp = getattr(player.actor, 'hitpoints', 999)
                if hp < maxhp / 3:
                    should_beep = True
                    break
        if should_beep and self._life_warning_beep is None:
            from bascenev1._nodeactor import NodeActor

            self._life_warning_beep = NodeActor(
                _bascenev1.newnode(
                    'sound',
                    attrs={
                        'sound': self._warn_beeps_sound,
                        'positional': False,
                        'loop': True,
                    },
                )
            )
        if self._life_warning_beep is not None and not should_beep:
            self._life_warning_beep = None
    @override
    def end(
        self, results: Any = None, delay: float = 0.0, force: bool = False
    ) -> None:
        if self.hardmode:
            level = self._get_coop_level_name()
            tdict = bs.app.config.get('squda_coop_levels_beaten_hardmode', {})
            if level not in tdict or not tdict.get('level'):
                bs.getsound('gooditem').play(volume=0.8)
            tdict[level] = True
        if not results.get('fail_message'):
            for player in self.players:
                char = bs.app.classic.spaz_appearances[
                    player.character
                ]
                tr = mell.translate_char_name
                if char.is_gimmick_character:
                    results['score'] = None
                    results['fail_message'] = bs.Lstr(
                        r='failGimmickCharacter',
                        s=[('${CHAR}', tr(player.character))],
                    )
        super().end(results, delay, force)
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        # Ouch. Hurts to do a import here, but we have to...
        from bascenev1lib.actor.spazbot import SpazBotDiedMessage, SpazBotHitMessage
        from bascenev1lib.actor.spaz import ShatteredMessage, HeadExplodedMessage, ParriedMessage
        from bascenev1lib.actor.bomb import ReturnMessage
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        if isinstance(msg, SpazBotHitMessage):
            if msg.types == (self._sb_lasthittype, self._sb_lastsubhittype):
                if self.ultrameter:
                    self.ultrameter.add_freshness(-15)
            else:
                if self.ultrameter:
                    self.ultrameter.add_freshness(10)
            self._sb_lasthittype, self._sb_lastsubhittype = msg.types
        elif isinstance(msg, bs.PlayerScoredMessage):
            if self.ultrameter:
                self.ultrameter.style_text(bs.Lstr(resource='stylePScored'), msg.score * 2, (1, 1, 0))
        elif isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            if self.ultrameter:
                self.ultrameter.style_text(bs.Lstr(resource='stylePDied'), -15, (0.5, 0.1, 0.1))
        elif isinstance(msg, SpazBotDiedMessage):
            if msg.types:
                hittype, subhittype = msg.types
            else:
                hittype = None
                subhittype = None
            if hittype == 'explosion' and msg.killerplayer:
                player = msg.killerplayer.actor
                bot = msg.spazbot
                distance = math.dist(bot.node.position, player.node.position)
                if distance >= 6.9:
                    if self.ultrameter:
                        self.ultrameter.style_text(bs.Lstr(resource='styleSniped'), 50, (0, 0.5, 0.8))
            if self.ultrameter:
                self.ultrameter.style_text(bs.Lstr(resource='styleKilled'), 30, (1, 0.1, 0.1))
        elif isinstance(msg, ShatteredMessage):
            if self.ultrameter:
                self.ultrameter.style_text(bs.Lstr(resource='styleShattered'), 40, (0.9, 0, 0.6))
        elif isinstance(msg, HeadExplodedMessage):
            if self.ultrameter:
                self.ultrameter.style_text(bs.Lstr(resource='styleHexploded'), 60, (1, 0.1, 0.1))
        elif isinstance(msg, ParriedMessage):
            if self.ultrameter:
                self.ultrameter.style_text(bs.Lstr(resource='styleParry'), 30, (0, 1, 0))
        elif isinstance(msg, ReturnMessage):
            if self.ultrameter:
                self.ultrameter.style_text(bs.Lstr(resource='styleReturned'), 70, (0, 1.3, 0.2))
        else:
            super().handlemessage(msg) # Augment standard behavior.
            
        super().handlemessage(msg) # Shouldn't happen; but still augment.
