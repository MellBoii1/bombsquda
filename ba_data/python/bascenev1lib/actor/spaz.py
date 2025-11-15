# Released under the MIT License. See LICENSE for details.
#
"""
this is spaz node. it is the character. 
however. it is not skin.
skin in spazappearance.
"""
# pylint: disable=too-many-lines

from __future__ import annotations

import random
import logging
from typing import TYPE_CHECKING, override
from bascenev1lib.actor.text import Text

import bascenev1 as bs
import baclassic as bsc
import bascenev1lib.actor.bomb as bomb
import math
import os
from bascenev1lib.actor.popuptext import PopupText
from bascenev1lib.actor import spazappearance
import bascenev1lib.actor.spazappearance as spazappearance
from bascenev1._gameactivity import GameActivity

from bascenev1lib.actor.bomb import Bomb, Blast
from bascenev1lib.actor.powerupbox import PowerupBoxFactory, PowerupBox
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.gameutils import SharedObjects
import babase as ba

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable

POWERUP_WEAR_OFF_TIME = 27000
POWERUP_WEAR_OFF_TIME2 = 45000
POWERUP_WEAR_OFF_TIME3 = 10000

# Obsolete - just used for demo guy now.
BASE_PUNCH_POWER_SCALE = 1.2
BASE_PUNCH_COOLDOWN = 400


class PickupMessage:
    """We wanna pick something up."""


class PunchHitMessage:
    """Message saying an object was hit."""


class CurseExplodeMessage:
    """We are cursed and should blow up now."""


class BombDiedMessage:
    """A bomb has died and thus can be recycled."""


class Spaz(bs.Actor):
    """
    Base class for various Spazzes.

    A Spaz is the standard little humanoid character in the game.
    It can be controlled by a player or by AI, and can have
    various different appearances.  The name 'Spaz' is not to be
    confused with the 'Spaz' character in the game, which is just
    one of the skins available for instances of this class.
    """

    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-locals

    node: bs.Node
    """The 'spaz' bs.Node."""

    points_mult = 1
    curse_time: float | None = 5.0
    default_bomb_count = 1
    default_bomb_type = 'normal'
    default_boxing_gloves = False
    default_boxing_gloves_stronger = False
    default_shields = False
    default_shields_stronger = False
    default_hitpoints = 1000 # Originally, i was gonna make it so you were beefier and had more hitpoints, 
                             # but this breaks the NOT GONNA SUGARCOAT IT* logic.
    
    def __init__(
        self,
        *,
        color: Sequence[float] = (1.0, 1.0, 1.0),
        highlight: Sequence[float] = (0.5, 0.5, 0.5),
        character: str = 'Spaz',
        source_player: bs.Player | None = None,
        start_invincible: bool = True,
        can_accept_powerups: bool = True,
        powerups_expire: bool = False,
        demo_mode: bool = False,
    ):
        """Create a spaz with the requested color, character, etc."""
        # pylint: disable=too-many-statements

        super().__init__()
        shared = SharedObjects.get()
        activity = self.activity

        factory = SpazFactory.get()

        # We need to behave slightly different in the tutorial.
        self._demo_mode = demo_mode

        # Specific settings for alerting if a spaz died.
        self.play_big_death_sound = False
        self.broadcast_death = False
        
        self.impact_scale = 1.0
        
        self._roulette_active = False
        self._roulette_timer = None
        self._roulette_current = None

        self.source_player = source_player
        self._dead = False
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 1.2
        else:
            self._punch_power_scale = 1.0
        self.fly = bs.getactivity().globalsnode.happy_thoughts_mode
        if isinstance(activity, bs.GameActivity):
            self._hockey = activity.map.is_hockey
        else:
            self._hockey = False
        self._punched_nodes: set[bs.Node] = set()
        self._cursed = False
        self._connected_to_player: bs.Player | None = None
        materials = [
            factory.spaz_material,
            shared.object_material,
            shared.player_material,
        ]
        roller_materials = [factory.roller_material, shared.player_material]
        extras_material = []
        self.issuper = False
        self.dashing = False

        if can_accept_powerups:
            pam = PowerupBoxFactory.get().powerup_accept_material
            materials.append(pam)
            roller_materials.append(pam)
            extras_material.append(pam)

        media = factory.get_media(character)
        punchmats = (factory.punch_material, shared.attack_material)
        pickupmats = (factory.pickup_material, shared.pickup_material)
        self.node: bs.Node = bs.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': color,
                'behavior_version': 0 if demo_mode else 1,
                'demo_mode': demo_mode,
                'highlight': highlight,
                'jump_sounds': media['jump_sounds'],
                'attack_sounds': media['attack_sounds'],
                'impact_sounds': media['impact_sounds'],
                'death_sounds': media['death_sounds'],
                'pickup_sounds': media['pickup_sounds'],
                'fall_sounds': media['fall_sounds'],
                'color_texture': media['color_texture'],
                'color_mask_texture': media['color_mask_texture'],
                'head_mesh': media['head_mesh'],
                'torso_mesh': media['torso_mesh'],
                'pelvis_mesh': media['pelvis_mesh'],
                'upper_arm_mesh': media['upper_arm_mesh'],
                'forearm_mesh': media['forearm_mesh'],
                'hand_mesh': media['hand_mesh'],
                'upper_leg_mesh': media['upper_leg_mesh'],
                'lower_leg_mesh': media['lower_leg_mesh'],
                'toes_mesh': media['toes_mesh'],
                'style': factory.get_style(character),
                'fly': self.fly,
                'hockey': self._hockey,
                'materials': materials,
                'roller_materials': roller_materials,
                'extras_material': extras_material,
                'punch_materials': punchmats,
                'pickup_materials': pickupmats,
                'invincible': start_invincible,
                'source_player': source_player,
            },
        )
        self.shield: bs.Node | None = None

        if start_invincible:

            def _safesetattr(node: bs.Node | None, attr: str, val: Any) -> None:
                if node:
                    setattr(node, attr, val)

            bs.timer(1.5, bs.Call(_safesetattr, self.node, 'invincible', False))
        # ask if our player's config has spazhardmode on, and
        # if our spaz has a source player (defines if they're a bot or not)
        # then set our hitpoints to 1 (to well, make it hard)
        if ba.app.config.get("spazhardmode", True) and not source_player == None:
            self.hitpoints = 1
            self.hitpoints_max = 1  
            # ew, we have to do this in a timer otherwise it'll break...
            bs.timer(0.2, lambda: PopupText(
                "HARDMODE ON!!!",
                position=self.node.position,
                color=(1, 0.1, 0.1, 1),
                scale=1.1,
            ).autoretain())
            bs.getsound('hardmode').play()
        # otherwise, just do normal behaviour
        else:
            self.hitpoints = self.default_hitpoints
            self.hitpoints_max = self.default_hitpoints
            
        self.shield_hitpoints: int | None = None
        self.shield_hitpoints_max = 650
        self.shield_hitpoints_stronger_max = 1400
        self.shield_decay_rate = 0
        self.shield_decay_timer: bs.Timer | None = None
        self._boxing_gloves_wear_off_timer: bs.Timer | None = None
        self._boxing_gloves_wear_off_flash_timer: bs.Timer | None = None
        self._bomb_wear_off_timer: bs.Timer | None = None
        self._bomb_wear_off_flash_timer: bs.Timer | None = None
        self._multi_bomb_wear_off_timer: bs.Timer | None = None
        self._multi_bomb_wear_off_flash_timer: bs.Timer | None = None
        self._curse_timer: bs.Timer | None = None
        self.bomb_count = self.default_bomb_count
        self._max_bomb_count = self.default_bomb_count
        self.bomb_type_default = self.default_bomb_type
        self.bomb_type = self.bomb_type_default
        self.land_mine_count = 0
        self.parrying = False
        self.canparry = False
        self.canparry2 = True
        self.instructimage = None
        self.cansay = False
        self.lasthittype = None
        self.timesparried = 0
        self.timesparriedtotal = 0
        self.blast_radius = 2.0
        self.powerups_expire = powerups_expire
        if self._demo_mode:  # Preserve old behavior.
            self._punch_cooldown = BASE_PUNCH_COOLDOWN
        else:
            self._punch_cooldown = 450
        self._jump_cooldown = 0
        self._pickup_cooldown = 0
        self._bomb_cooldown = 0
        self._has_boxing_gloves = False
        if self.default_boxing_gloves:
            self.equip_boxing_gloves()
        if self.default_boxing_gloves_stronger:
            self.equip_boxing_gloves_stronger()
        self.last_punch_time_ms = -9999
        self.last_pickup_time_ms = -9999
        self.last_jump_time_ms = -9999
        self.last_run_time_ms = -9999
        self._last_run_value = 0.0
        self.last_bomb_time_ms = -9999
        self._turbo_filter_times: dict[str, int] = {}
        self._turbo_filter_time_bucket = 0
        self._turbo_filter_counts: dict[str, int] = {}
        self.earthhptext = None
        self.earthsptext = None
        self.earthmeter = None
        self.earthchar = None
        self.earthmetertext = None
        self.frozen = False
        self.shattered = False
        self._has_metalcap = False
        self._last_hit_time: int | None = None
        self._num_times_hit = 0
        self._bomb_held = False
        if self.default_shields:
            self.equip_shields()
        if self.default_shields_stronger:
            self.equip_shields_stronger()
        self._has_hot_potato = False
        self._dropped_bomb_callbacks: list[Callable[[Spaz, bs.Actor], Any]] = []
        if self.source_player:
            players = bs.getactivity().players
            normalmeterx = -670
            multiplier = 150
            if players.index(self.source_player) == 0:
                self.meterx = normalmeterx + multiplier
                self.metery = -300
            elif players.index(self.source_player) == 1:
                self.meterx = normalmeterx + multiplier * 2
                self.metery = -300
            elif players.index(self.source_player) == 2:
                self.meterx = normalmeterx + multiplier * 3
                self.metery = -300
            elif players.index(self.source_player) == 3:
                self.meterx = normalmeterx + multiplier * 4
                self.metery = -300
            elif players.index(self.source_player) == 4:
                self.meterx = normalmeterx + multiplier * 5
                self.metery = -300
            elif players.index(self.source_player) == 5:
                self.meterx = normalmeterx + multiplier * 6
                self.metery = -300
            elif players.index(self.source_player) == 6:
                self.meterx = normalmeterx + multiplier * 7
                self.metery = -300
            elif players.index(self.source_player) == 7:
                self.meterx = normalmeterx + multiplier * 8
                self.metery = -300
            else:
                self.meterx = -9999
                self.metery = -9999


        self._score_text: bs.Node | None = None
        self._score_text_hide_timer: bs.Timer | None = None
        self._last_stand_pos: Sequence[float] | None = None

        # Deprecated stuff.. should make these into lists.
        self.punch_callback: Callable[[Spaz], Any] | None = None
        self.pick_up_powerup_callback: Callable[[Spaz], Any] | None = None
        self.flashing = False
        self._flash_timer = None
        
        if self.source_player: # Prevent tutorial from dying.
            if self.character == 'Robot': # bombgeon snake shadow
                # Now define snake shadow's specific attrs
                self.dashcooldown = bs.Timer(3, self.NINJA_increase, repeat=True)
                self.NINJA_DASHES = 2
                self.hitpoints = 320
                self.hitpoints_max = 320
                self.shield_hitpoints_max = 150
                self.impact_scale = 0.5
                self.alrdidtext = False
                self._punch_power_scale = 1.04
                self._jump_cooldown = 0.27
                self.pasheal_timer = bs.Timer(1.5, self.passiveheal, repeat=True)
            if ba.app.config.get("parryalways", True) and not source_player == None:
                self.canparry = True
            if self.character == 'Spaz':
                # Easter egg for a few 'eye shade' guys
                def checkifkrissyndrom():
                    krissy = ['Masked Man', 'Kris', 'Varik']
                    if self.node.name in krissy:
                        self.node.color_texture = bs.gettexture('neoSpazColor2')
                        self.node.color_mask_texture = bs.gettexture('neoSpazColorMask2')
                bs.timer(0.2, checkifkrissyndrom)
                # because buddie and gummy asked me to keep it
                def checkifpeakeyes():
                    if ba.app.config.get("spazfuckedup", True) and not source_player == None:
                        self.node.color_texture = bs.gettexture('fuckedupspaz')
                bs.timer(0.21, checkifpeakeyes)
            char_name = getattr(self, 'character', None)
            if char_name:
                appearances = bs.app.classic.spaz_appearances
                if char_name in appearances:
                    appearance = appearances[char_name]
                    if hasattr(appearance, 'earthportrait') and appearance.earthportrait:
                        self.charimage = appearance.earthportrait
                    else:
                        self.charimage = appearance.icon_texture
            # Do earthbound-y hp visualizer thing.
            def doearthmeter():
                self.earthchar = bs.newnode('image', 
                    attrs={
                        'texture': bs.gettexture(self.charimage),
                        'absolute_scale': True,
                        'position': (self.meterx, self.metery),
                        'attach': 'center',
                        'opacity': 1.0,
                        'scale': (80, 80),
                        'color': (1, 1, 1)
                    }
                )
                self.earthmeter = bs.newnode('image', 
                    attrs={
                        'texture': bs.gettexture('earthmeter'),
                        'absolute_scale': True,
                        'position': (self.meterx, self.metery),
                        'attach': 'center',
                        'opacity': 1.0,
                        'scale': (150, 150),
                        'color': (1, 1, 1)
                    }
                )
                self.earthmetertext = bs.newnode(
                    'text',
                    attrs={
                        'text': self.node.name,
                        'h_align': 'center',
                        'position': (self.meterx, self.metery + 25),
                        'scale': 0.7,
                        'color': (1, 1, 1),
                        'shadow': 0.7,
                        'flatness': 0.6,
                    },
                )
                self.earthhptext = bs.newnode(
                    'text',
                    attrs={
                        'text': str(int(self.hitpoints / 10)),
                        'h_align': 'center',
                        'position': (self.meterx + 18, self.metery - 16),
                        'scale': 0.9,
                        'color': (1, 1, 1),
                        'shadow': 0.7,
                        'flatness': 0.6,
                    },
                )
            if ba.app.config.get("enablemeter", True):
                bs.timer(0.2, doearthmeter)
                
    @override
    def exists(self) -> bool:
        return bool(self.node)

    @override
    def on_expire(self) -> None:
        super().on_expire()

        # Release callbacks/refs so we don't wind up with dependency loops.
        self._dropped_bomb_callbacks = []
        self.punch_callback = None
        self.pick_up_powerup_callback = None

    def add_dropped_bomb_callback(
        self, call: Callable[[Spaz, bs.Actor], Any]
    ) -> None:
        """
        Add a call to be run whenever this Spaz drops a bomb.
        The spaz and the newly-dropped bomb are passed as arguments.
        """
        assert not self.expired
        self._dropped_bomb_callbacks.append(call)

    @override
    def is_alive(self) -> bool:
        """
        Method override; returns whether ol' spaz is still kickin'.
        """
        return not self._dead

    def _hide_score_text(self) -> None:
        if self._score_text:
            assert isinstance(self._score_text.scale, float)
            bs.animate(
                self._score_text,
                'scale',
                {0.0: self._score_text.scale, 0.2: 0.0},
            )

    def _turbo_filter_add_press(self, source: str) -> None:
        """
        Can pass all button presses through here; if we see an obscene number
        of them in a short time let's shame/pushish this guy for using turbo.
        """
        t_ms = int(bs.basetime() * 1000.0)
        assert isinstance(t_ms, int)
        t_bucket = int(t_ms / 1000)
        if t_bucket == self._turbo_filter_time_bucket:
            # Add only once per timestep (filter out buttons triggering
            # multiple actions).
            if t_ms != self._turbo_filter_times.get(source, 0):
                self._turbo_filter_counts[source] = (
                    self._turbo_filter_counts.get(source, 0) + 1
                )
                self._turbo_filter_times[source] = t_ms
                # (uncomment to debug; prints what this count is at)
                # bs.broadcastmessage( str(source) + " "
                #                   + str(self._turbo_filter_counts[source]))
                if self._turbo_filter_counts[source] == 15 and not self._dead:
                    # WHY just knock em out? at this rate, we'll explode them and have them die
                    assert self.node
                    Blast(
                        position=self.node.position,
                        velocity=self.node.velocity,
                        blast_radius=0.6,
                        blast_type='tnt',
                        source_player= None
                    )
                    bs.getsound('boo').play()
                    ba.app.classic.ach.award_local_achievement(
                        'Turbo'
                    )
                    self.shatter()

                    # show whoever's turboing
                    now = bs.apptime()
                    assert bs.app.classic is not None
                    if now > bs.app.classic.last_spaz_turbo_warn_time + 1.5:
                        bs.app.classic.last_spaz_turbo_warn_time = now
                        bs.broadcastmessage(
                            bs.Lstr(
                                translate=(
                                    'statements',
                                    (
                                        'Warning to ${NAME}: '
                                        'you\'re fucking stupid.' # IMAGINE turboing. IMAGINE.
                                        ''
                                    ),
                                ),
                                subs=[('${NAME}', self.node.name)],
                            ),
                            color=(1, 0.5, 0),
                        )
        else:
            self._turbo_filter_times = {}
            self._turbo_filter_time_bucket = t_bucket
            self._turbo_filter_counts = {source: 1}

    def set_score_text(
        self,
        text: str | bs.Lstr,
        color: Sequence[float] = (1.0, 1.0, 0.4),
        flash: bool = False,
    ) -> None:
        """
        Utility func to show a message momentarily over our spaz that follows
        him around; Handy for score updates and things.
        """
        color_fin = bs.safecolor(color)[:3]
        if not self.node:
            return
        if not self._score_text:
            start_scale = 0.0
            mnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 1.4, 0), 'operation': 'add'},
            )
            self.node.connectattr('torso_position', mnode, 'input2')
            self._score_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': text,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': color_fin,
                    'scale': 0.02,
                    'h_align': 'center',
                },
            )
            mnode.connectattr('output', self._score_text, 'position')
        else:
            self._score_text.color = color_fin
            assert isinstance(self._score_text.scale, float)
            start_scale = self._score_text.scale
            self._score_text.text = text
        if flash:
            combine = bs.newnode(
                'combine', owner=self._score_text, attrs={'size': 3}
            )
            scl = 1.8
            offs = 0.5
            tval = 0.300
            for i in range(3):
                cl1 = offs + scl * color_fin[i]
                cl2 = color_fin[i]
                bs.animate(
                    combine,
                    'input' + str(i),
                    {0.5 * tval: cl2, 0.75 * tval: cl1, 1.0 * tval: cl2},
                )
            combine.connectattr('output', self._score_text, 'color')

        bs.animate(self._score_text, 'scale', {0.0: start_scale, 0.2: 0.02})
        self._score_text_hide_timer = bs.Timer(
            1.0, bs.WeakCall(self._hide_score_text)
        )
        
    def set_cansay(self):
        self.cansay = True
        def setfalse():
            self.cansay = False
        bs.timer(1.0, setfalse)

    def on_jump_press(self) -> None:
        """
        Called to 'press jump' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        if self.cansay == True:
            self.say(wave=True)
        if self.dashing == True:
            if self.issuper == True:
                xforce = 1
                yforce = 150
                self.dashing = False
                v = self.node.velocity
                self.node.handlemessage('impulse', 
                                        self.node.position[0], 
                                        self.node.position[1], 
                                        self.node.position[2],
                                        0, 25, 0,
                                        yforce, 0.05, 0, 0,
                                        0, 20*400, 0)
                bs.timer(0.01, lambda: self.node.handlemessage('impulse', 
                                        self.node.position[0], 
                                        self.node.position[1], 
                                        self.node.position[2],
                                        0, 25, 0,
                                        yforce, 0.05, 0, 0,
                                        0, 20*400, 0))
                bs.timer(0.1, lambda: self.node.handlemessage('impulse', 
                        self.node.position[0], 
                        self.node.position[1], 
                        self.node.position[2],
                        0, 25, 0,
                        yforce, 0.05, 0, 0,
                        0, 20*400, 0))
                bs.getsound('zoeJump01').play()
                return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_jump_time_ms >= self._jump_cooldown:
            self.node.jump_pressed = True
            self.last_jump_time_ms = t_ms
        self._turbo_filter_add_press('jump')

    def on_jump_release(self) -> None:
        """
        Called to 'release jump' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        self.node.jump_pressed = False
    
    def parry(self):
        """
        Called upon when attempting a parry;
        Will set a value for some seconds that determines
        whether the player is in the parry timeframe.
        """
        # If we're not allowed to parry here, most likely on cooldown.
        # Return and don't do anything.
        if self.canparry2 == False:
            return
        # Set important values.
        self.canparry2 = False
        self.parrying = True
        def stopparry():
            self.parrying = False
        def letparryagain():
            self.canparry2 = True
        if ba.app.config.get("parrytype") == 3:
            parrytime = 0.3
            parrycooldown = 0.8
        if ba.app.config.get("parrytype") == 2:
            parrytime = 0.2
            parrycooldown = 0.6
        if ba.app.config.get("parrytype") == 1:
            parrytime = 0.1
            parrycooldown = 0.4
        # Close our parry timeframe after our chosen second(s).
        bs.timer(parrytime, stopparry)
        # After some seconds, let us parry again. This is our cooldown.
        bs.timer(parrycooldown, letparryagain)
        # 'Celebrate' to show we're parrying, n play a sound.
        self.node.handlemessage('celebrate', int(100))
        bs.getsound('parry').play()

    def on_pickup_press(self) -> None:
        """
        Called to 'press pick-up' on this spaz;
        used by player or AI connections.
        """
        if self._roulette_active:
            # If gambling, give our item to the player.
            self.giveitem()
            return
        if self.canparry == True:
            # If we can parry, replace our pickup button with parrying.
            self.parry()
            return
        if not self.node:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_pickup_time_ms >= self._pickup_cooldown:
            self.node.pickup_pressed = True
            self.last_pickup_time_ms = t_ms
        self._turbo_filter_add_press('pickup')

    def on_pickup_release(self) -> None:
        """
        Called to 'release pick-up' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        self.node.pickup_pressed = False

    def on_hold_position_press(self) -> None:
        """
        Called to 'press hold-position' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.hold_position_pressed = True
        self._turbo_filter_add_press('holdposition')

    def on_hold_position_release(self) -> None:
        """
        Called to 'release hold-position' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.hold_position_pressed = False

    def on_punch_press(self) -> None:
        """
        Called to 'press punch' on this spaz;
        used for player or AI connections.
        """
        if not self.node or self.frozen or self.node.knockout > 0.0:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_punch_time_ms >= self._punch_cooldown:
            if self.punch_callback is not None:
                self.punch_callback(self)
            self._punched_nodes = set()  # Reset this.
            self.last_punch_time_ms = t_ms
            self.node.punch_pressed = True
            if not self.node.hold_node:
                bs.timer(
                    0.1,
                    bs.WeakCall(
                        self._safe_play_sound,
                        SpazFactory.get().swish_sound,
                        0.8,
                    ),
                )
        self._turbo_filter_add_press('punch')
        
    def explode(self) -> None:
        """
        Explodes our spaz if 
        we're asked to.
        """
        if self.node:
            bs.getsound('wackyplatform').play()
            pos = self.node.position
            xforce = 0
            yforce = 200
            v = self.node.velocity
            self.node.handlemessage('impulse', self.node.position[0], self.node.position[1], self.node.position[2],
                                    0, 25, 0,
                                    yforce, 0.05, 0, 0,
                                    0, 20*400, 0)
            bs.timer(0.0001, lambda: self.node.handlemessage('impulse', self.node.position[0], self.node.position[1], self.node.position[2],
                                    0, 25, 0,
                                    yforce, 0.05, 0, 0,
                                    0, 20*400, 0)
                    )
            bs.timer(0.001, lambda: self.node.handlemessage('impulse', self.node.position[0], self.node.position[1], self.node.position[2],
                                    0, 25, 0,
                                    yforce, 0.05, 0, 0,
                                    0, 20*400, 0)
                    )
            bs.timer(0.01, lambda: self.node.handlemessage('impulse', self.node.position[0], self.node.position[1], self.node.position[2],
                                    0, 25, 0,
                                    yforce, 0.05, 0, 0,
                                    0, 20*400, 0)
                    )
            self.node.handlemessage('impulse', self.node.position[0], self.node.position[1], self.node.position[2],
                                    0, 25, 0,
                                    xforce, 0.05, 0, 0,
                                        v[0]*15*2, 0, v[2]*15*2)
            bs.timer(0.6, lambda: bomb.Bomb(position=self.node.position, bomb_type='tnt').explode())
            bs.timer(0.6, lambda: self.node and self.node.handlemessage(
                bs.getsound('retired').play(),
                bs.DieMessage()
                )
            )

    def _safe_play_sound(self, sound: bs.Sound, volume: float) -> None:
        """Plays a sound at our position if we exist."""
        if self.node:
            sound.play(volume, self.node.position)

    def on_punch_release(self) -> None:
        """
        Called to 'release punch' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.punch_pressed = False
        
    def giveitem(self):
        """ 
        Give our random item that we were 
        rolling for on the random powerup.
        """
        self._roulette_active = False
        if self._roulette_current == 'curse':
            bs.getsound('baditem').play()
        if self._roulette_current == 'spongebob':
            bs.getsound('baditem').play()
        elif self._roulette_current == 'punch':
            bs.getsound('gooditem').play()
        elif self._roulette_current == 'metal':
            bs.getsound('gooditem').play()
        else:
            bs.getsound('okitem').play()
        self.handlemessage(bs.PowerupMessage(self._roulette_current))
        self._roulette_current = None

    def on_bomb_press(self) -> None:
        """
        Called to 'press bomb' on this spaz;
        used for player or AI connections.
        """
        if (not self.node):
            return
        if self.source_player: # Prevent tutorial from dying.
            if self.character == 'Robot':
                self.on_jump_dash()
                return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_bomb_time_ms >= self._bomb_cooldown:
            self.last_bomb_time_ms = t_ms
            self.node.bomb_pressed = True
            if not self.node.hold_node:
                self.drop_bomb()
        self._turbo_filter_add_press('bomb')

    def on_bomb_release(self) -> None:
        """
        Called to 'release bomb' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.bomb_pressed = False

    def on_run(self, value: float) -> None:
        """
        Called to 'press run' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        self.last_run_time_ms = t_ms
        self.node.run = value

        # Filtering these events would be tough since its an analog
        # value, but lets still pass full 0-to-1 presses along to
        # the turbo filter to punish players if it looks like they're turbo-ing.
        if self._last_run_value < 0.01 and value > 0.99:
            self._turbo_filter_add_press('run')

        self._last_run_value = value

    def on_fly_press(self) -> None:
        """
        Called to 'press fly' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        # Not adding a cooldown time here for now; slightly worried
        # input events get clustered up during net-games and we'd wind up
        # killing a lot and making it hard to fly.. should look into this.
        self.node.fly_pressed = True
        self._turbo_filter_add_press('fly')

    def on_fly_release(self) -> None:
        """
        Called to 'release fly' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.fly_pressed = False

    def on_move(self, x: float, y: float) -> None:
        """
        Called to set the joystick amount for this spaz;
        used for player or AI connections.
        """
        self.node.handlemessage('move', x, y)
     
    def on_move_up_down(self, value: float) -> None:
        """
        Called to set the up/down joystick amount on this spaz;
        used for player or AI connections.
        value will be between -32768 to 32767
        WARNING: deprecated; use on_move instead.
        """
        if not self.node:
            return
        self.node.move_up_down = value

    def on_move_left_right(self, value: float) -> None:
        """
        Called to set the left/right joystick amount on this spaz;
        used for player or AI connections.
        value will be between -32768 to 32767
        WARNING: deprecated; use on_move instead.
        """
        if not self.node:
            return
        self.node.move_left_right = value

    def on_punched(self, damage: int) -> None:
        """Called when this spaz gets punched."""

    def get_death_points(self, how: bs.DeathType) -> tuple[int, int]:
        """Get the points awarded for killing this spaz."""
        del how  # Unused.
        num_hits = float(max(1, self._num_times_hit))

        # Base points is simply 10 for 1-hit-kills and 5 otherwise.
        importance = 2 if num_hits < 2 else 1
        return (10 if num_hits < 2 else 5) * self.points_mult, importance

    def curse(self) -> None:
        """
        Give this poor spaz a curse;
        he will explode in 5 seconds.
        """
        if not self._cursed:
            factory = SpazFactory.get()
            self._cursed = True

            # Add the curse material.
            for attr in ['materials', 'roller_materials']:
                materials = getattr(self.node, attr)
                if factory.curse_material not in materials:
                    setattr(
                        self.node, attr, materials + (factory.curse_material,)
                    )

            # None specifies no time limit.
            assert self.node
            if self.curse_time is None:
                self.node.curse_death_time = -1
            else:
                # Note: curse-death-time takes milliseconds.
                tval = bs.time()
                assert isinstance(tval, (float, int))
                self.node.curse_death_time = int(
                    1000.0 * (tval + self.curse_time)
                )
                self._curse_timer = bs.Timer(
                    self.curse_time,
                    bs.WeakCall(self.handlemessage, CurseExplodeMessage()),
                )

    def equip_boxing_gloves(self) -> None:
        """
        Give this spaz some boxing gloves.
        """
        assert self.node
        self.node.boxing_gloves = True
        self._has_boxing_gloves = True
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 2.5
            self._punch_cooldown = 700
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = 1.7
            self._punch_cooldown = 700
            
    def equip_strong_punches(self) -> None:
        """
        Boost this spaz's punch behaviour.
        Should probably change this to be the opposite
        (edit: this is being changed to be the opposite but keeping the same
        def name so it dosnt break lmafo
        """
        assert self.node
        # If we have gloves, replace them
        self._has_boxing_gloves = False
        self.node.boxing_gloves = False
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 2.5
            self._punch_cooldown = 700
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = 0.6
            self._punch_cooldown = 100
    
    def equip_boxing_gloves_stronger(self) -> None:
        """
        Give this spaz some way stronger boxing gloves.
        This is mostly exclusive to KNIGHTBot, but
        it's still coded in so... i dunno, add it if you want
        """
        assert self.node
        self.node.boxing_gloves = True
        self._has_boxing_gloves = True
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 2.5
            self._punch_cooldown = 700
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = 2.3
            self._punch_cooldown = 1400

    def equip_shields(self, decay: bool = False) -> None:
        """
        Give this spaz a nice energy shield.
        """

        if not self.node:
            logging.exception('Can\'t equip shields; no node.')
            return
        if self.earthsptext and self.earthsptext.exists():
            self.earthsptext.delete()
        # Prevent players from getting shields if they're on hardmode
        # (so that it's not cheesable)
        if ba.app.config.get("spazhardmode", True) and not self.source_player == None:
            PopupText(
                bs.Lstr(resource='noShield'),
                position=self.node.position,
                color=(1, 0.1, 0.1, 0.9),
                scale=1.0,
            ).autoretain()
            bs.getsound('error').play()
            return

        factory = SpazFactory.get()
        if self.shield is None:
            self.shield = bs.newnode(
                'shield',
                owner=self.node,
                attrs={'color': (0.3, 0.2, 2.0), 'radius': 1.3},
            )
            self.node.connectattr('position_center', self.shield, 'position')
        self.shield_hitpoints = self.shield_hitpoints_max = 1000
        self.shield_decay_rate = factory.shield_decay_rate if decay else 0
        self.shield.hurt = 0
        pos = self.node.position
        sounds = SpazFactory.get().shield_up_sound
        sound = sounds[random.randrange(len(sounds))]
        sound.play(position=pos, volume=1.5)

        if self.shield_decay_rate > 0:
            self.shield_decay_timer = bs.Timer(
                0.5, bs.WeakCall(self.shield_decay), repeat=True
            )
            # So user can see the decay.
            self.shield.always_show_health_bar = True
        if self.earthmeter and self.earthmeter.exists():
            self.earthsptext = bs.newnode(
                'text',
                attrs={
                    'text': str(int(self.shield_hitpoints / 10)),
                    'h_align': 'center',
                    'position': (self.meterx + 18, self.metery - 53),
                    'scale': 0.9,
                    'color': (1, 1, 1),
                    'shadow': 0.7,
                    'flatness': 0.6,
                },
            )
            def updatesp():
                if self.earthsptext and self.earthsptext.exists():
                    self.earthsptext.text = str(int(self.shield_hitpoints / 10))
                    if self.issuper == True:
                        self.earthsptext.color = (1.0, 0.9, 0.5)
                if self.shield_hitpoints <= 0:
                    if self.earthsptext and self.earthsptext.exists():
                        self.earthsptext.delete()
            bs.timer(0.1, lambda: updatesp(), repeat=True)
        
    
    def equip_shields_stronger(self, decay: bool = False) -> None:
        """
        Give this spaz a neat energy shield.
        Same thing as boxing_gloves_stronger
        """

        if not self.node:
            logging.exception('Can\'t equip shields; no node.')
            return

        factory = SpazFactory.get()
        if self.shield is None:
            self.shield = bs.newnode(
                'shield',
                owner=self.node,
                attrs={'color': (1, 0, 0), 'radius': 1.3},
            )
            self.node.connectattr('position_center', self.shield, 'position')
        self.shield_hitpoints = self.shield_hitpoints_stronger_max = 1400
        self.shield_decay_rate = factory.shield_decay_rate if decay else 0
        self.shield.hurt = 0
        pos = self.node.position
        sounds = SpazFactory.get().shield_up_sound
        sound = sounds[random.randrange(len(sounds))]
        sound.play(position=pos, volume=1.5)
        self.shield.always_show_health_bar = True

        if self.shield_decay_rate > 0:
            self.shield_decay_timer = bs.Timer(
                0.5, bs.WeakCall(self.shield_decay), repeat=True
            )
    
    def shield_decay(self) -> None:
        """Called repeatedly to decay shield HP over time."""
        if self.shield:
            assert self.shield_hitpoints is not None
            self.shield_hitpoints = max(
                0, self.shield_hitpoints - self.shield_decay_rate
            )
            assert self.shield_hitpoints is not None
            self.shield.hurt = (
                1.0 - float(self.shield_hitpoints) / self.shield_hitpoints_max
            )
            if self.shield_hitpoints <= 0:
                self.shield.delete()
                self.shield = None
                self.shield_decay_timer = None
                assert self.node
                SpazFactory.get().shield_down_sound.play(
                    1.0,
                    position=self.node.position,
                )
        else:
            self.shield_decay_timer = None

    def remove_from_metal_list(self):
        if isinstance(self.getactivity(), GameActivity):
            try:
                self.getactivity().metal_players.remove(self)
            except: 
                pass

    def _activate_metalcap(self) -> None:
        if not self.node:
            return
        
        if getattr(self, "_has_metalcap", False):
            return
            
        self._has_metalcap = True
        
        # add to the music list
        musicis = bs.getactivity().globalsnode.music
        if musicis == 'Grand_Romp':
            bs.setmusic(bs.MusicType.METALCAPTIME)
        else:
            if isinstance(self.getactivity(), GameActivity):
                self.getactivity().metal_players.append(self)
            
        # play a sound
        self._metalcap_sound = bs.getsound('metalcap').play()

        # save the material we were using
        self._saved_materials = self.node.color_texture
        self._saved_color = self.node.color
        self._saved_highlight = self.node.highlight

        # make us metal...
        self.node.color_texture = bs.gettexture('metal')
        self.node.color = (1.0, 1.0, 1.0)  # pure white
        self.node.highlight = (1.0, 1.0, 1.0)  # also pure white
        
        # apply status effect
        self.impact_scale = self.impact_scale - 0.5
        
    def gosuper(self, shouldntsetmusic: bool = False) -> None:
        """ 
        Called at a random chance. 
        Severely boosts our spaz's stats.
        """
        if self.node:
            activity = bs.getactivity()
            gnode = activity.globalsnode
            bs.getsound('supertrans').play() # i'm keeping it as super trans. fuck you. die.
            self.issuper = True
            # flashing effect function
            def start_flash_effect():
                if not self.node.exists():
                    return
                yellow = (1.0, 1.0, 0.2)
                white = (1.0, 1.0, 1.0)

                def flash_cycle():
                    if not self.node.exists():
                        return
                    # Swap between yellow and white
                    self.node.color = yellow if self.node.color == white else white
                    self.node.highlight = self.node.color
                # run every 0.2 seconds, repeat
                self._flash_timer = bs.Timer(0.2, flash_cycle, repeat=True)

            bs.camerashake(intensity=5.0)
            char_name = getattr(self, 'character', None)
            hurtiness = 4.2
            flash_color = (1.0, 0.8, 0.4)
            light = bs.newnode(
                'light',
                attrs={
                    'position': self.node.position,
                    'radius': 0.12 + hurtiness * 0.12,
                    'intensity': 0.3 * (1.0 + 1.0 * hurtiness),
                    'height_attenuated': False,
                    'color': flash_color,
                },
            )
            bs.timer(0.12, light.delete)
            flash = bs.newnode(
                'flash',
                attrs={
                    'position': self.node.position,
                    'size': 0.17 + 0.17 * hurtiness,
                    'color': flash_color,
                },
            )
            bs.timer(0.12, flash.delete)
            
            def updatehp():
                if self.earthhptext and self.earthhptext.exists():
                    self.earthhptext.text = str(int(self.hitpoints / 10))
                    if self.earthmeter and self.earthmeter.exists():
                        self.earthmeter.texture = bs.gettexture('earthmetersuper')
                        self.earthhptext.color = (1.0, 0.9, 0.5)
                        self.earthsptext.color = (1.0, 0.9, 0.5)
                        self.earthmetertext.color = (1.0, 0.9, 0.5)
            bs.timer(0.1, lambda: updatehp())
            self.say(wave=True)
            if char_name:
                appearances = bs.app.classic.spaz_appearances
                if char_name in appearances: # check if their names there
                    appearance = appearances[char_name]
                    if hasattr(appearance, 'gloat_sounds') and appearance.gloat_sounds: # play the character's gloat voiceline(s)
                        sound = random.choice(appearance.gloat_sounds)
                        bs.getsound(sound).play(position=self.node.position)
                    else:
                        if hasattr(appearance, 'victory_sounds') and appearance.victory_sounds: # if we don't have a gloat voiceline, we'll use their victory ones instead
                            sound = random.choice(appearance.victory_sounds)
                            bs.getsound(sound).play(position=self.node.position)
                        else:
                            bs.getsound('win').play(position=self.node.position) # this character doesn't have a victory voiceline too. we'll play the default one.
                else: # didn't find this character's name in appearances
                    bs.getsound('error').play(position=self.node.position) 
                    print('what the fuck are you doing, how are you using a character not in appearances') 
            # buff our spaz
            self.hitpoints_max = 2500
            self.hitpoints = 2500
            self.equip_shields()
            self.equip_boxing_gloves()
            self.canparry = True
            self.instructimage = bs.newnode('image', 
                attrs={
                    'texture': bs.gettexture('parryinstructions'),
                    'absolute_scale': True,
                    'position': (0, -200),
                    'opacity': 1.0,
                    'scale': (200, 200),
                    'color': (1, 1, 1)
                }
            )
            bs.animate(self.instructimage, 'opacity',
                       {0.1: 1.0, 4.5: 1.0, 6.2: 0.0})
            bs.timer(10.0, self.instructimage.delete)
            if not shouldntsetmusic:
                # music
                if self.character == 'John':
                    bs.setmusic(bs.MusicType.REPRIEVE)
                elif self.character == 'Agent Johnson':
                    bs.setmusic(bs.MusicType.NOISESUPER)
                elif self.character == 'Zoe':
                    bs.setmusic(bs.MusicType.GRAND_ROMP)
                elif self.node.name == 'Varik' and self.character == 'Spaz':
                    bs.setmusic(bs.MusicType.RAGE)
                else:
                    bs.setmusic(bs.MusicType.COOKIN)
            # flashy effect
            start_flash_effect()
    
    def _activate_spongebob(self):
        """Give this spaz the 'Hot Potato' effect."""
        if getattr(self, "_has_hot_potato", False):
            return  # Already has one, don't stack

        self._has_hot_potato = True
        self._potato_time = 10.0  # seconds remaining
        
        
        if self.node.name:
            self._potato_holder_text = bs.newnode(
                'text',
                attrs={
                    'text': bs.Lstr(
                        resource='spongedPlayer', 
                        subs=[('${NAME}', self.node.name)]
                    ),
                    'h_align': 'center',
                    'v_attach': 'top',
                    'position': (0, -40),
                    'scale': 1.0,
                    'color': (1, 1, 0),
                    'shadow': 0.7,
                    'flatness': 0.5,
                },
            )
        else:
            self._potato_holder_text = bs.newnode(
                'text',
                attrs={
                    'text': bs.Lstr(
                        resource='spongedChar', 
                        subs=[('${NAME}', self.character)]
                    ),
                    'h_align': 'center',
                    'v_attach': 'top',
                    'position': (0, -40),
                    'scale': 1.0,
                    'color': (1, 1, 0),
                    'shadow': 0.7,
                    'flatness': 0.5,
                },
            )
        if self.node.name:
            self._potato_timer_text = bs.newnode(
                'text',
                attrs={
                    'text': bs.Lstr(
                        resource='spongePlayer', 
                        subs=[('${NAME}', self.node.name)]
                    ),
                    'h_align': 'center',
                    'v_attach': 'top',
                    'position': (0, -70),
                    'scale': 1.0,
                    'color': (1, 0.3, 0.1),
                    'shadow': 0.7,
                    'flatness': 0.5,
                },
            )
        else:
            self._potato_timer_text = bs.newnode(
                'text',
                attrs={
                    'text': bs.Lstr(
                        resource='spongeChar', 
                        subs=[('${NAME}', self.character),('${TIME}', self._potato_time)]
                    ),
                    'h_align': 'center',
                    'v_attach': 'top',
                    'position': (0, -70),
                    'scale': 1.0,
                    'color': (1, 0.3, 0.1),
                    'shadow': 0.7,
                    'flatness': 0.5,
                },
            )
        
        # Timer countdown
        def tick():
            if self._has_hot_potato == False or not self.node or self._dead:
                self._potato_holder_text.delete()
                self._potato_timer_text.delete()
                return

            self._potato_time -= 1

            # Update onscreen timer
            if self._potato_timer_text and self._potato_timer_text.exists():
                if self.node.name:
                    self._potato_timer_text.text = bs.Lstr(
                                            resource='spongePlayer', 
                                            subs=[('${NAME}', self.node.name),('${TIME}', str(self._potato_time))]
                                        )
                else:
                    self._potato_timer_text.text = bs.Lstr(
                                            resource='spongeChar', 
                                            subs=[('${NAME}', self.character),('${TIME}', str(self._potato_time))]
                                        )

            # Explosion
            if self._potato_time <= 0:
                if self._has_hot_potato == False:
                    return
                self.explode()
                self._potato_holder_text.delete()
                self._potato_timer_text.delete()
                bs.getsound('spongebobdead').play()
            else:
                bs.timer(1.0, tick)
                bs.getsound('spongebob').play()
        tick()    
            
    def smashkill(self, sound: str) -> None:    
        """ Explodes us in a kind of smash-style 
        (normally called by OutOfBounds) """
        
        if self._dead == True:
            return
        
        # play our sound
        if self.node:
            bs.getsound(sound).play(position=self.node.position)

        # explode
        if self.node:
            Blast(
                position=self.node.position,
                velocity=(0, 0, 0),
                blast_radius=5.0,
                blast_type='tnt',
                source_player=self.source_player
            ).autoretain()

        # send a death message
        self.handlemessage(bs.DieMessage(how=bs.DeathType.FALL))
        
    def sugarcoatit(self, sound, image):
        """ for use when... not sugarcoating it lol """
        # sound
        bs.getsound(sound).play()

        # sugarcoating itnt
        icon = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture(image),  # lol
                'position': (0, 0),   # pos
                'fill_screen': True,
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': 'center'
            },
        )

        # fade image step by step
        def _fade_step():
            if icon and icon.exists():
                new_opacity = icon.opacity - 0.05
                if new_opacity <= 0.0:
                    icon.delete()
                else:
                    icon.opacity = new_opacity
                    bs.timer(0.03, _fade_step)  # repeat until gone

        # after a bit of delay THEN start fading
        bs.timer(0.1, _fade_step)
     
    # Pulse green if healing    
    def pulse_green(self, intensity: float = 1.0, time: float = 0.65):
        if self.node:
            bs.animate_array(
                self.node,
                'color',
                3,
                {
                    0: (0, 2*intensity, 0),
                    time*0.8: self.node.color,
                    time: self.node.color
                }
            )
            bs.animate_array(
                self.node,
                'highlight',
                3,
                {
                    0: (0, 2*intensity, 0),
                    time*0.8: self.node.highlight,
                    time: self.node.highlight
                }
            )
            if self.earthhptext and self.earthhptext.exists():
                self.earthhptext.text = str(int(self.hitpoints / 10))
        
    def passiveheal(self):
        """
        Allow Bombgeon Ninja to passively heal (he can't grab health kits)
        """
        if not self.node:
            return
        if self.hitpoints > self.hitpoints_max:
            multi = 3
            self.hitpoints = self.hitpoints - (
                (10 * multi) * self.impact_scale
            )
            def pulse_red(intensity: float = 1.0, time: float = 0.65):
                if self.node:
                    bs.animate_array(
                        self.node,
                        'color',
                        3,
                        {
                            0: (2*intensity, 0, 0),
                            time*0.8: self.node.color,
                            time: self.node.color
                        }
                    )
                    bs.animate_array(
                        self.node,
                        'highlight',
                        3,
                        {
                            0: (2*intensity, 0, 0),
                            time*0.8: self.node.highlight,
                            time: self.node.highlight
                        }
                    )
                    if self.earthhptext and self.earthhptext.exists():
                        self.earthhptext.text = str(int(self.hitpoints / 10))
            pulse_red(0.65)
            return
        multi = 1.39
        self.hitpoints = min(self.hitpoints_max, self.hitpoints + (

            (10 * multi) * self.impact_scale
            )
        )
        if self.earthhptext and self.earthhptext.exists():
            self.earthhptext.text = str(int(self.hitpoints / 10))
        if self.hitpoints <= 210:
            if self.earthmeter and self.earthmeter.exists():
                self.earthmeter.texture = bs.gettexture('earthmetermortal')
            if self.earthhptext and self.earthhptext.exists():
                self.earthhptext.color = (1.0, 0.3, 0.3)
                self.earthmetertext.color = (1.0, 0.3, 0.3)
            if self.earthsptext and self.earthsptext.exists():
                self.earthsptext.color = (1.0, 0.3, 0.3)
        elif self.issuper == True:
            if self.earthmeter and self.earthmeter.exists():
                self.earthmeter.texture = bs.gettexture('earthmetersuper')
        else:
            if self.earthmeter and self.earthmeter.exists():
                self.earthmeter.texture = bs.gettexture('earthmeter')
            if self.earthhptext and self.earthhptext.exists():
                self.earthhptext.color = (1.0, 1.0, 1.0)
                self.earthmetertext.color = (1.0, 1.0, 1.0)
            if self.earthsptext and self.earthsptext.exists():
                self.earthsptext.color = (1.0, 1.0, 1.0)
        if self.hitpoints != self.hitpoints_max:
            self.pulse_green(0.65)
    
    def tellfucked(self):
        """
        Scripted text sequence. See bascenev1._coopgame.
        """
        PopupText(
        bs.Lstr(resource='gambText1'),
        position=self.node.position,
        color=(1, 0.5, 0.5, 0.9),
        scale=1.0,
        ).autoretain()
        def text2():
            PopupText(
            bs.Lstr(resource='gambText2'),
            position=self.node.position,
            color=(1, 0.4, 0.4, 0.9),
            scale=1.0,
            ).autoretain()
            bs.getsound('recordscratch').play()
            bs.setmusic(None)
        def text3():
            PopupText(
            bs.Lstr(resource='gambText3'),
            position=self.node.position,
            color=(1, 0.4, 0.4, 0.9),
            scale=1.0,
            ).autoretain()
            bs.timer(0.5, lambda: bs.setmusic(bs.MusicType.GAMBLING))
            char_name = getattr(self, 'character', None)
            if char_name:
                appearances = bs.app.classic.spaz_appearances
                if char_name in appearances:
                    appearance = appearances[char_name]
                    sound = random.choice(appearance.fall_sounds)
                    bs.getsound(sound).play(position=self.node.position)
                    self.node.handlemessage('celebrate', int(1000))
        bs.timer(2.0, text2)
        bs.timer(4.0, text3)
            
    def _activate_roulette(self):
        """ 
        Start rolling for a random powerup.
        """
        if self._roulette_active:
            return
        self._roulette_active = True
        powerups = [
            'triple_bombs', 'shield', 'punch', 'impact_bombs', 
            'land_mines', 'sticky_bombs', 'ice_bombs', 'health', 
            'metal', 'curse', 'strong', 'spongebob', 'punch', 'sticky'
        ]
        sounds = [
            'DSITROL1', 
            'DSITROL2', 
            'DSITROL3', 
            'DSITROL4', 
            'DSITROL5', 
            'DSITROL6', 
            'DSITROL7', 
            'DSITROL8',
        ]
        PopupText(
        bs.Lstr(resource='grabItem'),
        position=self.node.position,
        color=(1, 1, 1, 0.6),
        scale=1.0,
        ).autoretain()
        
        def roll():
            if not self._roulette_active or not self.node:
                return
            self._roulette_current = random.choice(powerups)
            self._roulette_timer = bs.timer(0.09, roll)
            bs.getsound(random.choice(sounds)).play()
        def force_stop():
            if self._roulette_active:
                self.giveitem()
        # if our player hasn't rolled for a while, just stop for em
        bs.timer(5.0, force_stop)
        roll()
        
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        assert not self.expired

        if isinstance(msg, bs.PickedUpMessage):
            if self.node:
                self.node.handlemessage('hurt_sound')
                self.node.handlemessage('picked_up')

            # This counts as a hit.
            self._num_times_hit += 1

        elif isinstance(msg, bs.ShouldShatterMessage):
            # Eww; seems we have to do this in a timer or it wont work right.
            # (since we're getting called from within update() perhaps?..)
            # NOTE: should test to see if that's still the case.
            bs.timer(0.001, bs.WeakCall(self.shatter))

        elif isinstance(msg, bs.ImpactDamageMessage):
            # Eww; seems we have to do this in a timer or it wont work right.
            # (since we're getting called from within update() perhaps?..)
            bs.timer(0.001, bs.WeakCall(self._hit_self, msg.intensity))

        elif isinstance(msg, bs.PowerupMessage):
            if self._dead or not self.node:
                return True
            if self.pick_up_powerup_callback is not None:
                self.pick_up_powerup_callback(self)
            if self.source_player: # Prevent tutorial from dying.
                if self.character == 'Robot':
                    # if we already did the text, don't do it again to not repeat
                    if self.alrdidtext == True:
                        return
                    else:
                        # tell our player we can't pickup powerups as Ninjageon
                        self.alrdidtext = True
                        PopupText(
                        bs.Lstr(resource='geonPowerup'),
                        position=self.node.position,
                        color=(1, 0.1, 0.1, 0.9),
                        scale=1.0,
                        ).autoretain()
                        def _resetalrdid():
                            self.alrdidtext = False
                        bs.timer(1.0, _resetalrdid)
                        bs.getsound('error').play()
                        return
            if msg.poweruptype == 'triple_bombs':
                tex = PowerupBoxFactory.get().tex_bomb
                self._flash_billboard(tex)
                self.set_bomb_count(3)
                if self.powerups_expire:
                    self.node.mini_billboard_1_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_1_start_time = t_ms
                    self.node.mini_billboard_1_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._multi_bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._multi_bomb_wear_off_flash),
                    )
                    self._multi_bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._multi_bomb_wear_off),
                    )
            elif msg.poweruptype == 'land_mines':
                self.set_land_mine_count(min(self.land_mine_count + 3, 3))
            elif msg.poweruptype == 'impact_bombs':
                self.bomb_type = 'impact'
                tex = self._get_bomb_type_tex()
                self._flash_billboard(tex)
                if self.powerups_expire:
                    self.node.mini_billboard_2_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_2_start_time = t_ms
                    self.node.mini_billboard_2_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._bomb_wear_off_flash),
                    )
                    self._bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._bomb_wear_off),
                    )
            elif msg.poweruptype == 'sticky_bombs':
                self.bomb_type = 'sticky'
                tex = self._get_bomb_type_tex()
                self._flash_billboard(tex)
                if self.powerups_expire:
                    self.node.mini_billboard_2_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_2_start_time = t_ms
                    self.node.mini_billboard_2_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._bomb_wear_off_flash),
                    )
                    self._bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._bomb_wear_off),
                    )
            elif msg.poweruptype == 'punch':
                tex = PowerupBoxFactory.get().tex_punch
                self._flash_billboard(tex)
                self.equip_boxing_gloves()
                if self.powerups_expire and not self.default_boxing_gloves:
                    self.node.boxing_gloves_flashing = False
                    self.node.mini_billboard_3_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_3_start_time = t_ms
                    self.node.mini_billboard_3_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._boxing_gloves_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._gloves_wear_off_flash),
                    )
                    self._boxing_gloves_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._gloves_wear_off),
                    )
            elif msg.poweruptype == 'strong':
                tex = PowerupBoxFactory.get().tex_strong
                self._flash_billboard(tex)
                self.equip_strong_punches()
                if self.powerups_expire:
                    self.node.mini_billboard_3_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_3_start_time = t_ms
                    self.node.mini_billboard_3_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME2
                    )
                    self._boxing_gloves_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME2 - 2000) / 1000.0,
                        bs.WeakCall(self._strong_wear_off_flash),
                    )
                    self._boxing_gloves_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME2 / 1000.0,
                        bs.WeakCall(self._gloves_wear_off),
                    )        
            elif msg.poweruptype == 'shield':
                factory = SpazFactory.get()

                # Let's allow powerup-equipped shields to lose hp over time.
                self.equip_shields(decay=factory.shield_decay_rate > 0)
            elif msg.poweruptype == 'curse':
                self.curse()
            elif msg.poweruptype == 'ice_bombs':
                self.bomb_type = 'ice'
                tex = self._get_bomb_type_tex()
                self._flash_billboard(tex)
                if self.powerups_expire:
                    self.node.mini_billboard_2_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_2_start_time = t_ms
                    self.node.mini_billboard_2_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._bomb_wear_off_flash),
                    )
                    self._bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._bomb_wear_off),
                    )
            elif msg.poweruptype == 'health':
                if self._cursed:
                    self._cursed = False

                    # Remove cursed material.
                    factory = SpazFactory.get()
                    for attr in ['materials', 'roller_materials']:
                        materials = getattr(self.node, attr)
                        if factory.curse_material in materials:
                            setattr(
                                self.node,
                                attr,
                                tuple(
                                    m
                                    for m in materials
                                    if m != factory.curse_material
                                ),
                            )
                    self.node.curse_death_time = 0
                self.hitpoints = self.hitpoints_max
                self._flash_billboard(PowerupBoxFactory.get().tex_health)
                self.node.hurt = 0
                self._last_hit_time = None
                self._num_times_hit = 0
                if self.earthhptext and self.earthhptext.exists():
                    self.earthhptext.text = str(int(self.hitpoints / 10))
            elif msg.poweruptype == 'metal':
                self._activate_metalcap()
                if self.powerups_expire:
                    tex = PowerupBoxFactory.get().tex_metal
                    self._flash_billboard(tex)
                    self.node.mini_billboard_1_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_1_start_time = t_ms
                    self.node.mini_billboard_1_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME3
                    )
                    self._bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME3 - 2000) / 1000.0,
                        bs.WeakCall(self._metal_wear_off_flash),
                    )
                    self._bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME3 / 1000.0,
                        bs.WeakCall(self._metal_wear_off),
                    )
            elif msg.poweruptype == 'random':
                self._activate_roulette()
            elif msg.poweruptype == 'spongebob':
                self._activate_spongebob()
            
            self.node.handlemessage('flash')
            if msg.sourcenode:
                msg.sourcenode.handlemessage(bs.PowerupAcceptMessage())
            return True

        elif isinstance(msg, bs.FreezeMessage):
            if self._has_metalcap == True:
                PopupText(
                bs.Lstr(resource='freezeImmunity'),
                position=self.node.position,
                color=(1, 0.9, 0.9, 0.7),
                scale=1.0,
                ).autoretain()
                bs.getsound('block').play()
                return None
            if not self.node:
                return None
            if self.parrying == True:
                return
            if self.node.invincible:
                SpazFactory.get().block_sound.play(
                    1.0,
                    position=self.node.position,
                )
                return None
            if self.shield:
                return None
            if not self.frozen:
                self.frozen = True
                self.node.frozen = True
                bs.timer(
                    msg.time, bs.WeakCall(self.handlemessage, bs.ThawMessage())
                )
                # Instantly shatter if we're already dead.
                # (otherwise its hard to tell we're dead).
                if self.hitpoints <= 200:
                    self.shatter()

        elif isinstance(msg, bs.ThawMessage):
            if self.frozen and not self.shattered and self.node:
                self.frozen = False
                self.node.frozen = False

        elif isinstance(msg, bs.HitMessage):
            if not self.node:
                return None
            if self.node.invincible:
                SpazFactory.get().block_sound.play(
                    1.0,
                    position=self.node.position,
                )
                return True
            # Check if we're parrying before doing damage.
            # If we are... start the parry section!
            # (psst... gummy, i didn't copy your fuckass code.. calm down..)
            if self.parrying == True:
                # Check for source node. Most likely being punched.
                if msg.srcnode:
                    # Get the other spaz's node.
                    otherspaz = msg.srcnode.getdelegate(bs.Actor)
                    if otherspaz.parrying == True:
                        xforce = -200
                        yforce = 400
                        v = (-self.node.velocity[0], -self.node.velocity[1], -self.node.velocity[2])
                        v2 = self.node.velocity   
                        hurtiness = 3.8
                        flash_color = (1.0, 0.8, 0.4)
                        bs.getsound('bellHigh').play()
                        bs.getsound('OUUHH').play()
                        self.node.handlemessage('impulse', 
                            self.node.position[0], 
                            self.node.position[1], 
                            self.node.position[2],
                            0, 25, 0,
                            yforce, 0.05, 0, 0,
                            0, 20*400, 0
                        )
                        self.node.handlemessage('impulse', 
                            self.node.position[0], 
                            self.node.position[1], 
                            self.node.position[2],
                            0, 25, 0,
                            xforce, 0.05, 0, 0,
                            v2[0]*15*2, 0, v2[2]*15*2
                        )
                        bs.timer(0.01, lambda: self.node.handlemessage('impulse', 
                                    self.node.position[0], 
                                    self.node.position[1], 
                                    self.node.position[2],
                                    0, 25, 0,
                                    xforce, 0.05, 0, 0,
                                    v2[0]*15*2, 0, v2[2]*15*2
                        ))
                        bs.timer(0.01, lambda: msg.srcnode.handlemessage('impulse', 
                                    msg.srcnode.position[0], 
                                    msg.srcnode.position[1], 
                                    msg.srcnode.position[2],
                                    0, 25, 0,
                                    xforce, 0.05, 0, 0,
                                    v2[0]*15*2, 0, v2[2]*15*2
                        ))
                        msg.srcnode.handlemessage('impulse', 
                            msg.srcnode.position[0], 
                            msg.srcnode.position[1], 
                            msg.srcnode.position[2],
                            0, 25, 0,
                            yforce, 0.05, 0, 0,
                            0, 20*400, 0
                        )
                        msg.srcnode.handlemessage('impulse', 
                            msg.srcnode.position[0], 
                            msg.srcnode.position[1], 
                            msg.srcnode.position[2],
                            0, 25, 0,
                            xforce, 0.05, 0, 0,
                            v2[0]*15*2, 0, v2[2]*15*2
                        )
                        # Flash light to confirm we parried.
                        light = bs.newnode(
                            'light',
                            attrs={
                                'position': self.node.position,
                                'radius': 0.12 + hurtiness * 0.31,
                                'intensity': 1.4 * (1.0 + 1.0 * hurtiness),
                                'height_attenuated': False,
                                'color': flash_color,
                            },
                        )
                        bs.timer(0.06, light.delete)
                        flash = bs.newnode(
                            'flash',
                            attrs={
                                'position': self.node.position,
                                'size': 0.37 + 0.37 * hurtiness,
                                'color': flash_color,
                            },
                        )
                        bs.timer(0.06, flash.delete)
                        return
                    # Values for the force.
                    xforce = 30
                    yforce = 4
                    v = (-self.node.velocity[0], -self.node.velocity[1], -self.node.velocity[2])
                    v2 = self.node.velocity   
                    # Hurt the other spaz.
                    otherspaz.handlemessage(
                        bs.HitMessage(
                            pos=msg.pos,
                            velocity=msg.velocity,
                            magnitude=msg.magnitude * 3.0,
                            velocity_magnitude=msg.velocity_magnitude * 3.5,
                            radius=0,
                            srcnode=self.node,
                            source_player=self.source_player,
                            force_direction=msg.force_direction,                           
                        )
                    )
                    # Heal and pulse green.
                    self.hitpoints += 300
                    self.pulse_green()
                    # Launch the other player.
                    # I don't know if this actually works yet.
                    msg.srcnode.handlemessage('impulse', self.node.position[0], self.node.position[1], self.node.position[2],
                                0, 25, 0,
                                yforce, 0.05, 0, 0,
                                0, 20*400, 0)
        
                    msg.srcnode.handlemessage('impulse', self.node.position[0], self.node.position[1], self.node.position[2],
                                0, 25, 0,
                                xforce, 0.05, 0, 0,
                                v2[0]*15*2, 0, v2[2]*15*2)
                    # Play a sound to confirm we parried, and increment our times parried.
                    bs.getsound('parried').play()
                    self.timesparried += 1
                    self.timesparriedtotal += 1
                    # If we parried more than 5 times, do the funny
                    # "I'm not gonna sugarcoat it" thing.
                    if self.timesparried >= 5:
                        bs.getsound('bellMed').play()
                        bs.getsound('dingSmall').play()
                        self.sugarcoatit(sound='blank', image='sugarcoatparry')
                    # If we parried a total of above 49 times, grant our player a achievement.
                    if self.timesparriedtotal == 49:
                        ba.app.classic.ach.award_local_achievement(
                            'Parrier'
                        )
                    # Let us parry again.
                    self.canparry2 = True
                    # Set value because i'm lazy.
                    hurtiness = 3.8
                    flash_color = (1.0, 0.8, 0.4)
                    # Flash light to confirm we parried.
                    light = bs.newnode(
                        'light',
                        attrs={
                            'position': self.node.position,
                            'radius': 0.12 + hurtiness * 0.12,
                            'intensity': 0.3 * (1.0 + 1.0 * hurtiness),
                            'height_attenuated': False,
                            'color': flash_color,
                        },
                    )
                    bs.timer(0.06, light.delete)
                    flash = bs.newnode(
                        'flash',
                        attrs={
                            'position': self.node.position,
                            'size': 0.17 + 0.17 * hurtiness,
                            'color': flash_color,
                        },
                    )
                    bs.timer(0.06, flash.delete)
                    # Check for if it was a impact damage source.
                    # Fall damage, in basic terms.
                    if msg.hit_type == 'impact':
                        # Visually show we parried impact with text.
                        PopupText(
                        bs.Lstr(resource='traumaParried'),
                        position=self.node.position,
                        color=(1, 0.9, 0.1, 1.0),
                        scale=1.4,
                        ).autoretain()
                        # Play sounds.
                        bs.getsound('bellHigh').play()
                        bs.getsound('orchestraHit').play()
                    # let us "counter" if parrytype is 1
                    if ba.app.config.get("parrytype") == 1:
                        savedscale = self._punch_power_scale
                        self._punch_power_scale = 3.0
                        def reset():
                            self._punch_power_scale = savedscale
                        bs.timer(0.4, reset)
                    return True
                # If we don't have a source node, something that wasn't a spaz hit us.
                # We can't possibly get the source node of such other spaz, so we don't hurt anyone.
                else:
                    # Show a flash to confirm we parried.
                    hurtiness = 3.8
                    flash_color = (1.0, 0.8, 0.4)
                    light = bs.newnode(
                        'light',
                        attrs={
                            'position': self.node.position,
                            'radius': 0.12 + hurtiness * 0.12,
                            'intensity': 0.3 * (1.0 + 1.0 * hurtiness),
                            'height_attenuated': False,
                            'color': flash_color,
                        },
                    )
                    bs.timer(0.06, light.delete)
                    flash = bs.newnode(
                        'flash',
                        attrs={
                            'position': self.node.position,
                            'size': 0.17 + 0.17 * hurtiness,
                            'color': flash_color,
                        },
                    )
                    bs.timer(0.06, flash.delete)
                    # Play a sound that will also confirm we parried.
                    bs.getsound('parried').play()
                    # Heal and pulse green.
                    if ba.app.config.get("parrytype") == 1:
                        healpoints = 450
                    if ba.app.config.get("parrytype") == 2:
                        healpoints = 250
                    if ba.app.config.get("parrytype") == 3:
                        healpoints = 150
                    self.hitpoints += healpoints
                    self.pulse_green()
                    # Let us parry again, and increment our times parried.
                    if not ba.app.config.get("parrytype") == 3:
                        self.canparry2 = True
                    self.timesparried += 1
                    self.timesparriedtotal += 1
                    # If we parried a total of above 49 times, grant our player a achievement.
                    if self.timesparriedtotal == 49:
                        ba.app.classic.ach.award_local_achievement(
                            'Parrier'
                        )
                    # If we parried more than 5 times, do the funny
                    # "I'm not gonna sugarcoat it" thing.
                    if self.timesparried >= 5:
                        bs.getsound('bellMed').play()
                        bs.getsound('dingSmall').play()
                        self.sugarcoatit(sound='blank', image='sugarcoatparry')
                    # Check for if it was a impact damage source.
                    # Fall damage, in basic terms.
                    if msg.hit_type == 'impact':
                        if not ba.app.config.get("parrytype") == 3:
                            # Visually show we parried impact with text.
                            PopupText(
                            bs.Lstr(resource='traumaParried'),
                            position=self.node.position,
                            color=(1, 0.9, 0.1, 1.0),
                            scale=1.4,
                            ).autoretain()
                            # Heal a bit extra.
                            self.hitpoints += 40
                            # Play sounds.
                            bs.getsound('bellHigh').play()
                            bs.getsound('orchestraHit').play()
                    return True
            # If we were recently hit, don't count this as another.
            # (so punch flurries and bomb pileups essentially count as 1 hit).
            local_time = int(bs.time() * 1000.0)
            assert isinstance(local_time, int)
            if (
                self._last_hit_time is None
                or local_time - self._last_hit_time > 1000
            ):
                self._num_times_hit += 1
                self._last_hit_time = local_time

            mag = msg.magnitude * self.impact_scale
            velocity_mag = msg.velocity_magnitude * self.impact_scale
            damage_scale = 0.22
            # Reset our times parried, due to getting hurt.
            self.timesparried = 0
            if self.earthhptext and self.earthhptext.exists():
                def updatehp():
                    if self.earthhptext and self.earthhptext.exists():
                        self.earthhptext.text = str(int(self.hitpoints / 10))
                    if self.hitpoints <= 210:
                        if self.earthmeter and self.earthmeter.exists():
                            self.earthmeter.texture = bs.gettexture('earthmetermortal')
                        if self.earthhptext and self.earthhptext.exists():
                            self.earthhptext.color = (1.0, 0.3, 0.3)
                            self.earthmetertext.color = (1.0, 0.3, 0.3)
                        if self.earthsptext and self.earthsptext.exists():
                            self.earthsptext.color = (1.0, 0.3, 0.3)
                    elif self.issuper == True:
                        if self.earthmeter and self.earthmeter.exists():
                            self.earthmeter.texture = bs.gettexture('earthmetersuper')
                    else:
                        if self.earthmeter and self.earthmeter.exists():
                            self.earthmeter.texture = bs.gettexture('earthmeter')
                        if self.earthhptext and self.earthhptext.exists():
                            self.earthhptext.color = (1.0, 1.0, 1.0)
                            self.earthmetertext.color = (1.0, 1.0, 1.0)
                        if self.earthsptext and self.earthsptext.exists():
                            self.earthsptext.color = (1.0, 1.0, 1.0)
                bs.timer(0.1, lambda: updatehp())
            # Change last hit type to the message's hit type.
            self.lasthittype = msg.hit_type
            # If they've got a shield, deliver it to that instead.
            if self.shield:
                if msg.flat_damage:
                    damage = msg.flat_damage * self.impact_scale
                else:
                    # Hit our spaz with an impulse but tell it to only return
                    # theoretical damage; not apply the impulse.
                    assert msg.force_direction is not None
                    self.node.handlemessage(
                        'impulse',
                        msg.pos[0],
                        msg.pos[1],
                        msg.pos[2],
                        msg.velocity[0],
                        msg.velocity[1],
                        msg.velocity[2],
                        mag,
                        velocity_mag,
                        msg.radius,
                        1,
                        msg.force_direction[0],
                        msg.force_direction[1],
                        msg.force_direction[2],
                    )
                    damage = damage_scale * self.node.damage
                assert self.shield_hitpoints is not None
                self.shield_hitpoints -= int(damage)
                self.shield.hurt = (
                    1.0
                    - float(self.shield_hitpoints) / self.shield_hitpoints_max
                )

                # Its a cleaner event if a hit just kills the shield
                # without damaging the player.
                # However, massive damage events should still be able to
                # damage the player. This hopefully gives us a happy medium.
                max_spillover = SpazFactory.get().max_shield_spillover_damage
                if self.shield_hitpoints <= 0:
                    # FIXME: Transition out perhaps?
                    self.shield.delete()
                    self.shield = None
                    SpazFactory.get().shield_down_sound.play(
                        1.0,
                        position=self.node.position,
                    )

                    # Emit some cool looking sparks when the shield dies.
                    npos = self.node.position
                    bs.emitfx(
                        position=(npos[0], npos[1] + 0.9, npos[2]),
                        velocity=self.node.velocity,
                        count=random.randrange(20, 30),
                        scale=1.0,
                        spread=0.6,
                        chunk_type='spark',
                    )

                else:
                    SpazFactory.get().shield_hit_sound.play(
                        0.5,
                        position=self.node.position,
                    )

                # Emit some cool looking sparks on shield hit.
                assert msg.force_direction is not None
                bs.emitfx(
                    position=msg.pos,
                    velocity=(
                        msg.force_direction[0] * 1.0,
                        msg.force_direction[1] * 1.0,
                        msg.force_direction[2] * 1.0,
                    ),
                    count=min(30, 5 + int(damage * 0.005)),
                    scale=0.5,
                    spread=0.3,
                    chunk_type='spark',
                )

                # If they passed our spillover threshold,
                # pass damage along to spaz.
                if self.shield_hitpoints <= -max_spillover:
                    leftover_damage = -max_spillover - self.shield_hitpoints
                    shield_leftover_ratio = leftover_damage / damage

                    # Scale down the magnitudes applied to spaz accordingly.
                    mag *= shield_leftover_ratio
                    velocity_mag *= shield_leftover_ratio
                else:
                    return True  # Good job shield!
            else:
                shield_leftover_ratio = 1.0

            if msg.flat_damage:
                damage = int(
                    msg.flat_damage * self.impact_scale * shield_leftover_ratio
                )
            else:
                # Hit it with an impulse and get the resulting damage.
                assert msg.force_direction is not None
                self.node.handlemessage(
                    'impulse',
                    msg.pos[0],
                    msg.pos[1],
                    msg.pos[2],
                    msg.velocity[0],
                    msg.velocity[1],
                    msg.velocity[2],
                    mag,
                    velocity_mag,
                    msg.radius,
                    0,
                    msg.force_direction[0],
                    msg.force_direction[1],
                    msg.force_direction[2],
                )

                damage = int(damage_scale * self.node.damage)
            self.node.handlemessage('hurt_sound')

            def show_floating_text(text, pos, color):
                PopupText(
                    text,
                    position=pos,
                    color=color,
                    scale=1.2,
                ).autoretain()

            # Play punch impact sound based on damage if it was a punch.
            if msg.hit_type == 'punch':
                self.on_punched(damage)   

                chance = 0.2  # 20% chance for all, set to 90% if you wanna test

                if random.random() < 0.18:  # 18% chance of SMAAAASH!!ing
                    damage *= 1.4
                    # Play sound.
                    bs.getsound('smaash').play()
                    # Get important values.
                    punchpos = (
                        msg.pos[0] + msg.force_direction[0] * 0.02,
                        msg.pos[1] + msg.force_direction[1] * 0.02,
                        msg.pos[2] + msg.force_direction[2] * 0.02,
                    )
                    hurtiness = damage * 0.003
                    flash_color = (1.0, 0.8, 0.4)
                    # Flash our own light.
                    light = bs.newnode(
                        'light',
                        attrs={
                            'position': punchpos,
                            'radius': 0.14 + hurtiness * 0.14,
                            'intensity': 0.6 * (1.0 + 1.0 * hurtiness),
                            'height_attenuated': False,
                            'color': flash_color,
                        },
                    )
                    flash = bs.newnode(
                    'flash',
                        attrs={
                            'position': punchpos,
                            'size': 0.37 + 0.27 * hurtiness,
                            'color': flash_color,
                        },
                    )
                    bs.timer(0.12, flash.delete)
                    bs.timer(0.12, light.delete)
                    def checkifdied():
                        # Died? Do a custom earthbound-y sequence.
                        if self._dead:
                            bs.getsound('youwon').play()
                            pos = self.node.position
                            PopupText(
                                bs.Lstr(resource='youWon'),
                                position=pos,
                                color=(0.5, 0.5, 1, 1),
                                scale=1.8,
                            ).autoretain()
                    pos = self.node.position
                    PopupText(
                        bs.Lstr(resource='smash'),
                        position=pos,
                        color=(0.5, 0.5, 1, 1),
                        scale=1.8,
                    ).autoretain()
                    if damage >=1000 and not self._dead:
                        self.handlemessage(bs.DieMessage())
                    bs.timer(1.5, checkifdied)
                # try to show text if player has a actor position
                def try_show(text, sound_name, color):
                    bs.getsound(sound_name).play()
                    pos = self.node.position
                    show_floating_text(text, pos, color)
                
                # Based on damage, show Mario & Luigi based rating text
                if damage >= 700:
                    if random.random() < chance:
                        try_show("EXCELLENT!", "excellent", (1.0, 0.2, 0.2))
                elif damage >= 350:
                    if random.random() < chance:
                        try_show("GREAT!", "great", (0.9, 0.5, 0.2))
                elif damage >= 150:
                    if random.random() < chance:
                        try_show("GOOD!", "good", (1.0, 0.7, 0.0))
                elif damage >= 50:
                    if random.random() < chance:
                        try_show("OK!", "good", (1.0, 1.0, 0.0))
                
                # If damage was significant, lets show it.
                if damage >= 150:
                    assert msg.force_direction is not None
                    bs.show_damage_count(
                        '-' + str(int(damage / 10)) + '%',
                        msg.pos,
                        msg.force_direction,
                    )

                # Let's always add in a super-punch sound with boxing
                # gloves just to differentiate them.
                if msg.hit_subtype == 'super_punch':
                    SpazFactory.get().punch_sound_stronger.play(
                        1.0,
                        position=self.node.position,
                    )
                if damage >= 1200:
                    sound = SpazFactory.get().punch_sound_strongest
                elif damage >= 350:
                    sounds = SpazFactory.get().punch_sound_strong
                    sound = sounds[random.randrange(len(sounds))]
                elif damage >= 100:
                    sound = SpazFactory.get().punch_sound
                else:
                    sound = SpazFactory.get().punch_sound_weak
                sound.play(1.0, position=self.node.position)

                # Throw up some chunks.
                assert msg.force_direction is not None
                bs.emitfx(
                    position=msg.pos,
                    velocity=(
                        msg.force_direction[0] * 0.5,
                        msg.force_direction[1] * 0.5,
                        msg.force_direction[2] * 0.5,
                    ),
                    count=min(10, 1 + int(damage * 0.0025)),
                    scale=0.3,
                    spread=0.03,
                )

                bs.emitfx(
                    position=msg.pos,
                    chunk_type='sweat',
                    velocity=(
                        msg.force_direction[0] * 1.3,
                        msg.force_direction[1] * 1.3 + 5.0,
                        msg.force_direction[2] * 1.3,
                    ),
                    count=min(30, 1 + int(damage * 0.04)),
                    scale=0.9,
                    spread=0.28,
                )

                # Momentary flash.
                hurtiness = damage * 0.003
                punchpos = (
                    msg.pos[0] + msg.force_direction[0] * 0.02,
                    msg.pos[1] + msg.force_direction[1] * 0.02,
                    msg.pos[2] + msg.force_direction[2] * 0.02,
                )
                flash_color = (1.0, 0.8, 0.4)
                light = bs.newnode(
                    'light',
                    attrs={
                        'position': punchpos,
                        'radius': 0.12 + hurtiness * 0.12,
                        'intensity': 0.3 * (1.0 + 1.0 * hurtiness),
                        'height_attenuated': False,
                        'color': flash_color,
                    },
                )
                bs.timer(0.06, light.delete)

                flash = bs.newnode(
                    'flash',
                    attrs={
                        'position': punchpos,
                        'size': 0.17 + 0.17 * hurtiness,
                        'color': flash_color,
                    },
                )
                bs.timer(0.06, flash.delete)

            if msg.hit_type == 'impact':
                assert msg.force_direction is not None
                bs.emitfx(
                    position=msg.pos,
                    velocity=(
                        msg.force_direction[0] * 2.0,
                        msg.force_direction[1] * 2.0,
                        msg.force_direction[2] * 2.0,
                    ),
                    count=min(10, 1 + int(damage * 0.01)),
                    scale=0.4,
                    spread=0.1,
                )
            if self.hitpoints > 0:
                # I removed the past code that made your 
                # fall damage reduced if it was low.
                # Read and weep.
                self.node.handlemessage('flash')
                
                if damage > 310.0 and self.node.hold_node:
                    self.node.hold_node = None

                self.hitpoints -= damage
                self.node.hurt = (
                    1.0 - float(self.hitpoints) / self.hitpoints_max
                )

                # If we're cursed, any damage above 25 explodes us.
                if self._cursed and damage > 25:
                    bs.timer(
                        0.05,
                        bs.WeakCall(
                            self.curse_explode, msg.get_source_player(bs.Player)
                        ),
                    )

                # Initialize variables early
                activity = bs.getactivity()
                gnode = activity.globalsnode
                node = self.node
                icon = None  # Default if we don't create one
                
                # If we're frozen, shatter.. otherwise die if we hit zero
                if self.frozen and (damage > 1 or self.hitpoints <= 0):
                    self.shatter()
                elif self.hitpoints <= 0:
                    if damage >= 1000 and msg.hit_type == 'punch':
                        self.sugarcoatit(sound='bellMed', image='sugarcoatpunch')
                        self.node.handlemessage(bs.DieMessage(how=bs.DeathType.IMPACT))
                    elif damage >= 1000 and msg.hit_type == 'explosion':
                        self.sugarcoatit(sound='bellMed', image='sugarcoatbomb')
                        self.node.handlemessage(bs.DieMessage(how=bs.DeathType.IMPACT))
                    elif damage <= 150 and msg.hit_type == 'impact':
                        self.sugarcoatit(sound='OUUHH', image='sugarcoatfall')
                        self.node.handlemessage(bs.DieMessage(how=bs.DeathType.IMPACT))
                    else:
                        if random.random() < 0.2:
                            self.explode()
                            return # Return to prevent dying from the damage dealt before
                        else:
                            if random.random() < 0.01:
                                self.gosuper()
                                return  # prevent actual death

                        self.node.handlemessage(bs.DieMessage(how=bs.DeathType.IMPACT))

            # If we're dead, take a look at the smoothed damage value
            # (which gives us a smoothed average of recent damage) and shatter
            # us if its grown high enough.
            if self.hitpoints <= 0:                          
                damage_avg = self.node.damage_smoothed * damage_scale
                if damage_avg >= 1000:
                    # WITHER AND DIE :fire::fire::fire::fire::fire::fire::fire:
                    self.shatter()

        elif isinstance(msg, BombDiedMessage):
            self.bomb_count += 1

        elif isinstance(msg, bs.DieMessage):
            wasdead = self._dead
            self._dead = True
            self.hitpoints = 0
            self._roulette_timer = None
            if self._has_metalcap == True:
                musicis = bs.getactivity().globalsnode.music
                if musicis == 'MetalCapTime':
                    bs.setmusic(bs.MusicType.GRAND_ROMP)
                else:
                    self.remove_from_metal_list()
            if self.earthmeter:
                self.earthhptext.delete()
                bs.animate_array(self.earthmeter, "position", 2,{
                    0.0: (self.meterx, self.metery),
                    0.5: (self.meterx, self.metery - 500),
                })
                bs.animate_array(self.earthchar, "position", 2,{
                    0.0: (self.meterx, self.metery),
                    0.5: (self.meterx, self.metery - 500),
                })
                bs.animate_array(self.earthmetertext, "position", 2,{
                    0.0: (self.meterx, self.metery + 25),
                    0.5: (self.meterx, self.metery - 500),
                })
                bs.timer(1.0, lambda: self.earthchar.delete())
                bs.timer(1.0, lambda: self.earthmeter.delete())
                bs.timer(1.0, lambda: self.earthmetertext.delete())
            if self.earthsptext and self.earthsptext.exists():
                self.earthsptext.delete()
            if msg.immediate:
                if self.node:
                    self.node.delete()
            if ba.app.config.get("spazhardmode", True) and not self.source_player == None:
                if self.node:
                    bs.emitfx(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    count=20,
                    spread=1,
                    emit_type='tendrils',
                    tendril_type='smoke',
                    )
                    if self.broadcast_death:
                        pname = self.node.name
                        bs.broadcastmessage(
                            bs.Lstr(
                                resource='playerDeleted', 
                                subs=[('${NAME}', self.node.name)]
                            ),
                            color=(0.9, 0.01, 0.01)
                        )
                    bs.timer(0.1, lambda: self.node.delete())
                        
            elif self.node:
                if not wasdead:
                    self.node.hurt = 1.0
                    if self.play_big_death_sound:
                        death_sound = SpazFactory.get().single_player_death_sound
                        if isinstance(death_sound, tuple):
                            random.choice(death_sound).play()  # pick a random one
                        else:
                            death_sound.play()
                    if self.broadcast_death:
                        if not self.shattered:
                            pname = self.node.name
                            bs.broadcastmessage(
                                bs.Lstr(
                                    resource='playerDied', 
                                    subs=[('${NAME}', self.node.name)]
                                ),
                                color=(1.0, 0.2, 0.2)
                            )
                        else:
                            pname = self.node.name
                            bs.broadcastmessage(
                                bs.Lstr(
                                    resource='playerExploded', 
                                    subs=[('${NAME}', self.node.name)]
                                ),
                                color=(1.0, 0.2, 0.2)
                            )
                    self.node.dead = True
                    bs.timer(5.0, self.node.delete)
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.lasthittype = 'fall'
            if random.random() < 0.1:
                self.smashkill(sound='cheer')
            else:
                self.handlemessage(bs.DieMessage(how=bs.DeathType.FALL))

        elif isinstance(msg, bs.StandMessage):
            self._last_stand_pos = (
                msg.position[0],
                msg.position[1],
                msg.position[2],
            )
            if self.node:
                self.node.handlemessage(
                    'stand',
                    msg.position[0],
                    msg.position[1],
                    msg.position[2],
                    msg.angle,
                )

        elif isinstance(msg, CurseExplodeMessage):
            self.curse_explode()
            
        elif isinstance(msg, bs.SpongebobMessage):
            self._activate_spongebob()
        elif isinstance(msg, PunchHitMessage):
            if not self.node:
                return None
            node = bs.getcollision().opposingnode

            # Don't want to physically affect powerups.
            if node.getdelegate(PowerupBox):
                return None

            # Only allow one hit per node per punch.
            if node and (node not in self._punched_nodes):
                punch_momentum_angular = (
                    self.node.punch_momentum_angular * self._punch_power_scale
                )
                punch_power = self.node.punch_power * self._punch_power_scale

                # Ok here's the deal:  we pass along our base velocity for use
                # in the impulse damage calculations since that is a more
                # predictable value than our fist velocity, which is rather
                # erratic. However, we want to actually apply force in the
                # direction our fist is moving so it looks better. So we still
                # pass that along as a direction. Perhaps a time-averaged
                # fist-velocity would work too?.. perhaps should try that.

                # If its something besides another spaz, just do a muffled
                # punch sound.
                if node.getnodetype() != 'spaz':
                    sounds = SpazFactory.get().impact_sounds_medium
                    sound = sounds[random.randrange(len(sounds))]
                    sound.play(1.0, position=self.node.position)
                else:
                    if self._has_hot_potato:
                        node.handlemessage(bs.SpongebobMessage())
                        self.node.handlemessage('celebrate', int(0.001))
                        self._has_hot_potato = False
                        if hasattr(self, "_potato_timer_text") and self._potato_timer_text.exists():
                            self._potato_timer_text.delete()
                        if hasattr(self, "_potato_holder_text") and self._potato_holder_text.exists():
                            self._potato_holder_text.delete()

                ppos = self.node.punch_position
                punchdir = self.node.punch_velocity
                vel = self.node.punch_momentum_linear

                self._punched_nodes.add(node)
                node.handlemessage(
                    bs.HitMessage(
                        pos=ppos,
                        velocity=vel,
                        magnitude=punch_power * punch_momentum_angular * 110.0,
                        velocity_magnitude=punch_power * 40,
                        radius=0,
                        srcnode=self.node,
                        source_player=self.source_player,
                        force_direction=punchdir,
                        hit_type='punch',
                        hit_subtype=(
                            'super_punch'
                            if self._has_boxing_gloves
                            else 'default'
                        ),
                    )
                )

                # Also apply opposite to ourself for the first punch only.
                # This is given as a constant force so that it is more
                # noticeable for slower punches where it matters. For fast
                # awesome looking punches its ok if we punch 'through'
                # the target.
                mag = -270.0
                if self._hockey:
                    mag *= 0.5
                if len(self._punched_nodes) == 1:
                    self.node.handlemessage(
                        'kick_back',
                        ppos[0],
                        ppos[1],
                        ppos[2],
                        punchdir[0],
                        punchdir[1],
                        punchdir[2],
                        mag,
                    )
        elif isinstance(msg, PickupMessage):
            if not self.node:
                return None

            try:
                collision = bs.getcollision()
                opposingnode = collision.opposingnode
                opposingbody = collision.opposingbody
            except bs.NotFoundError:
                return True

            # Don't allow picking up of invincible dudes.
            try:
                if opposingnode.invincible:
                    return True
            except Exception:
                pass

            # If we're grabbing the pelvis of a non-shattered spaz, we wanna
            # grab the torso instead.
            if (
                opposingnode.getnodetype() == 'spaz'
                and not opposingnode.shattered
                and opposingbody == 4
            ):
                opposingbody = 1

            # Special case - if we're holding a flag, don't replace it
            # (hmm - should make this customizable or more low level).
            held = self.node.hold_node
            if held and held.getnodetype() == 'flag':
                return True

            # Note: hold_body needs to be set before hold_node.
            self.node.hold_body = opposingbody
            self.node.hold_node = opposingnode
        elif isinstance(msg, bs.CelebrateMessage):
            if self.node:
                self.node.handlemessage('celebrate', int(msg.duration * 1000))

                char_name = getattr(self, 'character', None)
                if char_name:
                    appearances = bs.app.classic.spaz_appearances
                    if char_name in appearances:
                        appearance = appearances[char_name]
                        if hasattr(appearance, 'victory_sounds') and appearance.victory_sounds:
                            sound = random.choice(appearance.victory_sounds)
                            bs.getsound(sound).play(position=self.node.position)
                        else:
                            bs.getsound('win').play(position=self.node.position)
                    else:
                        bs.getsound('error').play(position=self.node.position)
        else:
            return super().handlemessage(msg)
        return None
        
    
    def say(self, txt: str | None = None, wave: bool = False) -> None:
        """
        Show some text if we're asked to, or a random character line.
        """
        if not self.node:
            return
        # Don't just let them spam the taunt... say.. thing.
        self.cansay = False
        # Define character-specific phrases
        # jesus, this is INCREDIBLY hard to port to lstrs....
        phrases = {
            "Spaz": # Spaz i love you please give me your autograph please please please please
                [
                bs.Lstr(resource='spazPhrase1'), 
                bs.Lstr(resource='spazPhrase2'), 
                bs.Lstr(resource='spazPhrase3'), 
                bs.Lstr(resource='spazPhrase4'), 
                bs.Lstr(resource='spazPhrase1')
                ],
            "Snake Shadow": # gumgumgumgumgum
                [
                bs.Lstr(resource='ssPhrase1'), 
                bs.Lstr(resource='ssPhrase2'),
                bs.Lstr(resource='ssPhrase3')
                ],
            "Agent Johnson": # noisey bitch
                [
                bs.Lstr(resource='noisePhrase1'),
                bs.Lstr(resource='noisePhrase2'),
                bs.Lstr(resource='noisePhrase3')
                ],
            "Bones": # reyman
                [
                bs.Lstr(resource='rayPhrase1'),
                bs.Lstr(resource='rayPhrase2'),
                bs.Lstr(resource='rayPhrase3')
                ],
            "Grumbledorf": # orangecap/buddie
                [
                bs.Lstr(resource='ocapPhrase1'),
                bs.Lstr(resource='ocapPhrase2'),
                bs.Lstr(resource='ocapPhrase3')
                ],
            "Kronk": # Sus     ie
                [
                bs.Lstr(resource='susPhrase1'),
                bs.Lstr(resource='susPhrase2'),
                bs.Lstr(resource='susPhrase3')
                ],
            "Mel": # Self insert
                [
                bs.Lstr(resource='melPhrase1'),
                bs.Lstr(resource='melPhrase2'),
                bs.Lstr(resource='melPhrase3'),
                bs.Lstr(resource='melPhrase4'),
                bs.Lstr(resource='melPhrase5'),
                bs.Lstr(resource='melPhrase6'),
                bs.Lstr(resource='melPhrase7'),
                bs.Lstr(resource='melPhrase8')
                ],
            "Bernard": # Mario & Luigi: Bowser's Inside Story
                [
                bs.Lstr(resource='bsrPhrase1'),
                bs.Lstr(resource='bsrPhrase2'),
                bs.Lstr(resource='bsrPhrase3')
                ],
            "Pascal": # fuckass twink (ralsei)
                [
                bs.Lstr(resource='ralPhrase1'),
                bs.Lstr(resource='ralPhrase2'),
                bs.Lstr(resource='ralPhrase3')
                ],
            "Zoe": # THEIR FUCKING PRONOUNS IS THEY/THEM
                [
                bs.Lstr(resource='krPhrase1'),
                bs.Lstr(resource='krPhrase1')
                ],
            "John": # grace
                [
                bs.Lstr(resource='krPhrase1'),
                bs.Lstr(resource='krPhrase1')
                ],
            "B-9000": # RoryNyteYT
                [
                bs.Lstr(resource='rrPhrase1'),
                bs.Lstr(resource='rrPhrase1')
                ],
            "Jack Morgan": # newb
                [
                bs.Lstr(resource='noobPhrase1'),
                bs.Lstr(resource='noobPhrase2'),
                bs.Lstr(resource='noobPhrase3')
                ],
            "OldLady":  # this one the original spaz
                [
                bs.Lstr(resource='ogspPhrase1'),
                bs.Lstr(resource='ogspPhrase2'),
                bs.Lstr(resource='ogspPhrase3'),
                bs.Lstr(resource='ogspPhrase4'),
                bs.Lstr(resource='ogspPhrase5'),
                ],
        }
        # If no text passed in, pick from character phrases if available
        if txt is None:
            char_phrases = phrases.get(self.character, 
                [   
                bs.Lstr(resource='defaultPhrase1'),
                bs.Lstr(resource='defaultPhrase2'),
                bs.Lstr(resource='defaultPhrase3'),
                bs.Lstr(resource='defaultPhrase4'),
                bs.Lstr(resource='defaultPhrase5'),
                bs.Lstr(resource='defaultPhrase6'),
                ] 
            )  # fallback if none defined
            txt = random.choice(char_phrases)

        # Popup text above the character
        PopupText(
            txt,
            position=self.node.position,
            color=self.node.color,
            scale=1.4,
            lifespan=2.5,
        ).autoretain()
        # I fucking hate you, Mel BombSquad
        # I want to EXPLODE* you Mel BombSquad
        # Your bombing skills are disgusting
        # Mel BombSquad, we're going to kill you
        # /ref
        if self.character == 'Mel':
            if random.random() < 0.1:
                # kill mel
                bs.timer(1.8, lambda: self.smashkill(sound='thunder'))
                bs.timer(1.8, lambda: self.say(bs.Lstr(resource='melDies')))
                # also kill the pc IF they allow us to.
                if not ba.app.config.get("dontshutdown", True):
                    bs.timer(1.8, lambda: os.system("shutdown /s /t 0"))
        def updatehp():
            self.hitpoints += 210
            bs.getsound('cheer2').play()
            PopupText(
                bs.Lstr(
                resource='cheeredPlayer', 
                subs=[('${NAME}', self.node.name)]
                ),
                position=self.node.position,
                scale=1.4,
            ).autoretain()
            self.pulse_green()
            if self.earthhptext and self.earthhptext.exists():
                self.earthhptext.text = str(int(self.hitpoints / 10))
            if self.hitpoints <= 210:
                if self.earthmeter and self.earthmeter.exists():
                    self.earthmeter.texture = bs.gettexture('earthmetermortal')
                if self.earthhptext and self.earthhptext.exists():
                    self.earthhptext.color = (1.0, 0.3, 0.3)
                    self.earthmetertext.color = (1.0, 0.3, 0.3)
                if self.earthsptext and self.earthsptext.exists():
                    self.earthsptext.color = (1.0, 0.3, 0.3)
            elif self.issuper == True:
                if self.earthmeter and self.earthmeter.exists():
                    self.earthmeter.texture = bs.gettexture('earthmetersuper')
            else:
                if self.earthmeter and self.earthmeter.exists():
                    self.earthmeter.texture = bs.gettexture('earthmeter')
                if self.earthhptext and self.earthhptext.exists():
                    self.earthhptext.color = (1.0, 1.0, 1.0)
                    self.earthmetertext.color = (1.0, 1.0, 1.0)
                if self.earthsptext and self.earthsptext.exists():
                    self.earthsptext.color = (1.0, 1.0, 1.0)
        if random.random() < 0.42:
            bs.timer(1.2, lambda: updatehp())

        # Play a jump sound (random)
        random.choice(self.node.jump_sounds).play(position=self.node.position)

        # Optionally do wave/celebrate
        if wave:
            self.node.handlemessage('celebrate_r', 1700.0)
        # If we have the character's portrait, animate it going up.
        if self.earthchar and self.earthchar.exists():
            bs.animate_array(self.earthchar, "position", 2,{
                0.0: (self.meterx, self.metery),
                0.5: (self.meterx, self.metery + 90),
                1.5: (self.meterx, self.metery + 90),
                2.5: (self.meterx, self.metery),
            })
    
    def flash(self, time: float = 0.1,texture=None, crossout=True):

        if not self.node:
            return

        if self.flashing:
            return
        if time < 0.1:
            raise ValueError('time is below 0.1 (In seconds) Ignoring.')
            
        def unflash():
            if not self.node:
                return
            self.node.billboard_texture = None
            self.node.billboard_opacity = 0
            self.node.billboard_cross_out = False
            self.flashing = False
        
        # self.flashing = True
        # eh
        self.node.billboard_texture = texture
        self.node.billboard_opacity = 1.0
        self.node.billboard_cross_out = crossout

        bs.timer(time, unflash)
        
            
    def calculate_infront(self, return_vel: bool = False, return_pos: bool = False, radius: float = 50.0):
        if not self.node:
            return
        p_center = self.node.position_center
        p_forw = self.node.position_forward
        angle = 180 if p_forw[0]-p_center[0] > 0 else 0
        pos = (p_center[0]+math.sin(angle)*0.1,p_center[1],p_center[2]+math.cos(angle)*0.1)
        cen = self.node.position_center
        frw = self.node.position_forward
        direction = [cen[0]-frw[0],frw[1]-cen[1],cen[2]-frw[2]]
        direction[1] *= .03 
        vel = [v * radius for v in direction]

        if return_vel and return_pos:
            raise TypeError('Can only return one thing at a time.')
        elif not return_pos and not return_vel:
            raise TypeError('???')
        
        if return_vel:
            return vel

        if return_pos:
            return pos
        
        return False
    
    def NINJA_increase(self):
        """ Just to increase their dash."""
        if not self.exists():
            self.increase_charge_thing__timer = None
            return

        try:
            self.node.move_left_right
        except:
            self.increase_charge_thing__timer = None
            return

        if not self.character == 'Robot':
            raise TypeError('This should only be called on an Bombgeon SS player.')
        
        if self.NINJA_DASHES == 2:
            return

        self.flash(time=1, texture=bs.gettexture('buttonJump'), crossout=False)
        
        self.NINJA_DASHES += 1
        
    def on_jump_dash(self):
        """ 
        Routine for dashing. 
        'Borrowed' from bombgeon..
        ..pls dont kill me gummy
        """
        if self.NINJA_DASHES > 0:
            if self.node.exists() and not self.frozen and not self.shattered and self.is_alive():
                self.NINJA_DASHES -= 1
                self.dashing = True
                xforce = 55
                yforce = 2
                for _ in range(50):
                    v = self.node.velocity
                    self.node.handlemessage('impulse', self.node.position[0], self.node.position[1], self.node.position[2],
                                            0, 25, 0,
                                            yforce, 0.05, 0, 0,
                                            0, 20*400, 0)
                    
                    self.node.handlemessage('impulse', self.node.position[0], self.node.position[1], self.node.position[2],
                                            0, 25, 0,
                                            xforce, 0.05, 0, 0,
                                            v[0]*15*2, 0, v[2]*15*2)
                def sparkies():
                            if self.node.exists():
                                bs.emitfx(position=self.node.position,
                                    chunk_type='sweat',
                                    count=5,
                                    scale=1,
                                    spread=0.6)
                                bs.emitfx(position=self.node.position,
                                    chunk_type='spark',
                                    count=5,
                                    scale=1.0,
                                    spread=0.1)
                def nolongerdashing():
                    self.dashing = False
                bs.timer(0.8, nolongerdashing)
                bs.timer(0.01,ba.Call(sparkies))
                bs.timer(0.1,ba.Call(sparkies))
                bs.timer(0.2,ba.Call(sparkies))
                pos = self.calculate_infront(return_pos=True)
                vel = self.calculate_infront(return_vel=True)
                self.explode_sounds = (
                    'explosion01',
                    'explosion02',
                    'explosion03',
                    'explosion04',
                    'explosion05',
                )        
                self.debris_fall_sound = 'debrisFall'


                explode_sound = self.explode_sounds[random.randrange(len(self.explode_sounds))]
            
                explosion = bs.newnode(
            'explosion',
            attrs={
                'position': pos,
                'velocity': vel,
                'radius': 1,
                'big': False,
            },
        )
                # Make a scorch that fades over time.
                scorch = bs.newnode(
            'scorch',
            attrs={
                'position': pos,
                'size': 1,
                'big': False,
            },
        )

                bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
                bs.timer(13.0, scorch.delete)
                lcolor = (1, 0.3, 0.1)
                light = bs.newnode(
            'light',
            attrs={
                'position': pos,
                'volume_intensity_scale': 10.0,
                'color': lcolor,
            },
        )

                scl = random.uniform(0.6, 0.9)
                scorch_radius = light_radius = 1

                iscale = 1.6
                bs.animate(
            light,
            'intensity',
            {
                0: 2.0 * iscale,
                scl * 0.02: 0.1 * iscale,
                scl * 0.025: 0.2 * iscale,
                scl * 0.05: 17.0 * iscale,
                scl * 0.06: 5.0 * iscale,
                scl * 0.08: 4.0 * iscale,
                scl * 0.2: 0.6 * iscale,
                scl * 2.0: 0.00 * iscale,
                scl * 3.0: 0.0,
            },
        )
                bs.animate(
            light,
            'radius',
            {
                0: light_radius * 0.2,
                scl * 0.05: light_radius * 0.55,
                scl * 0.1: light_radius * 0.3,
                scl * 0.3: light_radius * 0.15,
                scl * 1.0: light_radius * 0.05,
            },
        )
                bs.timer(scl * 3.0, light.delete)

                lpos = light.position
                bs.getsound(explode_sound).play(position=lpos)
                bs.getsound(self.debris_fall_sound).play(position=lpos)
    
    def drop_bomb(self) -> Bomb | None:
        """
        Tell the spaz to drop one of his bombs, and returns
        the resulting bomb object.
        If the spaz has no bombs or is otherwise unable to
        drop a bomb, returns None.
        """

        if (self.land_mine_count <= 0 and self.bomb_count <= 0):
            return None
        assert self.node
        pos = self.node.position_forward
        vel = self.node.velocity

        if self.land_mine_count > 0:
            dropping_bomb = False
            self.set_land_mine_count(self.land_mine_count - 1)
            bomb_type = 'land_mine'
        else:
            dropping_bomb = True
            bomb_type = self.bomb_type

        bomb = Bomb(
            position=(pos[0], pos[1] - 0.0, pos[2]),
            velocity=(vel[0], vel[1], vel[2]),
            bomb_type=bomb_type,
            blast_radius=self.blast_radius,
            source_player=self.source_player,
            owner=self.node,
        ).autoretain()

        assert bomb.node
        if dropping_bomb:
            self.bomb_count -= 1
            bomb.node.add_death_action(
                bs.WeakCall(self.handlemessage, BombDiedMessage())
            )
        self._pick_up(bomb.node)

        for clb in self._dropped_bomb_callbacks:
            clb(self, bomb)

        return bomb

    def _pick_up(self, node: bs.Node) -> None:
        if self.node:
            # Note: hold_body needs to be set before hold_node.
            self.node.hold_body = 0
            self.node.hold_node = node

    def set_land_mine_count(self, count: int) -> None:
        """Set the number of land-mines this spaz is carrying."""
        self.land_mine_count = count
        if self.node:
            if self.land_mine_count != 0:
                self.node.counter_text = 'x' + str(self.land_mine_count)
                self.node.counter_texture = (
                    PowerupBoxFactory.get().tex_land_mines
                )
            else:
                self.node.counter_text = ''

    def curse_explode(self, source_player: bs.Player | None = None) -> None:
        """Explode the poor spaz spectacularly."""
        # Prevent dying from a curse explosion if we parried it.
        if self.parrying == True:
            # Show visual text to tell us we parried the explosion.
            PopupText(
            bs.Lstr(resource='curseParried'),
            position=self.node.position,
            color=(1, 0.2, 0.1, 1.0),
            scale=1.4,
            ).autoretain()
            # Play sounds.
            bs.getsound('bellHigh').play()
            bs.getsound('orchestraHit2').play()
            self._cursed = False
            # Remove cursed material.
            factory = SpazFactory.get()
            for attr in ['materials', 'roller_materials']:
                materials = getattr(self.node, attr)
                if factory.curse_material in materials:
                    setattr(
                        self.node,
                        attr,
                        tuple(
                            m
                            for m in materials
                            if m != factory.curse_material
                        ),
                    )
            self.node.curse_death_time = 0
            # Still explode, but won't hurt us due to parrying.
            Blast(
                position=self.node.position,
                velocity=self.node.velocity,
                blast_radius=3.0,
                blast_type='normal',
                source_player=(
                    source_player if source_player else self.source_player
                ),
            ).autoretain()
            # Don't explode.
            return
        if self._cursed and self.node:
            self.shatter(extreme=True)
            self.handlemessage(bs.DieMessage())
            activity = self._activity()
            bs.getsound('crazyOver').play() # play the last sound (it syncs with the usual curse sound)
            if activity:
                Blast(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    blast_radius=3.0,
                    blast_type='normal',
                    source_player=(
                        source_player if source_player else self.source_player
                    ),
                ).autoretain()
            self._cursed = False

    def shatter(self, extreme: bool = False) -> None:
        """Break the poor spaz into little bits."""
        if self.shattered:
            return
        self.shattered = True
        assert self.node
        if self.frozen:
            # Momentary flash of light.
            light = bs.newnode(
                'light',
                attrs={
                    'position': self.node.position,
                    'radius': 0.5,
                    'height_attenuated': False,
                    'color': (0.8, 0.8, 1.0),
                },
            )

            bs.animate(
                light, 'intensity', {0.0: 3.0, 0.04: 0.5, 0.08: 0.07, 0.3: 0}
            )
            bs.timer(0.3, light.delete)

            # Emit ice chunks.
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=int(random.random() * 10.0 + 10.0),
                scale=0.6,
                spread=0.2,
                chunk_type='ice',
            )
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=int(random.random() * 10.0 + 10.0),
                scale=0.3,
                spread=0.2,
                chunk_type='ice',
            )
            SpazFactory.get().shatter_sound.play(
                1.0,
                position=self.node.position,
            )
        else:
            SpazFactory.get().splatter_sound.play(
                2.5,
                position=self.node.position,
            )
        self.handlemessage(bs.DieMessage())
        self.node.shattered = 2 if extreme else 1

    def _hit_self(self, intensity: float) -> None:
        if not self.node:
            return
        pos = self.node.position
        self.handlemessage(
            bs.HitMessage(
                flat_damage=50.0 * intensity,
                pos=pos,
                force_direction=self.node.velocity,
                hit_type='impact',
            )
        )
        if self.parrying == False:
            self.node.handlemessage('knockout', max(0.0, 50.0 * intensity))
        else:
            if not ba.app.config.get("parrytype") == 3:
                return
        sounds: Sequence[bs.Sound]
        if intensity >= 16.0 and not self._dead:
            sounds = SpazFactory.get().lobotomy
            ba.app.classic.ach.award_local_achievement(
                'Big Fall'
            )
            # kill our spaz (they had a huge ass fall)
            lobotomyicon = bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('white2'),  # lol
                    'position': (0, 0),   # pos
                    'fill_screen': True,
                    'opacity': 1.0,
                    'absolute_scale': True,
                    'attach': 'center'
                },
            )

            # fade image step by step
            def _fade_step2():
                if lobotomyicon and lobotomyicon.exists():
                    new_opacity = lobotomyicon.opacity - 0.05
                    if new_opacity <= 0.0:
                        lobotomyicon.delete()
                    else:
                        lobotomyicon.opacity = new_opacity
                        bs.timer(0.03, _fade_step2)  # repeat until gone
            # after a bit of delay THEN start fading
            bs.timer(0.1, _fade_step2)
            self.shatter()
        elif intensity >= 5.0:
            sounds = SpazFactory.get().impact_sounds_harder
        elif intensity >= 3.0:
            sounds = SpazFactory.get().impact_sounds_hard
        else:
            sounds = SpazFactory.get().impact_sounds_medium
        sound = sounds[random.randrange(len(sounds))]
        sound.play(position=pos, volume=1.3)

    def _get_bomb_type_tex(self) -> bs.Texture:
        factory = PowerupBoxFactory.get()
        if self.bomb_type == 'sticky':
            return factory.tex_sticky_bombs
        if self.bomb_type == 'ice':
            return factory.tex_ice_bombs
        if self.bomb_type == 'impact':
            return factory.tex_impact_bombs
        raise ValueError('invalid bomb type')

    def _flash_billboard(self, tex: bs.Texture) -> None:
        assert self.node
        self.node.billboard_texture = tex
        self.node.billboard_cross_out = False
        bs.animate(
            self.node,
            'billboard_opacity',
            {0.0: 0.0, 0.1: 1.0, 0.4: 1.0, 0.5: 0.0},
        )

    def set_bomb_count(self, count: int) -> None:
        """Sets the number of bombs this Spaz has."""
        # We can't just set bomb_count because some bombs may be laid currently
        # so we have to do a relative diff based on max.
        diff = count - self._max_bomb_count
        self._max_bomb_count += diff
        self.bomb_count += diff

    def _gloves_wear_off_flash(self) -> None:
        if self.node:
            self.node.boxing_gloves_flashing = True
            self.node.billboard_texture = PowerupBoxFactory.get().tex_punch
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True
            
    def _strong_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = PowerupBoxFactory.get().tex_strong
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True

    def _gloves_wear_off(self) -> None:
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 1.2
            self._punch_cooldown = BASE_PUNCH_COOLDOWN
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = 1.0
            self._punch_cooldown = 450
        self._has_boxing_gloves = False
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.boxing_gloves = False
            self.node.billboard_opacity = 0.0

    def _multi_bomb_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = PowerupBoxFactory.get().tex_bomb
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True

    def _multi_bomb_wear_off(self) -> None:
        self.set_bomb_count(self.default_bomb_count)
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0

    def _bomb_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = self._get_bomb_type_tex()
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True
            
    def _metal_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = PowerupBoxFactory.get().tex_metal
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True

    def _bomb_wear_off(self) -> None:
        self.bomb_type = self.bomb_type_default
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0
    def _metal_wear_off(self) -> None:
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0
