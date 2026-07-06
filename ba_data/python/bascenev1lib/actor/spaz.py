# Released under the MIT License. See LICENSE for details.
"""
Spaz actor class and related functionality.
"""
# pylint: disable=too-many-lines

from __future__ import annotations

import random
import logging
from typing import TYPE_CHECKING, override
from bascenev1lib.actor.text import Text

import bascenev1 as bs
import baclassic as bsc
import math
import os
import weakref
from bascenev1lib.actor.popuptext import PopupText
from bascenev1lib.actor import spazappearance
import bascenev1lib.actor.spazappearance as spazappearance
from bascenev1._gameactivity import GameActivity
from fromgoverhaul.watercooler import WaterCoolerSpawner
from bascenev1lib.actor.bomb import Bomb, Blast, BombFactory
from bascenev1lib.actor.powerupbox import PowerupBoxFactory, PowerupBox
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.actor.particles import BloodParticle, ConfettiParticle, SparkParticle
from bascenev1lib.actor.hookfireball import UKHook, Fireball, Tear
from bascenev1lib.actor.image_looped import LoopingImageAnimation
from bascenev1lib.gameutils import SharedObjects, TouchedMessage
from babase._logging import squdalog
from fromgoverhaul.mell_sfx import SoundFactory

import fromgoverhaul.mell_resources as mell
import babase as ba

from bascenev1lib.actor.entities.kookoo import Kookoo
from bascenev1lib.actor.entities.dozer import Dozer
from bascenev1lib.actor.entities.ire import Ire
from bascenev1lib.actor.entities.sorrow import Sorrow
from bascenev1lib.actor.entities.mime import Mime
from bascenev1lib.actor.entities.litany import Litany

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable

POWERUP_WEAR_OFF_TIME = 27000
POWERUP_WEAR_OFF_TIME2 = 19000
POWERUP_WEAR_OFF_TIME3 = 10000
POWERUP_WEAR_OFF_TIME_STAR = 9000
POWERUP_WEAR_OFF_TIME_K = 65000

# Obsolete - just used for demo guy now.
BASE_PUNCH_POWER_SCALE = 1.2
BASE_PUNCH_COOLDOWN = 400

SUPPORTED_STYLES = ['normal', 'metallic', 'robot', 'fancy']

RAINBOW_SPEED = 0.4  # determine speed
RAINBOW_COLORS = [
    (1.0, 0.0, 0.0),  # red
    (1.0, 0.5, 0.0),  # orange
    (1.0, 1.0, 0.0),  # yellow
    (0.0, 1.0, 0.0),  # green
    (0.0, 1.0, 1.0),  # cyan
    (0.0, 0.0, 1.0),  # blue
    (1.0, 0.0, 1.0),  # pink???
]

def build_rainbow(speed: float):
    colors = RAINBOW_COLORS + [RAINBOW_COLORS[0]]
    step = speed / (len(colors) - 1)
    return {
        i * step: color
        for i, color in enumerate(colors)
    }

RAINBOW = build_rainbow(RAINBOW_SPEED)

# Catchphrases that characters say
PHRASES = {
    "Spaz": ("spazPhrase", 4),
    "GummyBoiYT": ("ssPhrase", 3),
    "The Noise": ("noisePhrase", 3),
    "Rayman": ("rayPhrase", 3),
    "Orangecap": ("ocapPhrase", 3),
    "Susie": ("susPhrase", 3),
    "Mell": ("melPhrase", 8),
    "Bowser": ("bsrPhrase", 3),
    "Ralsei": ("ralPhrase", 3),
    "Kris": ("krPhrase", 1),
    "Roaring Knight": ("rrPhrase", 1),
    "Noob": ("noobPhrase", 3),
    "OG Spaz": ("ogspPhrase", 5),
    "Homer": ("homerPhrase", 8),
    "Buddie": ("budPhrase", 61),
    "SM64 Mario": ("marioPhrase", 5),
    "Ire": ("irePhrase", 4),
    "Dozer": ("dozerPhrase", 3),
    "SqudaTaobaoMascot": ("aliPhrase", 1),
    "Sonic": ("sonicPhrase", 5),
}
# A default fallback for characters that don't have it
DEFAULT_PHRASES = ("defaultPhrase", 16)
# Phrases for remarks/rivalries (like Spaz against Mell, or Sonic and Tails)
# Format: [KILLERCHAR, VICTIMCHAR]: (phraseLstrResource, amount)
REMARK_PHRASES = {
    ("Buddie", "Orangecap"): ("budKillsOrangecap", 1),
    ("Buddie", "Sonic"): ("budKillsOrangecap", 1),
    ("Buddie", "Tails"): ("budKillsOrangecap", 1),
    ("Buddie", "John Grace"): ("budKillsJohnGrace", 1),
    ("Buddie", "Mell"): ("budKillsMell", 1),
    ("Buddie", "Buddie"): ("budKillsBuddie", 1),
    ("Buddie", "Roaring Knight"): ("budKillsRory", 1),
    ("Buddie", "Jonathan"): ("budKillsJonathan", 1),
    ("Buddie", "SM64 Mario"): ("budKillsMario", 1),
    ("Buddie", "Kirby"): ("budKillsKirby", 1),
    ("Buddie", "Baller"): ("budKillsBaller", 1),
    ("Spaz", "Spaz"): ("spazKillsSpaz", 1),
    ("Mell", "Ire"): ("mellKillsIre", 1),
    ("Mell", "Dozer"): ("mellKillsDozer", 1),
    ("Mell", "Mell"): ("mellKillsMell", 1),
    ("Mell", "Buddie"): ("mellKillsBuddie", 1),
    ("Ralsei", "Kris"): ("ralseiKillsKris", 1),
    ("Kris", "Susie"): ("krisKillsSusie", 1),
    ("Roaring Knight", "Susie"): ("roryKillsSusie", 1),
    ("John Grace", "Kirby"): ("johnKillsKirby", 1),
    ("GummyBoiYT", "Taobao Mascot"): ("gummyKillsAli", 1),
    ("Ire", "Dozer"): ("ireKillsDozer", 3),
    ("Dozer", "Ire"): ("dozerKillsIre", 3),
    ("Sonic", "Tails"): ("sonicKillsTails", 3),
    ("Spaz", "Mell"): ("spazKillsMell", 3),
    ("Spaz", "GummyBoiYT"): ("spazKillsGummy", 3),
    ("Spaz", "OG Spaz"): ("spazKillsOG", 3),
    ("OG Spaz", "Spaz"): ("ogKillsSpaz", 3),
    ("Bowser", "SM64 Mario"): ("bowserKillsMario", 3),
    ("SM64 Mario", "Bowser"): ("marioKillsBowser", 3),
}

CHAIN_SOUNDS = [
    (6, 'mbm/chain5'),
    (5, 'mbm/chain4'),
    (4, 'mbm/chain3'),
    (3, 'mbm/chain2'),
    (2, 'mbm/chain1'),
    (1, 'mbm/chain0'),
]

RELEASE_SOUNDS = [
    (1, 'mbm/release'),
]

ENTITY_CONFIG = {
    'kookoo': {
        'attr_flag': 'kookood',
        'attr_obj': 'kookoo',
        'appearsLstr': bs.Lstr(resource='kookooAppears'),
        'class': Kookoo,
        'texture': lambda: PowerupBoxFactory.get().tex_kookoo,
    },
    'dozer': {
        'attr_flag': 'dozered',
        'attr_obj': 'dozer',
        'appearsLstr': bs.Lstr(resource='dozerAppears'),
        'class': Dozer,
        'texture': lambda: PowerupBoxFactory.get().tex_dozer,
    },
    'ire': {
        'attr_flag': 'ired',
        'attr_obj': 'ire',
        'appearsLstr': bs.Lstr(resource='ireAppears'),
        'class': Ire,
        'texture': lambda: PowerupBoxFactory.get().tex_ire,
    },
    'sorrow': {
        'attr_flag': 'sorrowful',
        'attr_obj': 'sorrow',
        'appearsLstr': bs.Lstr(resource='sorrowAppears'),
        'class': Sorrow,
        'texture': lambda: PowerupBoxFactory.get().tex_sorrow,
    },
    'mime': {
        'attr_flag': 'mimed',
        'attr_obj': 'mime',
        'appearsLstr': bs.Lstr(resource='mimeAppears'),
        'class': Mime,
        'texture': lambda: PowerupBoxFactory.get().tex_mime,
    },
    'litany': {
        'attr_flag': 'litanyd',
        'attr_obj': 'litany',
        'appearsLstr': bs.Lstr(resource='litanyAppears'),
        'class': Litany,
        'texture': lambda: PowerupBoxFactory.get().tex_litany,
    },
}

def playsound(name, pos):
    bs.getsound(name).play(position=pos)

class MinecraftDust(bs.Actor):
    # bs.getplayers()[0].actor.spawn_in_buncha_dust()

    def __init__(self, position: Sequence[float]):
        super().__init__()
        # hitbox
        shared = SharedObjects.get()
        self.node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'mesh': bs.getmesh('ball'),
                'color_texture': bs.gettexture('white'),
                'body_scale': 0.5,
                'position': position,
                'velocity': (random.uniform(-1.3, 1.3), 2, random.uniform(-1.3, 1.3)),
                'gravity_scale': 0.01,
                'shadow_size': 0.2,
                'materials': [shared.non_collide_mat],
            },
        )
        bs.animate(
            self.node, 
            'mesh_scale',
            {
                0: 0,
                0.05: 0.4,
                0.15: 1.2,
                0.2: 0.5,
                1.7: 0,
            }
        )
        bs.timer(1.7, bs.Call(self.handlemessage, bs.DieMessage()))
    
    @override
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        else: 
            return super().handlemessage(msg)

class MinecraftItem(bs.Actor):
    # bs.getplayers()[0].actor.spawn_in_buncha_items()

    def __init__(self, position: Sequence[float]):
        super().__init__()
        # hitbox
        shared = SharedObjects.get()
        self.node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'body_scale': 0.5,
                'position': position,
                'velocity': (random.uniform(-4.5, 4.5), 4.5, random.uniform(-4.5, 4.5)),
                'gravity_scale': 1.1,
                'materials': [shared.only_collide_with_floor_mat],
                'shadow_size': 0,
            },
        )
        # actual thing
        item = [
            ['tnt', 'rocky', 0.35],
            ['tnt', 'dirt', 0.35],
            ['tnt', 'netherrack', 0.35],
            ['ender_pearl', 'enderPearl', 0.5],
            ['wind_charge', 'windCharge', 0.5],
            ['totem', 'totemOfUndying', 0.5],
            ['arrow', 'arrow', 0.4],
            ['bread', 'bread', 0.5],
            ['pickaxe', 'ironPickaxe', 0.6],
            ['axe', 'ironAxe', 0.6],
            ['sword', 'ironSword', 0.6],
            ['bow', 'bow', 0.6],
            ['mace', 'mace', 0.6],
            ['bomb', 'bombStickyColor', 0.6],
        ]
        selected_item = random.choice(item)
        self.item_node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'mesh': bs.getmesh(selected_item[0]),
                'color_texture': bs.gettexture(selected_item[1]),
                'mesh_scale': selected_item[2],
                'gravity_scale': 0,
                'body': 'landMine',
                'position': position,
                'shadow_size': 0.3,
                'materials': [shared.non_collide_mat],
            },
        )
        self.tick_timer = bs.Timer(0.01, bs.Call(self._tick), repeat=True)
        self.do_rotate()
      
        bs.timer(8, bs.Call(self.handlemessage, bs.DieMessage()))
    
    def _rotate(self):
        if not self.node.exists() or not self.item_node.exists():
            return

        dir_x = 0.2
        dir_z = 0
        pos = self.item_node.position
        force = 3.5
        self.item_node.handlemessage(
            'impulse',
            pos[0],
            pos[1],
            pos[2]+0.2,
            0, 0, 0,
            force,
            force,
            0,
            0,
            dir_x,
            0,
            dir_z,
        )
        bs.timer(0.5, bs.Call(self.do_rotate))
    
    def do_rotate(self):
        if not self.node.exists() or not self.item_node.exists():
            return
        self.item_node.velocity = (0, 0, 0) 
        bs.timer(0.1, bs.Call(self._rotate))

    def _tick(self):
        if not self.node.exists() or not self.item_node.exists():
            return
        
        
        self.item_node.position = (
            self.node.position[0],
            self.node.position[1] + 0.1 + (math.sin((bs.time()) * 3.0) * 0.1),
            self.node.position[2],
        )
        
         
            #self.node.angular_velocity = self.item_node.angular_velocity
    
    @override
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            if not self.node.exists() or not self.item_node.exists():
                self.node.delete()
                self.item_node.delete()
                return
            if msg.immediate:
                self.node.delete()
                self.item_node.delete()
            else:
                bs.animate(
                    self.item_node, 'mesh_scale', {0: 
                                                   self.item_node.mesh_scale, 
                                                   0.2: 0.0}
                )
                bs.timer(0.2, bs.Call(self.node.delete))
                bs.timer(0.2, bs.Call(self.item_node.delete))
                

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        else: 
            return super().handlemessage(msg)
        


class PickupMessage:
    """We wanna pick something up."""


class PunchHitMessage:
    """Message saying an object was hit."""


class CurseExplodeMessage:
    """We are cursed and should blow up now."""


class BombDiedMessage:
    """A bomb has died and thus can be recycled."""

class FootingMessage:
    """
    Message class representing the footing state of an actor.
    Attributes:
        footing: The current footing state of the actor.
    """
    def __init__(self, footing):
        self.footing = footing
        
class EmeraldMessage:
    """
    Message for emerald-related events or state changes.
    Attributes:
        current: The current emerald value or state.
        srcnode: The emerald node that gave this Message.
    """
    def __init__(self, current, srcnode):
        self.current = current
        self.srcnode = srcnode

class HeadExplodedMessage:
    """
    Message for when a Spaz gets 
    his head crushed by a bomb.
    """
    def __init__(self, spaz):
        self.spaz = spaz 

class ShatteredMessage:
    """
    Message for when a Spaz gets 
    torn into multiple pieces. Basically; shattered.
    """
    def __init__(self, spaz):
        self.spaz = spaz 

class ParriedMessage:
    """
    Message for when a Spaz
    parries a damage source. (Bombs, punches, etc)
    """
    def __init__(self, spaz):
        self.spaz = spaz

class ClashMessage:
    """
    Message for when two spazzes 
    punch eachother in a short period, effectively, a 'clash'.
    """
    def __init__(self, position):
        self.position = position

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
    
    kaizo_mode: bool = False
    """Kaizo mode. Global bool that changes some
    stats and mechanics, to be more 'movement-based'."""

    points_mult = 1
    curse_time: float | None = 5.0
    default_bomb_count = 1
    default_bomb_type = 'normal'
    default_boxing_gloves = False
    default_boxing_gloves_stronger = False
    default_shields = False
    default_shields_stronger = False
    default_hitpoints = 1000 
    
    
    def __init__(
        self,
        *,
        color: Sequence[float] = (1.0, 1.0, 1.0),
        highlight: Sequence[float] = (0.5, 0.5, 0.5),
        name: str = '',
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
        if not getattr(self, 'character', None):
            self.character = character

        factory = SpazFactory.get()
        SoundFactory.get()

        # We need to behave slightly different in the tutorial.
        self._demo_mode = demo_mode

        # isaac stuff
        self.is_cry = False
        self.can_cry = True
        # Specific settings for alerting if a spaz died
        self.play_big_death_sound = False
        self.broadcast_death = False     
        self.impact_scale = 1.0
        self._roulette_active = False
        self._roulette_timer = None
        self._roulette_current = None
        self.spongebob_timer = None
        self._wiggle_count = 0
        self.wiggling = False
        self._next_wiggle_left = True
        self.charge_flash = None
        self.sparkies = None
        self.super_flash = None
        self.actor_type = 'spaz'
        self.deton = False
        self.deton_bombs = []
        self.times_detond = 0
        self.tdtnd_reset = None
        self.shotgunned = False
        self.fireballed = False
        self.whiplashed = False
        self.shotgun_shots = 0
        self.fireballs = 0
        self.hook = None
        self.scream_sfx = None
        self.scream_sfx_node = None
        self.screaming = False
        self.scream_celebrate_timer = None
        self.mortal_dmg_timer = None
        self.mortal_phase = False
        self.last_punched_time = 0
        # entity checks
        self.kookood = False
        self.dozered = False
        self.ired = False
        self.sorrowful = False
        self.mimed = False
        self.litanyd = False
        
        self.last_x = 0
        self.last_y = 0
        self.last_last_x = 0
        self.last_last_y = 0
        
        self.ire = None
        self.kookoo = None
        self.sorrow = None
        self.dozer = None
        self.mime = None
        self.litany = None

        self.source_player = source_player
        self._dead = False
        # stats for punch
        self.knightscale = 2.3
        self.knightcwd = 1400
        self.boxingscale = 1.7
        self.boxingcwd = 700
        self.punchscale = 1.1
        self.punchcwd = 450
        self.weakscale = 0.6
        self.weakcwd = 90
        # slightly stronger on kaizo mode
        # (we want faster, stronger bomb jumps)
        if self.kaizo_mode:
            self.boxingcwd = 320
            self.punchcwd = 200
            self.punchscale = 1.35
        self.last_victim_character = ''
        self.last_victim_name = ''
        self.weak_punches = False
        aprilfools = mell.get_festivity() == 'april_fools'
        # we replace various things if it's AF
        if aprilfools:
            character = 'Spaz'
            self.boxingscale = 0.8
            self.boxingcwd = 200
            self.default_bomb_count = 9999
            self.punchscale = 0.5
            self.punchcwd = 1
            self.weakcwd = 0.0001
            self.weakscale = 50
            self.knightscale = 0
            self.knightcwd = 9999
        # stats for punch
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 1.2
        else:
            self._punch_power_scale = self.punchscale
        self.fly = self.getactivity().globalsnode.happy_thoughts_mode
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
        self.prev_music = None
        self.force_stop_timer = None
        self.explotimer = None
        self.wiggledancetimer = None
        self.parryshield = None
        self.hardmode = False
        self.pickup_pressed = False
        self.flight_points = self.default_flight_points = 90
        self.flight_timer = None
        self.already_refilling = False
        self.refill_flight_timer = None
        self.flying = False
        self._super_light = None
        self._yeehaw_mathnode = None

        if can_accept_powerups:
            pam = PowerupBoxFactory.get().powerup_accept_material
            materials.append(pam)
            roller_materials.append(pam)
            extras_material.append(pam)
        # get config if we have a source player
        if self.source_player:
            self.parrybtn = self.source_player.settings['parry button']
            self.bombskin = self.source_player.settings['bomb skin']
            self.skin = self.source_player.settings['skin']
            scream = self.source_player.settings['scream sound']
            scream_dict = {
                'annie': 'anniescream',
                'anton': 'antonscream',
                'wario': 'wario_scream',
            }
            if scream in scream_dict.keys():
                self.scream_sfx = bs.getsound(scream_dict[scream])
            else:
                self.scream_sfx = bs.getsound('trublank')
            # KILL YOURSELF
            if ba.app.config.get('squda_randomgrace'):
                self.grace_check_timer = bs.Timer(1.0, self._randomly_attach_entity, repeat=True)
        else:
            self.parrybtn = 'grab'
            self.bombskin = None
            self.skin = None
            self.scream_sfx = bs.getsound('trublank')
        # we can override if a skin setting exists
        if self.skin:
            character = self.skin
        fav_char = bs.app.config.get('squda_favchar', None)
        if fav_char:
            character = fav_char
        media = factory.get_media(character)
        self.media = media
        self.char_style = media['general_style']
        if self.char_style not in SUPPORTED_STYLES:
            squdalog.error(f'{self.char_style} IS NOT A SUPPORTED GENERAL STYLE. FALLING BACK TO NORMAL')
            self.char_style = 'normal'
        self.expression_list = media['expression_changes']
        punchmats = (factory.punch_material, shared.attack_material)
        pickupmats = (factory.pickup_material, shared.pickup_material)
        self.node: bs.Node = bs.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': color,
                'name': name,
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
        self.hitpoints = self.default_hitpoints
        self.oldhp = self.hitpoints
        self.defaulthand = media['hand_mesh']
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
        self.standing = False
        self.instructimage = None
        self.cansay = False
        self.lasthittype = None
        self.letimer = None
        self.letimer2 = None
        self.timesparried = 0
        self.timesparriedtotal = 0
        self.yeehaws = 0
        self.yeehaw_text = None
        self.blast_radius = 2.0
        self.powerups_expire = powerups_expire
        if self._demo_mode:  # Preserve old behavior.
            self._punch_cooldown = BASE_PUNCH_COOLDOWN
        else:
            self._punch_cooldown = self.punchcwd
        self._jump_cooldown = 0
        self._pickup_cooldown = 0
        self._bomb_cooldown = 0
        self.bomb_fuse_time = 2.0
        self._has_boxing_gloves = False
        self._has_metalcap = False
        self._has_star = False
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
        self.eb_meter = None
        self.super_sparkies = None
        self.alreadydidanimation = False
        self.frozen = False
        self.shattered = False
        self.hexploded = False
        self._has_metalcap = False
        self._last_hit_time: int | None = None
        self._num_times_hit = 0
        self._bomb_held = False
        self.shield_hitpoints = 0
        if self.default_shields:
            self.equip_shields()
        if self.default_shields_stronger:
            self.equip_shields_stronger()
        self._has_hot_potato = False
        self._dropped_bomb_callbacks: list[Callable[[Spaz, bs.Actor], Any]] = []
        self._score_text: bs.Node | None = None
        self._score_text_hide_timer: bs.Timer | None = None
        self._last_stand_pos: Sequence[float] | None = None

        # Deprecated stuff.. should make these into lists.
        self.punch_callback: Callable[[Spaz], Any] | None = None
        self.pick_up_powerup_callback: Callable[[Spaz], Any] | None = None
        self.emeralds = []
        self.voicelines = []
        self.emeralds_indicator = None
        self.update_emerald_indicator()
        self.flashing = False
        self._flash_timer = None
        self.impulse_scale = 1.5
        self._saved_color = self.node.color
        self._saved_highlight = self.node.highlight
        self._saved_materials = self.node.color_texture
        self._saved_style = None
        self._saved_gen_style = None

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
        self.sparkies = None
        self.super_flash = None
        # stop voicelines
        self.stop_voicelines()

        # Clean up timers to prevent leaks
        timers_to_clear = [
            self.shield_decay_timer,
            self._boxing_gloves_wear_off_timer,
            self._boxing_gloves_wear_off_flash_timer,
            self._bomb_wear_off_timer,
            self._bomb_wear_off_flash_timer,
            self._multi_bomb_wear_off_timer,
            self._multi_bomb_wear_off_flash_timer,
            self._curse_timer,
            self._score_text_hide_timer,
            self._roulette_timer,
            self.force_stop_timer,
            self.letimer,
            self.letimer2,
            self.explotimer,
            self.wiggledancetimer,
            self._flash_timer,
            self.spongebob_timer,
            self.hook,
            self.scream_sfx,
            self.eb_meter,
        ]
        for timer in timers_to_clear:
            if timer is not None:
                timer = None

        # Clean up nodes
        nodes_to_delete = [
            self.shield,
            self._score_text,
            self.emeralds_indicator,
            self.eb_meter,
            self.charge_flash,
            self.yeehaw_text,
            self.parryshield,
            self.instructimage,
            self.scream_sfx_node,
        ]
        for node in nodes_to_delete:
            if node is not None and node.exists():
                node.delete()
        entities_tofuckingnuke = [
            self.ire,
            self.dozer,
            self.kookoo,
            self.sorrow,
            self.mime,
            self.litany,
        ]
        for entity in entities_tofuckingnuke:
            if entity is not None:
                entity.stop()
                entity = None

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
        
    def getspeed(self, 
            should_abs: bool = True, 
            decimals: int = 2, 
            ignore_y: bool = True
        ):
        """
        Calculate the speed of the actor based on velocity components.

        Args:
            should_abs (bool, optional): If True, returns the absolute value of the 
                maximum velocity component. Defaults to True.
            decimals (int, optional): Number of decimal places to round the result to. 
                Defaults to 2.
            ignore_y (bool, optional): If True, ignores the Y-axis velocity component 
                and only considers X and Z. If False, considers all three components 
                (X, Y, Z). Defaults to True.

        Returns:
            float: The speed rounded to the specified number of decimal places.
        """
        vx, vy, vz = self.node.velocity
        components = (vx, vz) if ignore_y else (vx, vy, vz)
        # absolute-ize the result if we should
        if should_abs:
            value = abs(max(components, key=abs))
        else:
            value = max(components)
        # yep, theres your speed!
        return round(value, decimals)

    def _turbo_filter_add_press(self, source: str) -> None:
        """
        Can pass all button presses through here; if we see an obscene number
        of them in a short time let's shame/punish this guy for using turbo.
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
                if self._turbo_filter_counts[source] == 15 and not self._dead:
                    # WHY just knock em out? at this rate, 
                    # we'll explode them and have them die
                    assert self.node
                    Blast(
                        position=self.node.position,
                        velocity=self.node.velocity,
                        blast_radius=0.6,
                        blast_type='tnt',
                        source_player= None
                    )
                    SoundFactory.get().turbo_death.play(
                        position=self.node.position
                    )
                    ba.app.classic.ach.award_local_achievement('Turbo')
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
        bs.timer(1.3, setfalse) # should maybe use setattr
    
    def show_fp_text(self):
        if not self.node: 
            return
        if not getattr(self, 'fp_text', None):
            mathnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 2.3, 0), 'operation': 'add'},
            )
            self.node.connectattr('torso_position', mathnode, 'input2')
            self.fp_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': '',
                    'in_world': True,
                    'scale': 0.01,
                    'h_align': 'center',
                    'opacity': 0
                },
            )
            mathnode.connectattr('output', self.fp_text, 'position')
        bs.animate(self.fp_text, 'opacity',
            {
                0: self.fp_text.opacity,
                0.5: 1,
            }
        )
    
    def hide_fp_text(self):
        if not self.node:
            return
        bs.animate(self.fp_text, 'opacity',
            {
                0: self.fp_text.opacity,
                0.5: 0,
            }
        )
    
    def flash_fp_text(self):
        bs.animate_array(self.fp_text, 'color', 3,
            {
                0: self.fp_text.color,
                0.1: (0, 0.3, 1),
                0.5: self.fp_text.color,
            }
        )
    
    def update_fp_text(self):
        if not self.node:
            return
        self.fp_text.text = f'{self.flight_points}/{self.default_flight_points}'
    
    def schedule_refill_flight(self):
        if self.already_refilling:
            return
        def refill():
            if not self.standing or not self.node or self.flying:
                return
            if self.flight_points >= self.default_flight_points:
                self.refill_flight_timer = None
                SoundFactory.get().flight_refilled.play(
                    position=self.node.position,
                    volume=1.3,
                )
                self.flash_fp_text()
                self.hide_fp_text()
                return
            self.flight_points += 1
            self.update_fp_text()
        def start():
            if not self.node:
                return
            self.already_refilling = False
            self.refill_flight_timer = bs.Timer(0.11, refill, repeat=True)
        self.already_refilling = True
        bs.timer(1.8, start)
    
    def super_flight(self):
        if not self.node or self.node.knockout:
            return
        if self.standing:
            return
        if self.flight_points <= 0:
            self.schedule_refill_flight()
            self.update_fp_text()
            return
        if self.refill_flight_timer:
            self.refill_flight_timer = None
        self.show_fp_text()
        self.update_fp_text()
        self.impulse(y=31)
        # apply some impulse on directions for
        # more control
        dir_x = self.node.move_left_right * 1.3
        dir_z = -self.node.move_up_down * 1.3
        pos = self.node.position
        force = 20
        self.node.handlemessage(
            'impulse',
            pos[0],
            pos[1],
            pos[2],
            0, 0, 0,
            force,
            force,
            0,
            0,
            dir_x,
            0,
            dir_z,
        )
        self.flight_points -= 1

    def on_jump_press(self) -> None:
        """
        Called to 'press jump' on this spaz;
        used by player or AI connections.
        """
        if self.character == "Isaac":
            self.is_cry = True
            self._shoot_tear("down")
        else:
            if not self.node:
                return
            if self.cansay == True:
                self.say(wave=True, shouldcelb=True)
            t_ms = int(bs.time() * 1000.0)
            assert isinstance(t_ms, int)
            if self.canparry == True and self.parrybtn == 'jump':
                self.attempt_parry()
                return
            if t_ms - self.last_jump_time_ms >= self._jump_cooldown:
                self.node.jump_pressed = True
                self.last_jump_time_ms = t_ms
            if self.issuper and not self.standing:
                self.flight_timer = bs.Timer(0.02, self.super_flight, repeat=True)
                self.flying = True
            self._turbo_filter_add_press('jump')

    def on_jump_release(self) -> None:
        """
        Called to 'release jump' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        self.is_cry = False
        if self.flying:
            self.flight_timer = None
            self.flying = False
            self.schedule_refill_flight()
        self.node.jump_pressed = False
    
    def scary_text(
        self, 
        text: str,
        xpos: int = 0, 
        color: tuple[float, float, float] = (1, 0.9, 0.9),
        scale: int = 0.013,
        spacing_x: int = 0.18,
        spacing_y: int = 0.35,
        endtime: int = 5,
        shakiness: int = 0.035,
    ):
        """
        Show some "scary text". Ah!
        :param text: the text. you know
        :param xpos: the offset where the text will start
        :param color: color of the text
        :param scale: scale of the **LETTERS**. this means you'll have to adjust spacing!
        :param spacing_x: x spacing of the letters
        :param spacing_y: y spacing of the letters
        :param endtime: time the text animates out
        :param shakiness: shakiness of the text
        """
        start_x_base = xpos
        start_x = start_x_base # start x
        line_offset = 0  # how many lines down we are
        nodelist = []
        for letter in text:
            # handle line break
            if letter == '\n':
                start_x = start_x_base
                line_offset += 1
                continue
            # position is based on start x which is also spacing
            # y is above our head, and it also uses line offsets
            # z never gets changed
            position = (
                self.node.position[0] + start_x,
                self.node.position[1] + 1.3 - (line_offset * spacing_y),
                self.node.position[2],
            )
            # create a node for em
            node = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': letter,
                    'in_world': True,
                    'color': color,
                    'scale': scale,
                    'h_align': 'center',
                    'position': position,
                },
            )
            # animate in then out
            bs.animate(node, 'opacity', {
                0.0: 0,
                1.0: 1,
                endtime - 1: 1,
                endtime: 0,
            })
            # append to node list so we can delete later
            nodelist.append(node)
            # shake the node
            mell.shake_node(
                node,
                duration=endtime + 1,
                interval=0.01,
                intensity=shakiness,
                array_num=3
            )
            def delete_all():
                for node in nodelist:
                    if node and node.exists():
                        node.delete()
            bs.timer(endtime, delete_all)
            # add spacing
            start_x += spacing_x
    
    def attempt_parry(self):
        """
        Called upon when attempting a parry;
        Will set a value for some seconds that determines
        whether the player is in the parry timeframe.
        """
        # If we're not allowed to parry here, most likely on cooldown.
        # Return and don't do anything.
        if self.canparry2 == False:
            return
        if not self.node or not self.is_alive():
            return
            
        # Set important values.
        self.canparry2 = False
        self.parrying = True
        parrytime = 0.2
        parrycooldown = 0.6
        
        def stopparry():
            self.parrying = False
        def letparryagain():
            self.canparry2 = True
            
        # Close our parry timeframe after our chosen second(s).
        # Then, allow parrying again after the cooldown
        bs.timer(parrytime, stopparry)
        bs.timer(parrycooldown, letparryagain)
        milscs = parrytime * 1000
        self.node.handlemessage('celebrate', int(milscs))
        # Make a shield node.
        self.parryshield = bs.newnode(
            'shield',
            owner=self.node,
            attrs={'color': (0, 0.5, 1), 'radius': 1.0},
        )
        self.node.connectattr('position_center', self.parryshield, 'position')
        bs.animate(
            self.parryshield, 
            'radius', 
            {
                parrytime - 0.15: 1.0, 
                parrytime: 0.0
            }
        )
        bs.timer(parrytime, self.parryshield.delete)
        SoundFactory.get().attempt_parry.play(position=self.node.position)
    
    def impulse(self, x: float | int = 0, y: float | int = 0):
        if not self.node:
            return
        v = self.node.velocity
        x = x
        y = y
        if x == 0 and y == 0:
            raise ValueError("You must specify at least X or Y for impulse.")
        # only use x and y impulse if specified
        if x != 0:
            self.node.handlemessage('impulse', 
                self.node.position[0], 
                self.node.position[1], 
                self.node.position[2],
                0, 25, 0, x, 0.05, 0, 0,
                v[0]*15*2, 0, v[2]*15*2
            )
        if y != 0:
            self.node.handlemessage('impulse', 
                self.node.position[0], 
                self.node.position[1], 
                self.node.position[2],
                0, 25, 0,
                y, 0.05, 0, 0,
                0, 20*400, 0
            )
    
    def set_expression(self):
        pass
    
    def _start_screaming(self):
        if not self.node or not self.is_alive():
            return
        if not self.pickup_pressed or self.screaming:
            return
        # Do a camera shake to not make it so empty.
        bs.camerashake(1)
        # Set the attribute and make a sound node
        self.screaming = True
        self.scream_sfx_node = bs.newnode(
            'sound',
            owner=self.node,
            attrs={
                'sound': self.scream_sfx,
                'volume': 1.5,
                'position': self.node.position,
            }
        )
        # Continuosly celebrate
        def celb():
            self.node.handlemessage('celebrate', int(50))
        self.scream_celebrate_timer = bs.Timer(0.01, celb, repeat=True)
        # Connect the sound to us
        self.node.connectattr('position', self.scream_sfx_node, 'position')
    
    def _stop_screaming(self):
        if not self.node:
            return
        if not self.screaming:
            return
        self.screaming = False
        # Clean up and stop everything we made
        if self.scream_sfx_node:
            self.scream_sfx_node.volume = 0
            self.scream_sfx_node.delete()
        if self.scream_celebrate_timer:
            self.scream_celebrate_timer = None
        

    def on_pickup_press(self) -> None:
        """
        Called to 'press pick-up' on this spaz;
        used by player or AI connections.
        """
        if self.character != "Isaac":
            bs.timer(0.3, self._start_screaming)
        self.pickup_pressed = True
        if self._roulette_active:
            # If rouletting, give our item to the player.
            self._give_item()
            return
        if self.whiplashed:
            if not self.node or not self.is_alive():
                return
            if not self.hook or not self.hook.node:
                self._shoot_hook()
                return
            else:
                SoundFactory.get().hook_despawn.play(position=self.hook.node.position)
                self.hook.handlemessage(bs.DieMessage())
        if self.deton:
            if not self.node:
                return
            bs.getsound('menu_sel').play(position=self.node.position)
            def reset():
                self.times_detond = 0
            self.times_detond += 1
            vol = 1.2
            if self.times_detond == 13:
                PopupText(
                    bs.Lstr(resource='easeDeton1'),
                    position=self.node.position,
                    color=(1, 0.5, 0, 1.0),
                    scale=1.4,
                ).autoretain()
                SoundFactory.get().horn_warningS.play(
                    volume=vol, 
                    position=self.node.position
                )
                SoundFactory.get().horn_warningV.play(
                    volume=vol, 
                    position=self.node.position
                )
            if self.times_detond == 26:
                PopupText(
                    bs.Lstr(resource='easeDeton2'),
                    position=self.node.position,
                    color=(1, 0.1, 0.1, 1.0),
                    scale=1.4,
                ).autoretain()
                SoundFactory.get().horn_dangerS.play(
                    volume=vol, 
                    position=self.node.position
                )
                SoundFactory.get().horn_dangerV.play(
                    volume=vol, 
                    position=self.node.position
                )
            if self.times_detond == 39:
                PopupText(
                    bs.Lstr(resource='easeDeton3'),
                    position=self.node.position,
                    color=(0.7, 0, 0, 1.0),
                    scale=1.4,
                ).autoretain()
                self.firework_explode(force_scream=True)
            self.tdtnd_reset = bs.Timer(0.8, reset)
            bs.timer(0.1, self.explode_deton_bombs)
        # wow, lotsa conditions
        if (
            len(self.emeralds) >= 7 and
            self.hitpoints >= 70 and
            self.standing == False and
            self.issuper == False
        ):
            self.gosuper()
            self.emeralds = []
            self.update_emerald_indicator()
            return
        
        if self.canparry == True and self.parrybtn == 'grab':
            self.attempt_parry()
            # isaac can shoot tears AND parry
            if self.character != "Isaac":
                return
        
        if not self.node:
            return
        if self.character == "Isaac":
            self.is_cry = True
            self._shoot_tear("up")
        else:
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
        self.pickup_pressed = False
        self._stop_screaming()
        self.is_cry = False

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
        if self.character == "Isaac":
            self.is_cry = True
            self._shoot_tear("left")
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        # if flying, then dash forward
        if self.flying and self.flight_points > 0:
            dir_x = self.node.move_left_right * 3
            dir_z = self.node.move_up_down * 3
            pos = self.node.position
            force = 80
            SoundFactory.get().super_dash.play(
                position=self.node.position
            )
            for _ in range(5):
                self.node.handlemessage(
                    'impulse',
                    pos[0],
                    pos[1],
                    pos[2],
                    0, 0, 0,
                    force,
                    force,
                    0,
                    0,
                    dir_x,
                    0.6,
                    -dir_z,
                )
            self.flight_points -= 15
            vel = self.node.velocity
            # Emit fake explosion for visual effect...
            explosion = bs.newnode(
                'explosion',
                attrs={
                    'position': pos,
                    'velocity': vel,
                    'radius': 1.0,
                    'big': False,
                    'color': self.node.color,
                },
            )
            bs.timer(1.0, explosion.delete)
            bs.emitfx(
                position=pos,
                emit_type='distortion',
                spread=2.0,
            )
            light = bs.newnode(
                'light',
                attrs={
                    'position': self.node.position,
                    'radius': 0.5,
                    'height_attenuated': False,
                    'color': self.node.color,
                },
            )
            bs.animate(
                light, 'intensity', {0.0: 0, 0.04: 3, 0.08: 1, 0.2: 0}
            )
            bs.timer(0.2, light.delete)
            vel = (-dir_x * 4, 0, dir_z * 4)
            bs.emitfx(
                position=pos,
                velocity=vel,
                count=int(4.0 + random.random() * 4),
                chunk_type='spark',
            )
            return
        if self.canparry == True and self.parrybtn == 'punch':
            self.attempt_parry()
            return
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
        
    def firework_explode(self, 
        on_die_call: Callable = None,
        force_scream: bool = False
    ) -> None:
        """
        Trigger a firework explosion effect on the actor.
        This method launches the actor upward and detonates it when it reaches
        a certain height, creating a firework explosion. If the actor gets stuck
        (doesn't reach the required height), it will explode after a timeout.
        Args:
            on_die_call (Callable, optional): A callback function to execute when
                the explosion occurs. Defaults to None.
            snd1 (str, optional): The sound effect to play at the start of the
                firework sequence. Defaults to 'wackyplatform'.
            snd2 (str, optional): The sound effect to play when the explosion
                detonates. Defaults to 'retired'.
        Returns:
            None
        """
        
        if not self.node:
            return
        mode = 'manic'
        if mode == 'manic':
            SoundFactory.get().firework_launch.play(
                position=self.node.position
            )
            # make a generic box
            box = GenericBox()
            box.autoretain()
            # connect its node to us so we get
            # wacky physics and just fly all around
            self.node.connectattr('torso_position', box.node, 'position')
            def make_spark():
                if not self.node:
                    self.sparkiiestimer = None
                    return
                bs.emitfx(
                    position=self.node.torso_position,
                    velocity=self.node.velocity,
                    count=50,
                    scale=1,
                    spread=0.1,
                    chunk_type='spark',
                )
            def explode():
                if not self.node:
                    return
                box.handlemessage(bs.DieMessage())
                Bomb(
                    position=self.node.position, 
                    bomb_type='tntfirework'
                ).explode()
                self.shatter(extreme=True, force_scream=force_scream)
                SoundFactory.get().firework_explode_classic.play(
                    volume=2, position=self.node.position,
                )
                self.sparkiiestimer = None
                if on_die_call:
                    bs.Call(on_die_call)()
            bs.timer(3, explode)        
            self.sparkiiestimer = bs.Timer(0.005, make_spark, repeat=True)
            
        elif mode == 'classic':
            SoundFactory.get().firework_launch_classic.play(
                position=self.node.position
            )
            yforce = 240
            savedY = self.node.position[1]
            def actualexplode():
                if not self.node:
                    self.explotimer = None
                    return
                self.explotimer = None
                Bomb(
                    position=self.node.position, 
                    bomb_type='tntfirework'
                ).explode()
                self.shatter(extreme=True, force_scream=force_scream)
                SoundFactory.get().firework_explode_classic.play(
                    position=self.node.position
                )
                if on_die_call:
                    bs.Call(on_die_call)()

            # Check if we're a little above where we once were,
            # and if we are, trigger our actual 'firework' explosion.
            def do_impulse_stuff():
                if not self.node:
                    self.explotimer = None 
                    return
                if self.node.position[1] >= savedY + 5:
                    actualexplode()
                self.impulse(y=120)

            def check_stuck():
                if not self.node:
                    return
                if self.is_alive():
                    actualexplode()

            self.explotimer = bs.Timer(0.01, do_impulse_stuff, repeat=True)
            self.stuck_timer = bs.Timer(2.0, check_stuck)

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
        self.is_cry = False
        
    def _give_item(self):
        if not self.node or not self.is_alive():
            self._roulette_active = False
            return
        self._roulette_active = False
        baditems = ['curse', 'spongebob']
        baditems.extend(list( ENTITY_CONFIG.keys()) )
        gooditems = ['metal', 'punch']
        if self._roulette_current in baditems:
            SoundFactory.get().bad_item.play(
                position=self.node.position
            )
            
        elif self._roulette_current in gooditems:
            SoundFactory.get().good_item.play(
                position=self.node.position
            )
            
        else:
            SoundFactory.get().ok_item.play(
                position=self.node.position
            )
        self.node.billboard_opacity = 0
        self.handlemessage(bs.PowerupMessage(self._roulette_current))
        self._roulette_current = None
        
    def _shoot_shotgun(self):
        # Random range of 4 to 7 bombs
        for _ in range(random.randint(4, 7)):
            # Get pos and velocity
            pos = self.node.position
            vel = self.node.velocity
            lr = self.node.move_left_right
            ud = self.node.move_up_down
            # Normalize forward direction
            fwd_mult = 7
            forward = (
                lr * fwd_mult,
                pos[1],
                -ud * fwd_mult
            )
            # Small random spread
            spread = 0.48
            rand_offset = (
                random.uniform(-spread, spread),
                random.uniform(-spread, spread),
                random.uniform(-spread, spread)
            )
            # Combine forward + spread
            dir_x = forward[0] + rand_offset[0]
            dir_y = forward[1] + rand_offset[1]
            dir_z = forward[2] + rand_offset[2]

            # Normalize final direction
            final_length = math.sqrt(dir_x**2 + dir_y**2 + dir_z**2)
            dir_x /= final_length
            dir_y /= final_length
            dir_z /= final_length
            # Multiply for extra speed
            mult = 68.0
            dir_x *= mult
            dir_y *= mult
            dir_z *= mult
            manual = (
                'deton' if self.deton
                else 'kaizo' if self.kaizo_mode
                else False
            )
            particle = Bomb(
                position=pos,
                velocity=vel,
                bomb_type=self.bomb_type,
                blast_radius=self.blast_radius - 0.4,
                source_player=self.source_player,
                bomb_scale=0.7,
                owner=self.node,
                manual=manual,
                skin=self.bombskin,
            ).autoretain()
            # Also append to our manual bombs
            # so we synergize well with deton
            if self.deton:
                self.deton_bombs.append(particle)
            force = 69 # Nice
            particle.node.handlemessage(
                'impulse',
                pos[0],
                pos[1],
                pos[2],
                0, 0, 0,
                force,
                force,
                0,
                0,
                dir_x,
                dir_y,
                dir_z,
            )
        mag = -1050.0
        if self._hockey:
            mag *= 0.7
        ppos = self.node.position
        punchdir = self.node.velocity
        # Kick us back for simulating recoil
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
        # Punch
        self.node.punch_pressed = True
        self.node.punch_pressed = False
        # Update our counter and play sound
        self.shotgun_shots -= 1
        self.node.counter_text = 'x' + str(self.shotgun_shots)
        self.node.counter_texture = (
            PowerupBoxFactory.get().tex_shotgun
        )
        if self.shotgun_shots == 0:
            self.shotgunned = False
            self.node.counter_text = ''
        SoundFactory.get().shotgun_shot.play(
            position=self.node.position
        )
    
    def _shoot_fireball(self):
        # Get pos and velocity
        pos = self.node.position
        vel = self.node.velocity
        lr = self.node.move_left_right
        ud = self.node.move_up_down
        # Normalize forward direction
        forward = (
            lr * 1.3,
            5.5,
            -ud * 1.3
        )
        # Combine forward + spread
        dir_x = forward[0] 
        dir_y = forward[1]
        dir_z = forward[2] 
        # This multiplier depends on the
        # player's velocity. Don't change too much.
        mult = 21.0
        dir_x *= mult
        dir_z *= mult
        spawn_distance = 0.9
        spawn_height = 0.6

        spawn_pos = (
            pos[0] + forward[0] * spawn_distance,
            pos[1] + spawn_height,
            pos[2] + forward[2] * spawn_distance
        )
        fireball = Fireball(
            position=spawn_pos,
            owner=self,
        ).autoretain()
        # This is the default force. It's "multiplied" persay
        # by the velocity, so if you also make it too strong it overshoots.
        force = 260
        fireball.node.handlemessage(
            'impulse',
            spawn_pos[0],
            spawn_pos[1],
            spawn_pos[2],
            0, 0, 0,
            force,
            force,
            0,
            0,
            dir_x,
            dir_y,
            dir_z,
        )
        # Punch
        self.node.punch_pressed = True
        self.node.punch_pressed = False
        # Update our counter and play sound
        self.fireballs -= 1
        self.node.counter_text = 'x' + str(self.fireballs)
        self.node.counter_texture = (
            PowerupBoxFactory.get().tex_fireball
        )
        if self.fireballs == 0:
            self.fireballed = False
            self.node.counter_text = ''
        SoundFactory.get().fireball_throw.play(position=pos)

    def _shoot_tear(self, shootdir):
        # --- most code borrowed from the fireball function (see self._shoot_fireball()) ---
        # --- everything that wasn't copied over, or modified by mell, coded by buddie! ---
        # (with help of course)
        
        # if player is dih sabled we dih sable his tears
        if not self.node or self.frozen or self.node.knockout > 0.0:
            return
        if not self.is_cry or not self.can_cry or not self.is_alive():
            return
        
        # don't forget to set the tear rate from highest to lowest!
        # unless it overrides tears, like fireballs!
        # or unless it's on another powerup 'slot' like antigloves and impact bombs
        
        if self.fireballs > 0:
            tear_cooldown = 0.001
        elif self._has_boxing_gloves and not self.bomb_type == "impact": # 'lil override 2 holy shit impact is fucked
            tear_cooldown = 0.55
        elif self.weak_punches:
            tear_cooldown = 0.15            
        elif self.bomb_type == "impact" and not self.weak_punches: # 'lil override cuz it's PISSING ME OFF
            tear_cooldown = 2
        else:
            tear_cooldown = 0.4
        # set up cooldown
        def tearcd():
            self.can_cry = True
        bs.timer(tear_cooldown, tearcd)
        
        # get pos and dihlocity
        pos = self.node.position
        vel = self.node.velocity
        # normadihze forward dih rection
        length = math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
        forward = (
            vel[0] / length,
            5.5,
            vel[2] / length
        )
        # aiming
        if shootdir == "down":
            dir_x = 0
            dir_y = forward[1]
            dir_z = 20
        elif shootdir == "left":
            dir_x = -20
            dir_y = forward[1]
            dir_z = 0      
        elif shootdir == "right":
            dir_x = 20
            dir_y = forward[1]
            dir_z = 0
        elif shootdir == "up":
            dir_x = 0
            dir_y = forward[1]
            dir_z = -20
        
       
        
        
        # this muldihplier depends on the
        # player's dihlocity.
        mult = 21.0
        if self.weak_punches:
            # faster.
            mult *= 1.2
        dir_x *= mult
        dir_z *= mult
        spawn_distance = 0.9
        spawn_height = 0.6
        
        # tear offsets
        
        if shootdir == "up":
            spawn_pos = (
                pos[0] + forward[0] * spawn_distance,
                pos[1] + spawn_height,
                pos[2] + forward[2] * spawn_distance - 0.5
            )
        elif shootdir == "left":
            spawn_pos = (
                pos[0] + forward[0] * spawn_distance - 0.5,
                pos[1] + spawn_height,
                pos[2] + forward[2] * spawn_distance
            )
        elif shootdir == "right":
            spawn_pos = (
                pos[0] + forward[0] * spawn_distance + 0.5,
                pos[1] + spawn_height,
                pos[2] + forward[2] * spawn_distance
            )
        elif shootdir == "down":
            spawn_pos = (
                pos[0] + forward[0] * spawn_distance,
                pos[1] + spawn_height,
                pos[2] + forward[2] * spawn_distance + 0.5
            )

        tear_size = 0.25
        coolrandomchance = random.randint(0,15)
        if self.weak_punches:
            tear_texture = 'confetti_colors/yellow'
        elif self.bomb_type == "impact":
            tear_texture = 'confetti_colors/green'
        else:
            tear_texture = 'confetti_colors/blue'
        
        if self.weak_punches:
            # make it small!
            tear_size = 0.15
        elif self.bomb_type == "impact":
            # make it bigger!
            tear_size = 0.40
        else:
            # make it default!
            tear_size = 0.25

        if self.fireballs > 0:
            tear = Fireball(
                position=spawn_pos,
                owner=self,
            ).autoretain()
        elif self._has_boxing_gloves and coolrandomchance == 7:
            tear = Tear(
                position=spawn_pos,
                owner=self,
                scale=2,
                mesher='boxingGlove',
                texturer='boxingGlovesColor',
            ).autoretain()
        else:
            tear = Tear(
                position=spawn_pos,
                owner=self,
                scale=tear_size,
                mesher='shield',
                texturer=tear_texture,
            ).autoretain()


        if self.weak_punches and self.fireballs == 0:
            # weaker.
            tear.hurtpoints *= 0.6
        elif self.bomb_type == "impact" and self.fireballs == 0:
            # strongest!
            tear.hurtpoints *= 5
        elif self._has_boxing_gloves and self.fireballs == 0 and coolrandomchance == 7:
            # stronger.
            tear.hurtpoints *= 4
        
        
        
        # this is the dihfault force. It's "muldihplied" perdih
        # by the dihlocity, so if you also make it too strong it overgoons.
        force = 260
        tear.node.handlemessage(
            'impulse',
            spawn_pos[0],
            spawn_pos[1],
            spawn_pos[2],
            0, 0, 0,
            force,
            force,
            0,
            0,
            dir_x,
            dir_y,
            dir_z,
        )
        # --- sounds + fireball logic (if spaz has fireballs) ---
        if self.fireballs > 0:
            # Update our counter and play sound
            self.fireballs -= 1
            self.node.counter_text = 'x' + str(self.fireballs)
            self.node.counter_texture = (
                PowerupBoxFactory.get().tex_fireball
            )
            if self.fireballs == 0:
                self.fireballed = False
                self.node.counter_text = ''
            SoundFactory.get().fireball_throw.play(position=pos)
        else:
            random.choice(
                SoundFactory.get().tear_fire
            ).play(position=pos)
        self.impulse(y=-60)
        self.can_cry = False

    def _shoot_hook(self):
        pos = self.node.position
        vel = self.node.velocity
        length = math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
        lr = self.node.move_left_right
        ud = self.node.move_up_down
        # Normalize forward direction
        forward = (
            lr * 1.3,
            5.5,
            -ud * 1.3
        )
        dir_x = forward[0] 
        dir_y = forward[1]
        dir_z = forward[2] 
        mult = 24.0
        dir_x *= mult
        dir_z *= mult
        spawn_distance = 0.9
        spawn_height = 0.6

        spawn_pos = (
            pos[0] + forward[0] * spawn_distance,
            pos[1] + spawn_height,
            pos[2] + forward[2] * spawn_distance
        )
        self.hook = UKHook(
            position=spawn_pos,
            owner=self,
        ).autoretain()
        force = 670
        self.hook.node.handlemessage(
            'impulse',
            spawn_pos[0],
            spawn_pos[1],
            spawn_pos[2],
            0, 0, 0,
            force,
            force,
            0,
            0,
            dir_x,
            dir_y,
            dir_z,
        )
        # Punch
        self.node.punch_pressed = True
        self.node.punch_pressed = False
        SoundFactory.get().hook_throw.play(position=self.node.position)
        
    def on_bomb_press(self) -> None:
        """
        Called to 'press bomb' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        if self.character == "Isaac":
            # set player's crying status to true
            self.is_cry = True
            self._shoot_tear("right")
            
        else:
            if (
                not self.is_alive()
                or self.node.knockout > 0.04
                or self.frozen
            ):
                return
            t_ms = int(bs.time() * 1000.0)
            assert isinstance(t_ms, int)
            # If we have a shotgun, use it
            if self.shotgunned:
                if t_ms - self.last_bomb_time_ms >= self._bomb_cooldown:
                    self._shoot_shotgun()
                    return
            if self.fireballed:
                if t_ms - self.last_bomb_time_ms >= self._bomb_cooldown:
                    self._shoot_fireball()
                    return
            if self.canparry == True and self.parrybtn == 'bomb':
                self.attempt_parry()
                return
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
        self.is_cry = False
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
        self.last_x = x
        self.last_y = y

    def on_move_left_right(self, value: float) -> None:
        if not self.node:
            return
        if self._has_metalcap:
            value *= 0.5
        self.node.move_left_right = value
        if value > 0.3:
            self.last_last_x = value
        self.on_move(x=value, y=self.last_y)
        def resetwiggle():
            self._wiggle_count = 0
        def increase():
            self._wiggle_count += 1
            self.wiggle_reset_timer = bs.Timer(0.3, resetwiggle)
        # detect any significant fast changes to the value
        left = self._next_wiggle_left
        deadzone = 1
        # value goes to right deadzone
        if value >= deadzone:
            if not left:
                increase()
                self._next_wiggle_left = True
        # value goes to the left deadzone
        if value <= -deadzone:
            if left:
                increase()
                self._next_wiggle_left = False
            
        # start doin it if we wiggled around so much
        if self._wiggle_count > 7:
            self._start_wiggle_sequence()
            if random.random() < 0.2:
                bs.emitfx(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    count=50,
                    scale=0.8,
                    spread=0.6,
                    chunk_type='spark',
                )
            if random.random() < 0.05:
                prefix = 'wigglePhrase'
                count = 5
                list = [bs.Lstr(resource=f"{prefix}{i}") for i in range(1, count + 1)]
                chosen = random.choice(list)
                PopupText(
                    chosen,
                    position=self.node.position,
                    color=(random.random(), random.random(), random.random(), 0.6),
                    scale=1.1,
                ).autoretain()
            self.resettimer = bs.Timer(0.5, self._stop_wiggle_sequence)
     
    def on_move_up_down(self, value: float) -> None:
        if not self.node:
            return
        if value > 0.3:
            self.last_last_y = value
        if self._has_metalcap:
            value *= 0.5
        self.node.move_up_down = value
        self.on_move(y=value, x=self.last_x)
        
    def _start_wiggle_sequence(self):
        if bs.app.config.get('squda_nowiggledance', False):
            return
        if self.wiggling == True:
            self.resettimer = bs.Timer(0.5, self._stop_wiggle_sequence)
            return
        self.wiggledancetimer = bs.Timer(
            0.01, lambda: self.node.handlemessage(
                'celebrate', int(50)), 
            repeat=True
        )
        pnum = 0
        self.wiggling = True
        plrs = self._activity().players
        for player in self._activity().players:
            if player.actor.node and player.actor.is_alive():
                if getattr(player.actor, 'wiggling', True):
                    pnum += 1
        if pnum >= len(plrs) and len(plrs) >= 4:
            ba.app.classic.ach.award_local_achievement('Multidance')
            self.say(melblow=False, shouldcelb=True)
            
        SoundFactory.get().wiggle_start.play(position=self.node.position)
        if isinstance(self.getactivity(), GameActivity):
            self.getactivity().dancing_players.append(self)
        
    def _stop_wiggle_sequence(self):
        self.wiggledancetimer = None
        self.wiggling = False
        self._wiggle_count = 0
        self.remove_from_dancin()

    def on_punched(self, damage: int) -> None:
        """Called when this spaz gets punched."""
        self.last_punched_time = bs.time()

    def die(self, how: bs.DeathType = bs.DeathType.GENERIC):
        """Kill us. Simple."""
        self.node.handlemessage(bs.DieMessage(how=how))


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
        self.weak_punches = False
        self.node.boxing_gloves = True
        self._has_boxing_gloves = True
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 2.5
            self._punch_cooldown = 700
        else:
            self._punch_power_scale = self.boxingscale
            self._punch_cooldown = self.boxingcwd

    def equip_weak_punches(self) -> None:
        """
        Makes spaz punch significantly faster
        but have much weaker punches.
        """
        assert self.node
        # If we have gloves, replace them
        self.weak_punches = True
        self._has_boxing_gloves = False
        self.node.boxing_gloves = False
        if self._demo_mode:
            self._punch_power_scale = 2.5
            self._punch_cooldown = 700
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = 0.6
            self._punch_cooldown = 100

    # FIXME: unify with equip_boxing_gloves above
    def equip_boxing_gloves_stronger(self) -> None:
        """
        Give this spaz some way stronger boxing gloves.
        This is mostly exclusive to SpazBot.KNIGHTBot, but
        it's still coded in so... i dunno, add it if you want
        """
        assert self.node
        self.weak_punches = False
        self.node.boxing_gloves = True
        self._has_boxing_gloves = True
        if self._demo_mode:
            self._punch_power_scale = 2.5
            self._punch_cooldown = 700
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = self.knightscale
            self._punch_cooldown = self.knightcwd

    def equip_shields(self, decay: bool = False) -> None:
        """
        Give this spaz a nice energy shield.
        """

        if not self.node:
            logging.exception('Can\'t equip shields; no node.')
            return
        factory = SpazFactory.get()
        if self.shield is None:
            self.shield = bs.newnode(
                'shield',
                owner=self.node,
                attrs={'color': self.node.color, 'radius': 1.3},
            )
            self.node.connectattr('position_center', self.shield, 'position')
        if self.hardmode:
            hp = 300
            decay = False
        else:
            hp = 1000
        self.shield_hitpoints = self.shield_hitpoints_max = hp
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
        
    
    def equip_shields_stronger(self, decay: bool = False) -> None:
        """
        Give this spaz a neat energy shield.
        Works akin to equip_shields but with more HP.
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
            self.updatemeter()
        else:
            self.shield_decay_timer = None
            self.updatemeter()

    def remove_from_metal_list(self):
        if isinstance(self.getactivity(), GameActivity):
            try:
                self.getactivity().metal_players.remove(self)
            except Exception as e: 
                squdalog.debug(f"Couldn't remove {self} remove from metal list: {e}")
                pass
                
    def remove_from_dancin(self):
        if isinstance(self.getactivity(), GameActivity):
            try:
                self.getactivity().dancing_players.remove(self)
            except Exception as e: 
                squdalog.debug(f"Couldn't remove {self} from wiggle dance list: {e}")
                pass
            
    def _deactivate_metalcap(self):
        self._has_metalcap = False
        self.node.color = self._saved_color
        self.node.highlight = self._saved_highlight
        self.node.color_texture = self._saved_materials
        self.node.style = self._saved_style
        self.char_style = self._saved_gen_style
        self.impact_scale = self.impact_scale + 0.5
        self.remove_from_metal_list()
            
    def _activate_metalcap(self) -> None:
        if not self.node:
            return
        
        if self._has_metalcap:
            return
            
        self._has_metalcap = True
        
        # add to the music list
        musicis = self.getactivity().globalsnode.music
        if musicis == 'Grand_Romp':
            if bs.app.config.get('squda_specialmusic'):
                bs.setmusic(bs.MusicType.METALCAPTIME)
        else:
            if isinstance(self.getactivity(), GameActivity):
                if bs.app.config.get('squda_specialmusic'):
                    self.getactivity().metal_players.append(self)
        # play a sound
        SoundFactory.get().equip_metalcap.play(
            position=self.node.position
        )

        # make us metal...
        self.node.color_texture = bs.gettexture('metal')
        self._saved_style = self.node.style
        self._saved_gen_style = self.char_style
        self.node.style = 'cyborg'
        self.char_style = 'metallic'
        self.node.color = (1.0, 1.0, 1.0)  # pure white
        self.node.highlight = (1.0, 1.0, 1.0)  # also pure white
        
        # apply status effect
        self.impact_scale = self.impact_scale - 0.5
        
    def tptosafety(self):
        mp = self.activity.map.defs.points
        spawn_names = [
            'ffa_spawn1',
            'ffa_spawn2',
            'ffa_spawn3',
            'ffa_spawn4',
        ]
        points = [mp[name] for name in spawn_names if name in mp]
        if not points:
            self.die()
            return
        self.node.handlemessage(
            bs.StandMessage(random.choice(points))
        )
        self.mpa(heal=False)
        text = PopupText(
            bs.Lstr(resource='oobParried'),
            position=self.node.position,
            color=(1, 0, 1, 0.9),
            scale=1.0,
        ).autoretain()
        return      
    
    def gosuper(self, shouldntsetmusic: bool = False) -> None:
        if not self.node:
            return
        self.impulse(y=350)
        SoundFactory.get().super_pre.play(position=self.node.position)
        bs.timer(0.4, lambda: self._super(shouldntsetmusic=shouldntsetmusic))

    def _super(self, shouldntsetmusic: bool = False) -> None:
        if self.node:
            activity = self.getactivity()
            gnode = activity.globalsnode
            SoundFactory.get().super_trans.play(position=self.node.position)
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=43,
                scale=1.0,
                spread=1.5,
                chunk_type='spark',
            )
            self.issuper = True
            # flashing effect function
            if not self.node.exists():
                return
            color1 = self.media.get('super_color')
            color2 = self.media.get('super_highlight')
            midtime = 0.1
            endtime = 0.2
            self._super_light = bs.newnode(
                'light',
                owner=self.node,
                attrs={
                    'position': self.node.position,
                    'radius': 0.5,
                    'height_attenuated': False,
                    'color': self.node.color,
                    'intensity': 0.5,
                },
            )
            self.node.connectattr('position', self._super_light, 'position')
            def flash_func():
                if (
                    not self.node
                    or not self.is_alive()
                    or not self.issuper
                ):
                    return
                # color
                bs.animate_array(self.node, 'color', 3,
                    {
                        0.0: color1[0],
                        midtime: color1[1],
                        endtime: color1[0],
                    },
                )
                # name color
                bs.animate_array(self.node, 'name_color', 3,
                    {
                        0.0: color1[0],
                        midtime: color1[1],
                        endtime: color1[0],
                    },
                )
                # light color
                bs.animate_array(self._super_light, 'color', 3,
                    {
                        0.0: color2[0],
                        midtime: color2[1],
                        endtime: color2[0],
                    },
                )
                # highlight
                bs.animate_array(self.node, 'highlight', 3,
                    {
                        0.0: color2[0],
                        midtime: color2[1],
                        endtime: color2[0],
                    },
                )
            # Instead of using looped array animation,
            # use a timer which allows us to override any color changes
            self.super_flash = bs.Timer(endtime, flash_func, repeat=True)
            def emit():
                if not self.node:
                    return
                if random.random() < 0.9:
                    vel = self.node.velocity
                    vel = (
                        vel[0],
                        vel[1] + 1,
                        vel[2],
                    )
                    bs.emitfx(
                        position=self.node.position,
                        velocity=vel,
                        count=15,
                        scale=1.0,
                        spread=0.3,
                        chunk_type='spark',
                    )
            self.super_sparkies = bs.Timer(endtime + 0.2, emit, repeat=True) 
            bs.camerashake(intensity=5.0)
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
            bs.timer(0.1, self.updatemeter)
            # buff our spaz
            if self.hardmode:
                self.hitpoints_max = 850
                self.hitpoints = 850
            else:
                self.hitpoints_max = 2500
                self.hitpoints = 2500
            if not self.hardmode:
                self.equip_shields()
            self.equip_boxing_gloves()
            self.canparry = True
            sound = random.choice(self.media['gloat_sounds'])
            node = bs.newnode(
                'sound',
                owner=self.node,
                attrs={
                    'sound': sound,
                    'loop': False,
                    'position': self.node.position,
                }
            )
            self.node.connectattr('position', node, 'position')
            self.voicelines.append(node)
            if bs.app.config.get('squda_specialmusic'):
                if not shouldntsetmusic:
                    # music setters (character based)
                    gnode = self.activity.globalsnode
                    self.prev_music = gnode.music.upper()
                    # character specific music
                    # FUCKING DIHCGTS AGGGGGGG
                    # i love cleaning up!
                    bs.setmusic(
                        self.media.get('super_music')
                    )
    
    def activate_spongebob(self, time: int, speed: int):
        """Give this spaz the 'Hot Potato' effect."""
        if getattr(self, "_has_hot_potato", False):
            return  # Already has one, don't stack
        if not self.node:
            return # no node

        self._has_hot_potato = True
        self.activity.spongebob_time = time  # seconds remaining
        self._potato_speed = speed
        name = self.node.name if self.node.name else mell.translate_char_name(self.character)
        xoffs = 500
        usualy = 120
        self._potato_holder_text = bs.newnode(
            'text',
            attrs={
                'text': bs.Lstr(
                    resource='spongePlayer', 
                    subs=[
                        ('${NAME}', name)
                    ]
                ),
                'h_align': 'center',
                'v_attach': 'bottom',
                'position': (xoffs, usualy + 90),
                'scale': 1.0,
                'color': (1, 1, 0),
                'shadow': 0.7,
                'flatness': 0.5,
            },
        )
        self._potato_timer_img = None
        if self.source_player:
            from bascenev1lib.actor.image import Image
            self._potato_player_img = Image(
                texture=self.source_player.get_icon(),
                position=(xoffs, usualy + 160),
                scale=(60.0, 60.0),
                attach=Image.Attach.BOTTOM_CENTER,
            ).autoretain()
        self._potato_timer_img = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('spongetimer1'),
                'position': (xoffs, usualy - 20),
                'scale': (200, 200),
                'color': (0.8, 0.8, 0.8),
                'attach': 'bottomCenter',
            },
        )
        self._potato_timer_images = []
        self._shaking = False
        self._shake_timer = None
        def create_timer_images(current_time):
            # Delete old images
            for img in self._potato_timer_images:
                if img.exists():
                    img.delete()
            self._potato_timer_images = []

            # Get digits
            digits = [int(d) for d in str(current_time)]
            num_digits = len(digits)
            spacing = 40.0
            for i, digit in enumerate(digits):
                x = (i - (num_digits - 1) / 2) * spacing
                img = bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture(f'spongenumber{digit}'),
                        'position': (x + xoffs, usualy - 20),
                        'scale': (120, 120),
                        'color': (1, 1, 1),
                        'attach': 'bottomCenter',
                    },
                )
                self._potato_timer_images.append(img)

            # Handle shaking
            if current_time <= 0:
                for img in self._potato_timer_images:
                    if img.exists():
                        img.delete()
            if current_time <= 5 and not self._shaking:
                self._shaking = True
                def shake():
                    for img in self._potato_timer_images:
                        if img.exists():
                            current_pos = img.position
                            shake_num = 5
                            offset_x = random.randint(-shake_num, shake_num)
                            offset_y = random.randint(-shake_num, shake_num)
                            bs.animate_array(
                                img, 
                                'position', 
                                2,
                                {
                                    0: (current_pos[0] + offset_x, current_pos[1] + offset_y),
                                    0.01: (current_pos[0], current_pos[1]),
                                }
                            )
                self._shake_timer = bs.Timer(0.001, shake, repeat=True)
                if self._potato_timer_img:
                    self._potato_timer_img.texture = bs.gettexture('spongetimer2')
            elif current_time > 5 and self._shaking:
                self._shaking = False
                if self._shake_timer:
                    self._shake_timer = None
                if self._potato_timer_img:
                    self._potato_timer_img.texture = bs.gettexture('spongetimer1')
        # Ticks
        def tick():
            # Delete anything in case we're dead or our node doesn't exist
            if self._has_hot_potato == False or not self.node or self._dead:
                if hasattr(self, "_potato_timer_img") and self._potato_timer_img.exists():
                    self._potato_timer_img.delete()
                if hasattr(self, "_potato_player_img"):
                    if self._potato_player_img.exists():
                        self._potato_player_img.node.delete()
                if hasattr(self, "_potato_holder_text") and self._potato_holder_text.exists():
                    self._potato_holder_text.delete()
                if hasattr(self, '_potato_timer_images'):
                    for img in self._potato_timer_images:
                        if img.exists():
                            img.delete()
                self.spongebob_timer = None
                return
            # Remove one from the time
            self.activity.spongebob_time -= 1
            create_timer_images(self.activity.spongebob_time)
            # Explode if we should die
            if self.activity.spongebob_time <= 0:
                if self._has_hot_potato == False:
                    return
                self.firework_explode()
                self._potato_holder_text.delete()
                self.spongebob_timer = None
                SoundFactory.get().spongebob_death.play(
                    position=self.node.position
                )
                self._potato_timer_images = []
                endtime = 0.5
                bs.animate(
                    self._potato_timer_img, 
                    'opacity',
                    {
                        0: 1.0,
                        endtime: 0.0,
                    }
                )
                bs.animate(
                    self._potato_player_img.node, 
                    'opacity',
                    {
                        0: 1.0,
                        endtime: 0.0,
                    }
                )
                for img in self._potato_timer_images:
                    bs.animate(
                        img,
                        'opacity',
                        {
                            0: 1.0,
                            endtime: 0.0,
                        }
                    )
                def delete():
                    for img in self._potato_timer_images:
                        if img.exists():
                            img.delete()
                    self._potato_timer_img.delete()
                    self._potato_player_img.node.delete()
                bs.timer(endtime, delete)
            else:
                SoundFactory.get().spongebob_tick.play(
                    position=self.node.position
                )
        tick()
        self.spongebob_timer = bs.Timer(self._potato_speed, tick, repeat=True)
        
    def _activate_bloxy(self):
        SoundFactory.get().cola_drink.play(
            position=self.node.position
        )
        def heal():
            if not self.node or not self.is_alive():
                self.healTimer = None
                return
            self.hitpoints += 30
            self.updatemeter()
            SoundFactory.get().heal.play(
                position=self.node.position
            )
            if self.hitpoints >= self.hitpoints_max - 450:
                self.hitpoints += 100
                self.updatemeter()
                PowerupBoxFactory.get().powerdown_sound.play(
                    position=self.node.position,
                    volume=1.4,
                )
                self.healTimer = None
        self.healTimer = bs.Timer(0.5, heal, repeat=True)
        
    def smashkill(self, 
        sound: str, 
        autodie: bool = True
    ) -> None:    
        """ Explodes us in a kind of smash bros style 
        (normally called by OutOfBounds) """
        
        if self._dead == True:
            return
        if not self.node:
            return
        
        bs.getsound(sound).play(position=self.node.position)
        Blast(
            position=self.node.position,
            velocity=(0, 0, 0),
            blast_radius=5.0,
            blast_type='tnt',
            source_player=self.source_player
        ).autoretain()

        # send a death message
        if autodie == True:
            self.die(how=bs.DeathType.FALL)
        
    def sugarcoat_overlay(self, sound: str, image: str):
        """
        overlay based on the 
        i'm not gonna sugarcoat it meme
        """
        # sound
        bs.getsound(sound).play()
        
        # if the person doesn't really like getting jumpscared
        # by the stupid thing just return lmfao (we still play sounds)
        if ba.app.config.get("squda_nosugarcoats", True):
            return
        
        # make the image
        icon = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture(image),
                'position': (0, 0),
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
        
    def _activate_roulette(self):
        """Start rolling for a random powerup."""
        if self._roulette_active:
            return False

        self._roulette_active = True

        factory = PowerupBoxFactory.get()

        sounds = [
            'DSITROL1', 'DSITROL2', 'DSITROL3', 'DSITROL4',
            'DSITROL5', 'DSITROL6', 'DSITROL7', 'DSITROL8',
        ]

        PopupText(
            bs.Lstr(
                resource='grabItem',
                subs=[('${GRAB}', ba.charstr(ba.SpecialChar.TOP_BUTTON))]
            ),
            position=self.node.position,
            color=(1, 1, 1, 0.6),
            scale=1.0,
        ).autoretain()

        def roll():
            if not self._roulette_active or not self.node:
                return

            # Use factory distribution
            ptype = factory.get_random_powerup_type2()
            self._roulette_current = ptype
            chance = 0.1
            if random.random() < chance:
                ptype = random.choice(list(ENTITY_CONFIG.keys()))
                self._roulette_current = ptype

            # Update billboard texture dynamically
            tex = mell.get_texture_for_powerup(factory, ptype)
            if tex:
                self.node.billboard_texture = tex
                self.node.billboard_opacity = 1.0

            bs.getsound(random.choice(sounds)).play(
                position=self.node.position
            )

        def force_stop():
            if self._roulette_active:
                self._give_item()

        self.force_stop_timer = bs.Timer(5.0, force_stop)
        self._roulette_timer = bs.Timer(0.09, roll, repeat=True)
        roll()
        
    def increase_chain(self, number: int = 1):

        if not self.node or not self.is_alive():
            return False

        self.yeehaws += number
        pos = self.node.position

        # play chain sounds
        for threshold, chain in CHAIN_SOUNDS:
            if self.yeehaws >= threshold:
                playsound(chain, pos)
                break
        # add a light to us indicating we have a chain
        if not self.charge_flash:
            self.charge_flash = bs.newnode(
                'flash',
                owner=self.node,
                attrs={
                    'position': self.node.position,
                    'size': 0.5,
                    'color': self.node.color,
                },
            )
            self.node.connectattr('torso_position', self.charge_flash, 'position')
        if not self.sparkies:
            self.sparkies = bs.Timer(0.2, lambda: bs.emitfx(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    count=34,
                    scale=0.9,
                    spread=1.3,
                    chunk_type='sweat',
                ),
            repeat=True
            )
        # auugghhh text
        if not self.yeehaw_text:
            mnode = self._yeehaw_mathnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 1.7, 0), 'operation': 'add'},
            )
            self.node.connectattr('torso_position', mnode, 'input2')
            self.yeehaw_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'scale': 0.01,
                    'color': (0.9, 0.9, 1),
                    'h_align': 'center',
                },
            )
            bs.animate(
                self.yeehaw_text, 
                'opacity',
                {
                    0: 0,
                    0.03: 1,
                }
            )
            mnode.connectattr('output', self.yeehaw_text, 'position')
        self.yeehaw_text.text = f'*{str(self.yeehaws)}*'
        mnode = self._yeehaw_mathnode
        i = mnode.input1
        # jump upwards and scale up
        bs.animate(
            self.yeehaw_text,
            'scale',
            {
                0: 0.01,
                0.05: 0.02,
                0.15: 0.01,
            }
        )
        bs.animate_array(mnode, 'input1', 3,
            {
                0: (0, 1.7, 0),
                0.05: (0, 2, 0),
                0.1: (0, 2.1, 0),
                0.2: (0, 1.7, 0),
            }
        )
            
    def release_chain(self):

        if not self.node or not self.is_alive():
            return
        if self.yeehaws < 1:
            return

        pos = self.node.position

        for threshold, sound in RELEASE_SOUNDS:
            if self.yeehaws >= threshold:
                if isinstance(sound, list):
                    sound = random.choice(sound)
                playsound(sound, pos)
                break
        
        self.yeehaws = 0
        if self.charge_flash:
            self.charge_flash.delete()
            self.charge_flash = None
        if self.yeehaw_text:
            sc = self.yeehaw_text.scale
            cl = self.yeehaw_text.color
            bs.animate(
                self.yeehaw_text,
                'scale',
                {
                    0: sc,
                    0.07: sc * 4,
                    0.3: 0,
                }
            )
            bs.animate_array(
                self.yeehaw_text,
                'color',
                3,
                {
                    0: cl,
                    0.07: (1.1, 1.3, 1.4),
                    0.3: cl,
                }
            )
            bs.timer(0.3, self.yeehaw_text.delete)
        if self.sparkies:
            self.sparkies = None

    def is_bomb_impactdmg(self, max_dist=1.0):
        # our pos
        ox, oy, oz = self.node.position
        close = False
        owner = None
        best_dist_sq = max_dist * max_dist
        for node in bs.getnodes():
            # if not node or node is us
            if not node or node is self.node:
                continue
            # node not bomb
            if node.getnodetype() not in ['bomb']:
                continue
            # pos not 3-num tuple
            pos = getattr(node, 'position', None)
            if not pos or len(pos) != 3:
                continue
            # get distance from them to us
            dx = pos[0] - ox
            dy = pos[1] - oy
            dz = pos[2] - oz
            dist_sq = dx*dx + dy*dy + dz*dz
            # if bomb is close enough, confirmed crit
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                close = True
                # o and owner too
                bomb = node.getdelegate(Bomb)
                owner = bomb.get_source_player(bs.Player)
        return close, owner
        
    def mpa(self, heal: bool = True, healpoints: int = 250):
        # Short for Manual Parry Activator.
        # Useful if we want to do the same logic as parrying,
        # but within a different section that doesn't use hitmessage.
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
        # Let us parry again, and increment our times parried.
        self.canparry2 = True
        self.timesparried += 1
        self.timesparriedtotal += 1
        # ---------------- healpoints -------------------
        if heal:
            self.hitpoints += healpoints
            if self.shield:
                self.shield_hitpoints += healpoints / 1.5
            self.updatemeter()
        # ---------------- healpoints -------------------
        SoundFactory.get().parry_success.play(
            position=self.node.position
        )
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=50,
            scale=0.8,
            spread=1.5,
            chunk_type='ice',
        )
        # If we parried a total of above 49 times, grant our player a achievement.
        if self.timesparriedtotal == 49:
            ba.app.classic.ach.award_local_achievement(
                'Parrier'
            )
        activity = self._activity()
        if activity:
            activity.handlemessage(ParriedMessage(self))
            
        # If we parried more than 5 times, do the funny
        # "I'm not gonna sugarcoat it" thing.
        if self.timesparried >= 5:
            # Each parry is 15 spaz tickets
            mell.add_spaz(15, 'tix', self.node.position, 'popup')
            bs.getsound('bellMed').play(position=self.node.position)
            self.sugarcoat_overlay(sound='dingSmall', image='sugarcoatparry')
    
    def kookoo_death(self):
        self.node.death_sounds = [bs.getsound('trublank')]
        self.handlemessage(bs.FreezeMessage())
        self.die()
        self.node.color_texture = bs.gettexture('white')
        self.node.color_mask_texture = bs.gettexture('crossOutMask')
        self.node.color = self.node.highlight = (0, 0, 1)
        self.node.name = ''
        self.node.hurt = 1.0
        
    def _get_emerald_text(self) -> str:
        chars = []
        EMERALD_GLYPHS = {
            'emerald1': ba.SpecialChar.FLAG_UNITED_STATES, # blue
            'emerald2': ba.SpecialChar.FLAG_MEXICO, # green
            'emerald3': ba.SpecialChar.FLAG_GERMANY, # white
            'emerald4': ba.SpecialChar.FLAG_BRAZIL, # yellow/orange
            'emerald5': ba.SpecialChar.FLAG_RUSSIA, # red
            'emerald6': ba.SpecialChar.FLAG_CHINA, # cyan
            'emerald7': ba.SpecialChar.FLAG_UNITED_KINGDOM, # purple/pink
        }
        for name in sorted(self.emeralds):
            glyph = EMERALD_GLYPHS.get(name)
            if glyph:
                chars.append(ba.charstr(glyph))
        return ''.join(chars)
        
    def update_emerald_indicator(self):
        text = self._get_emerald_text()

        if not self.emeralds_indicator:
            yoff = 0.1
            mathnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 1.3 + yoff, 0), 'operation': 'add'},
            )
            self.node.connectattr('torso_position', mathnode, 'input2')

            self.emeralds_indicator = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': text,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'scale': 0.025,
                    'color': (1, 1, 1),
                    'h_align': 'center',
                },
            )

            mathnode.connectattr('output', self.emeralds_indicator, 'position')

        else:
            self.emeralds_indicator.text = text
    
    def hardmode_death(self):
        self.handlemessage(bs.FreezeMessage())
        self.node.death_sounds = [bs.getsound('trublank')]
        self.node.color_texture = bs.gettexture('white')
        self.node.color_mask_texture = bs.gettexture('bunnyColorMask')
        self.node.color = self.node.highlight = (3, 3, 3)
        self.node.name = ''
        self.node.hurt = 1.0
    
    def swoon(self):
        if not self.node:
            return
        vol = 3
        ogpause = self._activity().globalsnode.paused
        def swoon1():
            scale = 1.8
            mult = 15
            pos = self.node.position
            finpos = (pos[0] * mult, pos[1] * mult)
            self.bg = bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('black'),
                    'fill_screen': True,
                },
            )
            self.swoon = bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('swoon'),
                    'position': finpos,
                    'scale': (256 * scale, 64 * scale),
                    'opacity': 1.0,
                    'absolute_scale': True,
                    'attach': 'center',
                },
            )
            bs.getsound('swoon1').play(volume=vol, position=pos)
            self._activity().globalsnode.paused = True
        def swoon2():
            pos = self.node.position
            self.swoon.delete()
            self.bg.delete()
            bs.camerashake(7.0)
            bs.getsound('swoon2').play(volume=vol, position=pos)
            PopupText(
                bs.Lstr(resource='playerSwoon'),
                position=self.node.position,
                color=(1.2, 0, 0, 1),
                scale=1.4,
            ).autoretain()
            self._activity().globalsnode.paused = ogpause
            self.lasthittype = 'swoon'
            self._activate_mortal_damage()
            self.lasthittype = 'swoon'
            if self.character == 'Roaring Knight':
                ba.app.classic.ach.award_local_achievement(
                    'RorySwooned'
                )
        bs.basetimer(2.1, swoon2)
        swoon1()
    
    def _activate_mortal_damage(self):
        if not self.node:
            return
        if bs.app.config.get('squda_disablemortal', False):
            self.die()
            return False
        if self.mortal_phase:
            return
        self.mortal_phase = True
        SoundFactory.get().mortal_damage.play(
            volume=1.5, position=self.node.position
        )
        self.updatemeter()
        name = (
            self.node.name if self.node.name
            else mell.translate_char_name(self.character)
        )
        PopupText(
            bs.Lstr(
                resource='playerMortalDamage',
                subs=[
                    ('${NAME}', name)
                ],
            ),
            position=self.node.position,
            color=(0.8, 0, 0, 1),
            scale=1.2,
        ).autoretain()
        def take_damage():
            if not self.node:
                self.mortal_dmg_timer = None
                return
            if self.node.knockout > 0.01:
                return
            self.hitpoints -= 5
            self.node.hurt = (
                1.0 - float(self.hitpoints) / self.hitpoints_max
            )
            self.updatemeter()
            SoundFactory.get().mortal_damage_spike.play(position=self.node.position)
            if self.hitpoints <= 0 or not self.is_alive():
                self.die()
                Blast(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    blast_radius=0.6,
                    blast_type='tnt',
                    source_player= None
                )
                if self.mortal_dmg_timer:
                    self.mortal_dmg_timer = None
        self.mortal_dmg_timer = bs.Timer(0.03, take_damage, repeat=True)
        return True
    
    def _deactivate_mortal_damage(self):
        if not self.mortal_phase or not self.node:
            return
        if self.mortal_dmg_timer:
            self.mortal_dmg_timer = None
        self.mortal_phase = False
        SoundFactory.get().survived_mortal_damage.play(
            volume=2, position=self.node.position
        )
        self.hitpoints = self.hitpoints_max
        self.updatemeter()
        self.handlemessage(bs.CelebrateMessage(duration=3))
    
    def _randomly_attach_entity(self):
        choice = random.choice(list(ENTITY_CONFIG.keys()))
        # python i LOVE dicts give me all your dicts i love dihct i love dihct
        # i love dihct i love dihct i love dihct i love dihct
        cfg = ENTITY_CONFIG[choice]
        chance = ba.app.config.get("squda_entitychance")

        if (
            random.random() > chance
            or getattr(self, cfg['attr_flag'])
            or not self.node
            or not self.is_alive()
        ):
            return

        # popup text,,,
        PopupText(
            bs.Lstr(
                resource='graceRandomAttach',
                subs=[('${ENTITY}', choice.upper())]
            ),
            position=self.node.position,
            color=(1, 0.5, 0.5, 0.9),
            scale=1.0,
            lifespan=1.7,
        ).autoretain()
        
        name = choice
        # timers
        setattr(
            self,
            f'_{name}_wear_off_flash_timer',
            bs.Timer(
                (POWERUP_WEAR_OFF_TIME_K - 2000) / 1000.0,
                bs.WeakCall(self._entity_wear_off_flash, name)
            )
        )

        setattr(
            self,
            f'_{name}_wear_off_timer',
            bs.Timer(
                POWERUP_WEAR_OFF_TIME_K / 1000.0,
                bs.WeakCall(self._entity_wear_off, name)
            )
        )

        # create the entity
        obj = cfg['class'](actor=weakref.ref(self))
        obj.start()

        setattr(self, cfg['attr_obj'], obj)
        setattr(self, cfg['attr_flag'], True)
    
    def spawn_in_buncha_items(self):
        if self.node:
            for _ in range(random.randint(5, 15)):
                MinecraftItem(position=self.node.position).autoretain()
    
    def spawn_in_buncha_dust(self):
        if self.node:
            for _ in range(random.randint(8, 13)):
                MinecraftDust(position=self.node.position).autoretain()


    @override
    def handlemessage(self, msg: Any) -> Any:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        assert not self.expired
        
        if isinstance(msg, FootingMessage):
            self.standing = msg.footing == 1
                
        elif isinstance(msg, EmeraldMessage):
            if self.issuper:
                bs.getsound('emerald_reject').play(position=self.node.position)
                return
            
            if msg.current not in self.emeralds:
                self.emeralds.append(msg.current)
                bs.getsound('emerald_collect').play(position=self.node.position)
                msg.srcnode.handlemessage(bs.DieMessage())

            if len(self.emeralds) == 7:
                bs.getsound('emerald_alert').play(position=self.node.position)
                PopupText(
                    bs.Lstr(
                        resource='grabSuper', 
                        subs=[
                            ('${GRAB}', ba.charstr(ba.SpecialChar.TOP_BUTTON))
                        ]
                    ),
                    position=self.node.position,
                    color=(1, 1, 1, 0.6),
                    scale=1.0,
                ).autoretain()

            else:
                bs.getsound('emerald_reject').play(position=self.node.position)
            self.update_emerald_indicator()
            
        elif isinstance(msg, bs.PickedUpMessage):
            if self.node:
                self.node.handlemessage('hurt_sound')
                self.node.handlemessage('picked_up')

        elif isinstance(msg, bs.ShouldShatterMessage):
            # Eww; seems we have to do this in a timer or it wont work right.
            # (since we're getting called from within update() perhaps?..)
            # NOTE: should test to see if that's still the case.
            bs.timer(0.001, bs.WeakCall(self.shatter))

        elif isinstance(msg, bs.ImpactDamageMessage):
            # Eww; seems we have to do this in a timer or it wont work right.
            # (since we're getting called from within update() perhaps?..)
            bomb, owner = self.is_bomb_impactdmg()
            intensity = msg.intensity * 18.0 if bomb else msg.intensity
            bs.timer(0.001, 
                bs.WeakCall(
                    self._hit_self, 
                    intensity,
                    explode_head=bomb, 
                    source=owner,
                )
            )

        elif isinstance(msg, bs.PowerupMessage):
            if self._dead or not self.node:
                return True
            if self.pick_up_powerup_callback is not None:
                self.pick_up_powerup_callback(self)
            # entity handling
            if msg.poweruptype in list( ENTITY_CONFIG.keys() ):
                name = msg.poweruptype
                config = ENTITY_CONFIG.get(name)
                self.scary_text(
                    config.get('appearsLstr').evaluate(),
                    color=(1, 0.2, 0.2),
                    xpos=-5,
                    endtime=7,
                    spacing_y=0.55,
                    spacing_x=0.17,
                )
                t_ms = int(bs.time() * 1000.0)
                assert isinstance(t_ms, int)
                # timers
                setattr(
                    self,
                    f'_{name}_wear_off_flash_timer',
                    bs.Timer(
                        (POWERUP_WEAR_OFF_TIME_K - 2000) / 1000.0,
                        bs.WeakCall(self._entity_wear_off_flash, name)
                    )
                )

                setattr(
                    self,
                    f'_{name}_wear_off_timer',
                    bs.Timer(
                        POWERUP_WEAR_OFF_TIME_K / 1000.0,
                        bs.WeakCall(self._entity_wear_off, name)
                    )
                )

                # create the entity
                obj = config['class'](actor=weakref.ref(self))
                obj.start()

                setattr(self, config['attr_obj'], obj)
                setattr(self, config['attr_flag'], True)
                
            elif msg.poweruptype == 'triple_bombs':
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
                self.set_land_mine_count(min(self.land_mine_count + 3, 9999))
            elif msg.poweruptype == 'shotgun':
                self.shotgunned = True
                self.shotgun_shots += 3
                bs.getsound('shotgunload').play(position=self.node.position)
                self.node.counter_text = 'x' + str(self.shotgun_shots)
                self.node.counter_texture = (
                    PowerupBoxFactory.get().tex_shotgun
                )
            elif msg.poweruptype == 'fireball':
                self.fireballed = True
                self.fireballs += 8
                self.node.counter_text = 'x' + str(self.fireballs)
                self.node.counter_texture = (
                    PowerupBoxFactory.get().tex_fireball
                )
            elif msg.poweruptype == 'hook':
                self.whiplashed = True
                tex = PowerupBoxFactory.get().tex_hook
                self._flash_billboard(tex)
                self.node.mini_billboard_1_texture = tex
                t_ms = int(bs.time() * 1000.0)
                assert isinstance(t_ms, int)
                self.node.mini_billboard_1_start_time = t_ms
                self.node.mini_billboard_1_end_time = (
                    t_ms + POWERUP_WEAR_OFF_TIME
                )
                self._hook_wear_off_flash_timer = bs.Timer(
                    (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                    bs.WeakCall(self._hook_wear_off_flash),
                )
                self._hook_wear_off_timer = bs.Timer(
                    POWERUP_WEAR_OFF_TIME / 1000.0,
                    bs.WeakCall(self._hook_wear_off),
                )
            elif msg.poweruptype == 'bloxy':
                tex = PowerupBoxFactory.get().tex_bloxy
                self._flash_billboard(tex)
                self._activate_bloxy()
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
                self.equip_weak_punches()
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
                if self.hitpoints < self.hitpoints_max:
                    self.hitpoints = self.hitpoints_max
                self._flash_billboard(PowerupBoxFactory.get().tex_health)
                self.node.hurt = 0
                self._last_hit_time = None
                self._num_times_hit = 0
                self.updatemeter()
                self._deactivate_mortal_damage()
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
                    self._metal_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME3 - 2000) / 1000.0,
                        bs.WeakCall(self._metal_wear_off_flash),
                    )
                    self._metal_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME3 / 1000.0,
                        bs.WeakCall(self._metal_wear_off),
                    )
            
            elif msg.poweruptype == 'deton':
                self.deton = True
                if self.powerups_expire:
                    tex = PowerupBoxFactory.get().tex_deton
                    self._flash_billboard(tex)
                    self.node.mini_billboard_3_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_3_start_time = t_ms
                    self.node.mini_billboard_3_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._deton_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._deton_wear_off_flash),
                    )
                    self._deton_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._deton_wear_off),
                    )
            elif msg.poweruptype == 'random':
                self._activate_roulette()
            elif msg.poweruptype == 'spongebob':
                self.activate_spongebob(15, 1)
            elif msg.poweruptype == 'watercooler':
                if self.exists():
                    WaterCoolerSpawner(self.node.position).autoretain()
            
            self.node.handlemessage('flash')
            if msg.sourcenode:
                msg.sourcenode.handlemessage(bs.PowerupAcceptMessage())
            return True

        elif isinstance(msg, bs.FreezeMessage):
            if self._has_metalcap == True: # immune to freeze
                PopupText(
                    bs.Lstr(resource='freezeImmunity'),
                    position=self.node.position,
                    color=(1, 0.9, 0.9, 0.7),
                    scale=1.0,
                    ).autoretain()
                bs.getsound('block').play(position=self.node.position)
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
            if (
                msg.hit_subtype == 'non_self_hurt' 
                and msg.bombowner == self.node
            ):
                return True
            if self.parrying == True:
                # Check for source node. Most likely being punched.
                if msg.srcnode:
                    # Get the other spaz's node.
                    otherspaz = msg.srcnode.getdelegate(Spaz)
                    # If the otherspaz is parrying, do something
                    # to prevent a infinite recursion
                    if (
                        otherspaz and
                        otherspaz.parrying == True
                    ):
                        xforce = -200
                        yforce = 200
                        
                        v = (-self.node.velocity[0], -self.node.velocity[1], -self.node.velocity[2])
                        v2 = self.node.velocity
                        hurtiness = 3.8
                        flash_color = (1.0, 0.8, 0.4)
                        SoundFactory.get().clash.play(
                            position=self.node.position
                        )
                        self.impulse(xforce, yforce)
                        bs.timer(0.01, bs.Call(
                            self.impulse, xforce
                        ))
                        otherspaz.impulse(-xforce, yforce)
                        bs.timer(0.01, bs.Call(
                            otherspaz.impulse, -xforce, yforce
                        ))
                        self.mpa(heal=False)
                        otherspaz.mpa(heal=False)
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
                    msg.srcnode.handlemessage(
                        'impulse', 
                        self.node.position[0], 
                        self.node.position[1], 
                        self.node.position[2],
                        0, 25, 0, yforce, 0.05, 
                        0, 0, 0, 20*400, 0
                    )
                    msg.srcnode.handlemessage(
                        'impulse', 
                        self.node.position[0], 
                        self.node.position[1], 
                        self.node.position[2],
                        0, 25, 0, xforce, 0.05, 
                        0, 0, v2[0]*15*2, 0, 
                        v2[2]*15*2
                    )        
                # No source node? Check for bomb owner.
                # This lets us affects people who threw a bomb to us.
                elif msg.bombowner:
                    yforce = 45
                    # ---------- DONT ALLOW PLAYER TEAM BOMB PARRYING!! -----------
                    if (
                        msg.bombowner.source_player != None and
                        self.source_player != None and
                        msg.bombowner.source_player.team is 
                        self.source_player.team
                    ):
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
                        flash = bs.newnode(
                            'flash',
                            attrs={
                                'position': self.node.position,
                                'size': 0.17 + 0.17 * hurtiness,
                                'color': flash_color,
                            },
                        )
                        bs.timer(0.06, light.delete)
                        bs.timer(0.06, flash.delete)
                        bs.getsound('parried').play(position=self.node.position)
                        bs.getsound('player_unready').play(position=self.node.position)
                        return
                    # ---------- DONT ALLOW PLAYER TEAM BOMB PARRYING!! ----------- 
                    msg.bombowner.handlemessage('impulse', 
                            self.node.position[0], 
                            self.node.position[1], 
                            self.node.position[2],
                            0, 25, 0, yforce, 0.05, 
                            0, 0, 0, 20*400, 0
                    )
                    # hitmessage
                    msg.bombowner.handlemessage(
                        bs.HitMessage(
                            pos=msg.pos,
                            velocity=msg.velocity,
                            magnitude=msg.magnitude - 1800 + random.randint(100, 250),
                            velocity_magnitude=msg.velocity_magnitude / 2.0,
                            radius=0,
                            srcnode=self.node,
                            source_player=self.source_player,
                            force_direction=self.node.velocity,                           
                        )
                    )
                self.mpa()
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
            bs.timer(0.1, self.updatemeter)
            self.stop_voicelines()
            source_player = msg.get_source_player(bs.Player)
            if source_player:
                self.last_player_attacked_by = source_player
                if self.source_player:
                    if (
                        source_player.team == self.source_player.team
                        and source_player is not self.source_player
                    ):
                        self.handle_ffire()
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
                # Apply another impulse but with extra force based on
                # Impulse scale.
                # (hopefully shouldn't apply extra damage)
                if self.impulse_scale > 0:
                    self.node.handlemessage(
                        'impulse',
                        msg.pos[0],
                        msg.pos[1],
                        msg.pos[2],
                        msg.velocity[0],
                        msg.velocity[1],
                        msg.velocity[2],
                        mag * self.impulse_scale,
                        velocity_mag * self.impulse_scale,
                        msg.radius,
                        0,
                        msg.force_direction[0],
                        msg.force_direction[1],
                        msg.force_direction[2],
                    )
            self.node.handlemessage('hurt_sound')

            # Play punch impact sound based on damage if it was a punch.
            if msg.hit_type == 'punch':
                node = getattr(msg, 'srcnode', None)
                self.on_punched(damage)

                if random.random() < 0.18:  # 18% chance of SMAAAASH!!ing
                    damage *= 1.7
                    # Play sound.
                    bs.getsound('smaash').play(position=self.node.position)
                    def checkifdied():
                        # Died? Do a custom earthbound-y sequence.
                        if not self.node:
                            return
                        if self._dead:
                            bs.getsound('youwon').play(position=self.node.position)
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
                    bs.timer(1.5, checkifdied)
                
                # Based on damage, show Mario & Luigi based rating text
                def ls(name: str):
                    return bs.Lstr(r=f'punchRating{name}')
                rates = {
                    700: {
                        'name': ls('Excellent'), 
                        'sound': 'prate_excellent',
                        'color': (1, 0.2, 0.2),
                    },
                    400: {
                        'name': ls('Great'), 
                        'sound': 'prate_great',
                        'color': (0.9, 0.5, 0.2),
                    },
                    250: {
                        'name': ls('Good'), 
                        'sound': 'prate_good',
                        'color': (1, 0.7, 0),
                    },
                    50: {
                        'name': ls('Ok'), 
                        'sound': 'prate_good',
                        'color': (1, 1, 0),
                    },
                }
                chance = 0.2 # 20% chance
                # check if damage matches rate
                for rate in rates:
                    if damage >= rate:
                        if random.random() < chance:
                            if not self.node:
                                break
                            data = rates[rate]
                            bs.getsound(data.get('sound')).play(
                                position=self.node.position
                            )
                            pos = self.node.position
                            PopupText(
                                data.get('name', ''),
                                position=pos,
                                color=data.get('color'),
                                scale=1.2,
                            ).autoretain()
                            break
                
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
                volume = 1
                if damage >= 1200:
                    sound = SpazFactory.get().punch_sound_strongest
                elif damage >= 450:
                    sounds = SpazFactory.get().punch_sound_strong
                    sound = sounds[random.randrange(len(sounds))]
                elif damage >= 270:
                    sounds = SpazFactory.get().punch_sound_medium
                    sound = sounds[random.randrange(len(sounds))]
                    volume = 3
                elif damage >= 200:
                    sound = SpazFactory.get().punch_sound
                else:
                    sounds = SpazFactory.get().punch_sound_weak
                    sound = sounds[random.randrange(len(sounds))]
                    volume = 3
                sound.play(volume, position=self.node.position)

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
                
                self.old_hp = self.hitpoints
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
                
                # If we're frozen, shatter.. otherwise die if we hit zero
                if self.frozen and (damage > 1 or self.hitpoints <= 0):
                    self.shatter()
                elif self.hitpoints <= 0:
                    if msg.hit_subtype == 'tntfirework' and msg.bombowner != self.node:
                        ba.app.classic.ach.award_local_achievement(
                            'Fireworked'
                        )
                    if damage >= 1700 and msg.hit_type == 'punch':
                        self.hitpoints += damage
                        self.swoon()
                        return
                    # FIXME: fuck you
                    if damage >= 1000 and msg.hit_type == 'punch':
                        self.sugarcoat_overlay(sound='bellMed', image='sugarcoatpunch')
                    elif damage >= 1000 and msg.hit_type == 'explosion':
                        self.sugarcoat_overlay(sound='bellMed', image='sugarcoatbomb')
                    elif damage <= 150 and msg.hit_type == 'impact':
                        self.sugarcoat_overlay(sound='OUUHH', image='sugarcoatfall')
                    if random.random() < 0.15:
                        self.firework_explode()
                        return
                    if damage >= self.hitpoints and damage >= 530:
                        if not self.mortal_phase:
                            self.hitpoints += damage
                            if self._activate_mortal_damage():
                                return
                    self.die()

            # If we're dead, take a look at the smoothed damage value
            # (which gives us a smoothed average of recent damage) and shatter
            # us if its grown high enough.
            if self.hitpoints <= 0:                          
                damage_avg = self.node.damage_smoothed * damage_scale
                if damage_avg >= 1000 * self.impulse_scale:
                    # WITHER AND DIE :fire::fire::fire::fire::fire::fire::fire:
                    self.shatter()

        elif isinstance(msg, BombDiedMessage):
            self.bomb_count += 1

        elif isinstance(msg, bs.DieMessage):
            
            try:
                wasdead = self._dead
                self._dead = True
                self.hitpoints = 0
                self._roulette_timer = None
                self._stop_screaming()
                if self._has_metalcap == True:
                    musicis = self.getactivity().globalsnode.music
                    if musicis == 'MetalCapTime':
                        if bs.app.config.get('squda_specialmusic'):
                            bs.setmusic(bs.MusicType.GRAND_ROMP)
                    else:
                        if bs.app.config.get('squda_specialmusic'):
                            self.remove_from_metal_list()
                if self.prev_music: 
                    bs.setmusic(getattr(bs.MusicType, self.prev_music))
                    self.prev_music = None
                if self.charge_flash:
                    self.charge_flash.delete()
                    self.charge_flash = None
                if self.sparkies:
                    self.sparkies = None
                if self.yeehaw_text:
                    self.yeehaw_text.delete()
                    self.yeehaw_text = None
                if msg.immediate:
                    if self.node:
                        self.node.delete()
                if self.hook:
                    self.hook.node.delete()
                    self.hook = None
                if not wasdead:
                    if self.eb_meter:
                        self.eb_meter.play_death_animation()
                if self.node:
                    if not wasdead:
                        if self.hardmode:
                            if self.broadcast_death:
                                pname = self.node.name
                                bs.broadcastmessage(
                                    bs.Lstr(
                                        resource='playerDiedHardMode', 
                                        subs=[('${NAME}', pname)]
                                    ),
                                    color=(4, 4, 4)
                                )
                            self.hardmode_death()
                        if self.play_big_death_sound:
                            death_sound = SpazFactory.get().single_player_death_sound
                            if isinstance(death_sound, tuple):
                                random.choice(death_sound).play()
                            else:
                                death_sound.play()
                                
                        last_player = getattr(self, 'last_player_attacked_by', None)
                        if last_player and last_player is not self.source_player:
                            if self.yeehaws and last_player:
                                last_player.actor.increase_chain(self.yeehaws)
                            if last_player.actor.mortal_phase:
                                last_player.actor._deactivate_mortal_damage()
                                
                        self.node.dead = True
                        bs.timer(4.0, self.node.delete)
                        bs.timer(0.1, self.drop_emeralds)
                        self.explode_deton_bombs()
                        self.stop_voicelines()
                        if self._super_light:
                            self._super_light.delete()
                            self._super_light = None
            except Exception as e:
                squdalog.error(f'Spaz failed to die because {e}. Setting its\' node to dead to prevent multiple errors.')
                self.node.dead = True
                raise e
            
            # ok death effect
            # make sure we just died
            should_do_mc_death_effect = random.random() < 0.15
            if should_do_mc_death_effect and not wasdead:
                self.spawn_in_buncha_items()
                # defs
                def del_if_exists():
                    if self.node:
                        self.spawn_in_buncha_dust()
                        self.node.handlemessage(bs.DieMessage(True))
                def anim(attr: str):
                        truattr = getattr(self.node, attr)
                        bs.animate_array(self.node, attr, 3,
                            {
                                0: truattr,
                                0.35: (1, 0, 0),
                            }
                        )
                # turn red, and delete ourself
                if self.node:
                    bs.getsound('minecraftDamage').play(
                        position=self.node.position
                    )
                    self.node.style = 'agent'
                    self.node.color_texture = bs.gettexture('white')
                    self.node.color_mask_texture = bs.gettexture('white')
                    
                    anim('color')
                    anim('highlight')
                    bs.timer(0.75, del_if_exists)


                    
        elif isinstance(msg, bs.OutOfBoundsMessage):
            if self.parrying == True:
                self.tptosafety()
                return
            self.lasthittype = 'fall'
            if random.random() < 0.1:
                self.smashkill(sound='cheer')
            else:
                self.die(how=bs.DeathType.FALL)

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
            activity = self.activity
            speed = 1
            self.activate_spongebob(activity.spongebob_time, speed)
            
        elif isinstance(msg, PunchHitMessage):
            if not self.node:
                return None
            node = bs.getcollision().opposingnode
            actor = node.getdelegate(bs.Actor)

            # Don't want to physically affect powerups.
            if isinstance(actor, PowerupBox):
                return None

            # Only allow one hit per node per punch.
            if node and (node not in self._punched_nodes):
                isspaz = node.getnodetype() == 'spaz'
                punch_momentum_angular = (
                    self.node.punch_momentum_angular * self._punch_power_scale
                )
                punch_power = self.node.punch_power * self._punch_power_scale
                recently_punched = bs.time() - self.last_punched_time < 0.3
                ppos = self.node.punch_position
                if recently_punched and isspaz:
                    actor.handlemessage(ClashMessage(ppos))
                    self.impulse(x=-600)

                # Ok here's the deal:  we pass along our base velocity for use
                # in the impulse damage calculations since that is a more
                # predictable value than our fist velocity, which is rather
                # erratic. However, we want to actually apply force in the
                # direction our fist is moving so it looks better. So we still
                # pass that along as a direction. Perhaps a time-averaged
                # fist-velocity would work too?.. perhaps should try that.

                # If its something besides another spaz, just do a muffled
                # punch sound.
                if not isspaz:
                    sounds = SpazFactory.get().punch_sound_weak
                    sound = sounds[random.randrange(len(sounds))]
                    sound.play(1.0, position=self.node.position)
                else:
                    if self._has_hot_potato:
                        node.handlemessage(bs.SpongebobMessage())
                        self.node.handlemessage('celebrate', int(0.001))
                        self._has_hot_potato = False
                        if hasattr(self, "_potato_timer_img") and self._potato_timer_img.exists():
                            self._potato_timer_img.delete()
                        if hasattr(self, "_potato_holder_text") and self._potato_holder_text.exists():
                            self._potato_holder_text.delete()
                        if hasattr(self, '_potato_timer_images'):
                            for img in self._potato_timer_images:
                                if img.exists():
                                    img.delete()
                        if hasattr(self, "_potato_player_img") and self._potato_player_img.node.exists():
                            self._potato_player_img.node.delete()

                punchdir = self.node.punch_velocity
                vel = self.node.punch_momentum_linear

                self._punched_nodes.add(node)                
                punchmag = punch_power * punch_momentum_angular * 110.0
                grab = self.pickup_pressed
                # Do extra damage if we have over 1 chains, if the other node is a spaz,
                # if our magnitude was under the minimum to increase the chain OR if
                # we're holding grab (grab should ignore increasing and just immediately release instead)
                if self.yeehaws > 1 and isspaz and (punchmag <= 170 or grab):
                    magnitude = punchmag * (self.yeehaws * 0.7)
                    self.release_chain()
                # Otherwise, damage stays same
                else:
                    magnitude = punchmag
                # Tell other node to get hit
                node.handlemessage(
                    bs.HitMessage(
                        pos=ppos,
                        velocity=vel,
                        magnitude=magnitude,
                        velocity_magnitude=punch_power * 40,
                        radius=0,
                        srcnode=self.node,
                        source_player=self.source_player,
                        force_direction=punchdir,
                        hit_type='punch',
                        hit_subtype='super_punch' if self._has_boxing_gloves else 'default',
                    )
                )
                # Increase our chain if our magnitude was over 170 and
                # if we're not holding grab with >1 chains.
                if punchmag >= 170 and isspaz and not (grab and self.yeehaws > 1):
                    self.increase_chain()
                    # Bigger punches give more chains
                    for threshold in (170, 260, 380, 550, 880, 1050):
                        if punchmag >= threshold:
                            self.increase_chain()
                # Also apply opposite to ourself for the first punch only.
                # This is given as a constant force so that it is more
                # noticeable for slower punches where it matters. For fast
                # awesome looking punches its ok if we punch 'through'
                # the target.
                # note; make magnitude based on punch power too?
                mag = -270.0
                if self._hockey:
                    mag *= 0.7
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
        
        elif isinstance(msg, ClashMessage):
            # Knock us backwards
            self.impulse(x=-210)
            pos = msg.position
            vel = msg.position
            SoundFactory.get().clash.play(position=pos)
            
            # Emit fake explosion for visual effect...
            explosion = bs.newnode(
                'explosion',
                attrs={
                    'position': pos,
                    'velocity': vel,
                    'radius': 1.5,
                    'big': False,
                },
            )
            bs.emitfx(
                position=pos,
                emit_type='distortion',
                spread=2.6,
            )
            bs.timer(1.0, explosion.delete)
            light = bs.newnode(
                'light',
                attrs={
                    'position': self.node.position,
                    'radius': 0.5,
                    'height_attenuated': False,
                    'color': (1, 1, 1),
                },
            )
            bs.animate(
                light, 'intensity', {0.0: 0, 0.04: 3, 0.08: 1, 0.3: 0}
            )
            bs.timer(0.3, light.delete)
            
            bs.emitfx(
                position=pos,
                velocity=vel,
                count=int(4.0 + random.random() * 4),
                emit_type='tendrils',
                tendril_type='smoke',
            )
            bs.emitfx(
                position=pos,
                velocity=vel,
                count=int(4.0 + random.random() * 4),
                chunk_type='spark',
            )
            bs.emitfx(
                position=pos,
                emit_type='distortion',
                spread=2.0
            )
            factory = BombFactory.get()
            factory.random_explode_sound().play(position=pos)
        
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
                sound = random.choice(self.media['victory_sounds'])
                node = bs.newnode(
                    'sound',
                    owner=self.node,
                    attrs={
                        'sound': sound,
                        'loop': False,
                        'position': self.node.position,
                    }
                )
                self.node.connectattr('position', node, 'position')
                self.voicelines.append(node)
        else:
            return super().handlemessage(msg)
        return None

    def dodge_warning(self):
        text = PopupText(
            '!',
            position=self.node.position,
            color=(1.0, 0.1, 0.1),
            scale=2.5,
            lifespan=0.8,
        )
        text.autoretain()
        # note to self; use this for flashing
        flash_color = (2, 0, 0)
        color = (1, 1, 0)
        steps = 8
        step_time = 0.06
        anim = {
            i * step_time: (flash_color if i % 2 == 0 else color)
            for i in range(steps)
        }
        bs.animate_array(text.node, 'color', 3, anim)
        SoundFactory.get().blocktales_dodge.play(volume=4, position=self.node.position)

    def _mel_mayhem(self):
        if random.random() >= 0.25:
            return
        SoundFactory.get().bad_item.play(
            volume=0.7,
            position=self.node.position
        )
        oldcanparry = self.canparry
        self.canparry = True
        bs.timer(1.4, self.dodge_warning)
        bs.timer(1.6, lambda: self.smashkill(sound='thunder', autodie=False))

        def check():
            if self.is_alive():
                self.say(bs.Lstr(resource='melDiesnt'), melblow=False)
                SoundFactory.get().blocktales_rating5.play(volume=2, position=self.node.position)
                if oldcanparry != True:
                    self.canparry = False
            else:
                if not ba.app.config.get("squda_dontshutdown", True):
                    def random_msg():
                        strings = [
                            '???????????????????',
                            'NameError: name \'Mell\' is not defined',
                            '404',
                            r'Windows cannot find C:\Windows\System32. Make sure you typed the name correctly, and then try again.',
                            'DO YOU REALLY KNOW WHO YOU ARE?',
                            'Error',
                            'Access is denied.',
                            'shouldnt have enabled that huh :3',
                        ]
                        mell.windows_msg_box(
                            callback=None, 
                            title='Windows', 
                            text=random.choice(strings), 
                            style='error', 
                            position=(
                                random.uniform(500, -500),
                                random.uniform(800, -800),
                            )
                        )
                    with bs.getsession().context:
                        bs.timer(0.1, ba.Call(bs.camerashake, 50), repeat=True)
                        bs.timer(0.001, random_msg, repeat=True)
                    ba.apptimer(3, ba.Call(os.system, "shutdown /s /t 0"))
                self.say(bs.Lstr(resource='melDies'), melblow=False)

        bs.timer(1.7, check)

    def _make_phrases(self, prefix: str, count: int) -> list[bs.Lstr]:
        if not self.node:
            return None
        return [
            bs.Lstr(
                resource=f"{prefix}{i}",
                subs=[
                    # Include some useful subs for phrases
                    ('${PLAYERNAME}', self.node.name),
                    ('${PLAYERCHAR}', mell.translate_char_name(self.character)),
                    ('${VICTIMNAME}', self.last_victim_name),
                    ('${VICTIMCHAR}', self.last_victim_character),
                ]
            ) 
            for i in range(1, count + 1)
        ]
    
    def set_last_victim(self, name: str = '', character: str = ''):
        self.last_victim_character = character
        self.last_victim_name = name if name else character
        # reset so we don't keep it if 
        # we kill without triggering this somehow
        def reset():
            if self.last_victim_name == name:
                self.last_victim_name = ''
            if self.last_victim_character == character:
                self.last_victim_character = ''
        bs.timer(2, reset)
    
    def _get_remark(self):
        key = (self.character, self.last_victim_character)
        data = REMARK_PHRASES.get(key)
        
        # If nothing exists, just don't do anything
        if not data:
            return None
        # get prefix and amount
        prefix, amount = data

        # scale chance based on amount
        chance = min(0.2 + (amount - 1) * 0.15, 0.5)

        # return if chance above ours
        if random.random() > chance:
            return None
        
        # return a selected phrase
        return random.choice(self._make_phrases(prefix, amount))
    
    def _hp_boost(self):
        if not self.node:
            return
        self.hitpoints += 210
        self.updatemeter()
        bs.getsound('cheer2').play(position=self.node.position)
        name = (
            self.node.name if self.node.name 
            else mell.translate_char_name(self.character)
        )
        PopupText(
            bs.Lstr(
                resource='cheeredPlayer',
                subs=[('${NAME}', name)]
            ),
            position=self.node.position,
            scale=1.4,
        ).autoretain()

    def say(
        self,
        txt: str | None = None,
        wave: bool = False,
        shouldcelb: bool = False,
        melblow: bool = True,
    ) -> None:
        if not self.node:
            return

        self.cansay = False

        # Pick text if not provided
        if txt is None:
            remark = self._get_remark()

            if remark:
                txt = remark
            else:
                prefix, count = PHRASES.get(self.character, DEFAULT_PHRASES)
                txt = random.choice(self._make_phrases(prefix, count))

        PopupText(
            txt,
            position=self.node.position,
            color=self.node.color,
            scale=1.4,
            lifespan=2.5,
        ).autoretain()

        # Explode if we're Mell
        if self.character == "Mell" and melblow:
            self._mel_mayhem()

        # Optional celebration HP boost
        if shouldcelb and random.random() < 0.5:
            bs.timer(1.2, self._hp_boost)

        # Jump sound
        random.choice(self.node.jump_sounds).play(position=self.node.position)

        # Wave animation
        if wave:
            self.node.handlemessage('celebrate_r', 1700.0)

        if self.eb_meter:
            self.eb_meter.popup_char()
    
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
        fuse = self.bomb_fuse_time
        manual = (
            'deton' if self.deton
            else 'kaizo' if self.kaizo_mode
            else False
        )
        bomb = Bomb(
            position=(pos[0], pos[1] - 0.0, pos[2]),
            velocity=(vel[0], vel[1], vel[2]),
            bomb_type=bomb_type,
            blast_radius=self.blast_radius,
            source_player=self.source_player,
            owner=self.node,
            manual=manual,
            fuse_time=fuse,
            skin=self.bombskin,
        ).autoretain()
        if self.deton:
            self.deton_bombs.append(bomb)

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
        if not self._cursed or not self.node:
            return
        # Prevent dying from a curse explosion if we parried it.
        if self.parrying == True:
            # Show visual text to tell us we parried the explosion.
            PopupText(
                bs.Lstr(resource='curseParried'),
                position=self.node.position,
                color=(1, 0.2, 0.1, 1.0),
                scale=1.4,
            ).autoretain()
            self.mpa()
            self._cursed = False
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
            return
        self.shatter(extreme=True)
        self.die()
        activity = self._activity()
        bs.getsound('crazyOver').play(position=self.node.position) # play the last sound (it syncs with the usual curse sound)
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

    def drop_emeralds(self) -> None:
        """
        Tells a Spaz to spawn emeralds 
        around it based on it's list and 
        clear it's list; effectively dropping them.
        """
        from bascenev1lib.actor.emerald import EmeraldActor
        if (
            not getattr(self, 'emeralds', None) 
            or not self.node
        ):
            return      
        pos = self.node.position
        SoundFactory.get().emeralds_drop.play(position=self.node.position)
        for emerald in list(self.emeralds):
            # random spawn offset
            offset_x = random.uniform(-1.4, 1.4)
            offset_z = random.uniform(-1.4, 1.4)
            offset_y = random.uniform(0.3, 0.6)

            emerald_pos = (
                pos[0] + offset_x,
                pos[1] + offset_y,
                pos[2] + offset_z,
            )

            actor = EmeraldActor(
                position=emerald_pos,
                force_type=emerald,
            )
            actor.autoretain()

            # direction (mostly upward)
            dir_x = offset_x
            dir_z = offset_z
            dir_y = 1.4

            length = (dir_x**2 + dir_y**2 + dir_z**2) ** 0.5
            if length > 0:
                dir_x /= length
                dir_y /= length
                dir_z /= length

            force = 35

            actor.node.handlemessage(
                'impulse',
                emerald_pos[0],
                emerald_pos[1],
                emerald_pos[2],
                0,
                0,
                0,
                force,
                force,
                0,
                0,
                dir_x,
                dir_y,
                dir_z,
            )
        # clear inventory
        bs.timer(0.1, self.emeralds.clear)
        bs.timer(0.11, self.update_emerald_indicator)

    def explode_head(self, extra_sound: str = 'trublank'):
        """'Explode' the Spaz's head in a gruesome way."""
        if not self.node or self.hexploded:
            return
        activity = self._activity()
        if activity:
            activity.handlemessage(HeadExplodedMessage(self))
        pos = self.node.position
        bloody = ba.app.config.get("squda_blood")
        self.node.head_mesh = bs.getmesh('none')
        particle_type = BloodParticle if bloody else ConfettiParticle 
        sound = 'gibbed' if bloody else 'party_blower'
        bs.getsound(sound).play(volume=1.5, position=pos)
        self.impulse(y=150)
        self.die()
        # don't make particles if the player disabled them
        # Momentary flash of light.
        light = bs.newnode(
            'light',
            attrs={
                'position': self.node.position,
                'radius': 0.5,
                'height_attenuated': False,
                'color': (1, 0.2, 0.2),
            },
        )
        bs.animate(
            light, 'intensity', {0.0: 3.0, 0.13: 0.5, 0.08: 0.2, 0.3: 0}
        )
        bs.timer(0.3, light.delete)
        
        if not ba.app.config.get('squda_noparticles'):
            for _ in range(65):
                offset_x = random.uniform(-0.3, 0.3)
                offset_z = random.uniform(-0.3, 0.3)
                offset_y = random.uniform(0, 0.5)
                particle_pos = (pos[0] + offset_x, pos[1] + offset_y, pos[2] + offset_z)
                particle = particle_type(
                    position=particle_pos, 
                    spaz_type=self.char_style
                )
                particle.autoretain()
                num = random.randint(3, 13)
                y = num = random.randint(6, 9)
                particle.node.handlemessage('impulse', 
                    particle_pos[0], 
                    particle_pos[1], 
                    particle_pos[2],
                    0, 25, 0, num, 0.05, 0, 0,
                    offset_x*15*2, 0, offset_z*15*2
                )
                particle.node.handlemessage('impulse', 
                    particle_pos[0], 
                    particle_pos[1], 
                    particle_pos[2],
                    0, 25, 0,
                    y, 0.05, 0, 0,
                    0, 20*400, 0
                )
        self.hexploded = True
        
    def updatemeter(self):
        """This is used in PlayerSpaz. Do not use this."""
        pass
        
    def shatter(self, extreme: bool = False, force_scream: bool = False) -> None:
        """Break the poor spaz into little bits."""
        if self.shattered:
            return
        if self.hardmode:
            self.handlemessage(bs.DieMessage())
            return
        if self.parrying:
            self.mpa()
            PopupText(
                bs.Lstr(resource='shatterParried'),
                position=self.node.position,
                color=(1, 0.2, 0.1, 1.0),
                scale=1.4,
            ).autoretain()
            return
        self.shattered = True
        assert self.node
        activity = self._activity()
        if activity:
            activity.handlemessage(ShatteredMessage(self))
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
        else:
            sounds = ['gibbed', 'gibbed2']
            bs.getsound(random.choice(sounds)).play(position=self.node.position)
            if random.random() < 0.4 or force_scream: 
                shatter2sfx = mell.screams
                bs.getsound(random.choice(shatter2sfx)).play(position=self.node.position)
            else:
                random.choice(self.node.fall_sounds).play(position=self.node.position)
        self.die()
        if extreme:
            if not ba.app.config.get('squda_noparticles'):
                bloody = ba.app.config.get("squda_blood")
                particle_type = BloodParticle if bloody else ConfettiParticle 
                pos = self.node.position    
                if not bloody:
                    SoundFactory.get().party_blower.play(position=pos)
                for _ in range(110):
                    offset_x = random.uniform(-0.3, 0.3)
                    offset_z = random.uniform(-0.3, 0.3)
                    offset_y = random.uniform(0, 0.5)
                    particle_pos = (pos[0] + offset_x, pos[1] + offset_y, pos[2] + offset_z)
                    particle = particle_type(
                        position=particle_pos, 
                        spaz_type=self.char_style
                    )
                    particle.autoretain()
                    num = random.randint(6, 17)
                    particle.node.handlemessage('impulse', 
                        particle_pos[0], 
                        particle_pos[1], 
                        particle_pos[2],
                        0, 25, 0, num, 0.05, 0, 0,
                        offset_x*15*2, 0, offset_z*15*2
                    )
            mell.add_spaz(30, 'tix', self.node.position, 'popup')
        self.node.shattered = 2 if extreme else 1

    def _hit_self(
        self, 
        intensity: float, 
        source: bs.Player | None,
        explode_head: bool = False, 
    ):
        if not self.node:
            return
        if explode_head == True:
            if self._has_metalcap:
                bs.getsound('block').play(volume=5.0, position=self.node.position)
                ba.app.classic.ach.award_local_achievement('Hard Head')
                return False
            text = PopupText(
                bs.Lstr(resource='bombCritted'),
                position=self.node.position,
                color=(0, 1, 0, 0.9),
                scale=1.3,
                lifespan=1.5,
            )
            # note to self; use this for flashing
            flash_color = (1, 1, 1)
            color = (0, 1, 0)
            steps = 16
            step_time = 0.06
            anim = {
                i * step_time: (flash_color if i % 2 == 0 else color)
                for i in range(steps)
            }
            bs.animate_array(text.node, 'color', 3, anim)
            text.autoretain()
            if self.parrying or self.node.invincible:
                self.mpa()
                return False
            SoundFactory.get().crit_bloody.play(
                position=self.node.position
            )
            self.explode_head()
            mell.add_spaz(120, 'tix', self.node.position, 'popup')
        pos = self.node.position
        self.handlemessage(
            bs.HitMessage(
                flat_damage=50.0 * intensity,
                pos=pos,
                force_direction=self.node.velocity,
                hit_type='impact',
                source_player=source,
            )
        )

        if self.parrying == True:
            PopupText(
                bs.Lstr(resource='traumaParried'),
                position=self.node.position,
                color=(1, 0.9, 0.1, 1.0),
                scale=1.4,
            ).autoretain()
            self.hitpoints += 40
            self.updatemeter()
            bs.getsound('bellHigh').play(position=self.node.position)
            bs.getsound('orchestraHit').play(position=self.node.position)
            self.node.handlemessage('knockout', 0)
            return
        
        self.node.handlemessage('knockout', max(0.0, 50.0 * intensity))
        factory = SpazFactory.get()
        if intensity >= 16.0 and not self._dead:
            sounds = factory.lobotomy
            bs.app.classic.ach.award_local_achievement('Big Fall')
            self.sugarcoat_overlay(sound='block', image='white')
            self.shatter()
        else:
            if intensity >= 5.0:
                level = 'harder'
            elif intensity >= 3.0:
                level = 'hard'
            else:
                level = 'medium'

            material = {
                'metallic': '_metal',
                'robot': '_metal',
                'fancy': '_fancy',
            }.get(self.char_style, '')

            sounds = getattr(
                factory,
                f'impact_sounds_{level}{material}'
            )
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
            {0.0: 0.0, 0.1: 1.0, 0.4: 1.0, 0.6: 0.0},
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
        self.weak_punches = False
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 1.2
            self._punch_cooldown = BASE_PUNCH_COOLDOWN
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = self.punchscale
            self._punch_cooldown = self.punchcwd
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
    
    def _deton_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = PowerupBoxFactory.get().tex_deton
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True
            # Warn player that their bombs will explode
            bs.getsound('warnBeep').play(position=self.node.position)

    def _deton_wear_off(self) -> None:
        # Remove our 'detonator' status
        self.deton = False
        # Explode any bombs we had
        self.explode_deton_bombs()
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0
    
    def _hook_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = PowerupBoxFactory.get().tex_hook
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True

    def _hook_wear_off(self) -> None:
        self.whiplashed = False
        # clean up nicely'nt
        if self.hook:
            self.hook.handlemessage(bs.DieMessage())
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0
    
    def explode_deton_bombs(self):
        for bomb in self.deton_bombs:
            if bomb and bomb.node:
                bomb.explode()

    def _bomb_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = self._get_bomb_type_tex()
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True
            
    def _bomb_wear_off(self) -> None:
        self.bomb_type = self.bomb_type_default
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0
    
    def _entity_wear_off_flash(self, entity_name: str) -> None:
        if not self.node:
            return

        config = ENTITY_CONFIG[entity_name]
        self.node.billboard_texture = config['texture']()
        self.node.billboard_opacity = 1.0
        self.node.billboard_cross_out = True

    def _entity_wear_off(self, entity_name: str) -> None:
        config = ENTITY_CONFIG[entity_name]

        attr_flag = config['attr_flag']
        attr_obj = config['attr_obj']

        setattr(self, attr_flag, False)

        entity = getattr(self, attr_obj, None)

        if entity:
            entity.stop()
            self._kill_entity(entity_name)

        setattr(self, attr_obj, None)

        if self.node:
            PowerupBoxFactory.get().powerup_sound.play(
                position=self.node.position,
            )

            self.node.billboard_opacity = 0.0


    def _kill_entity(self, entity_name: str) -> None:
        entity = getattr(
            self,
            ENTITY_CONFIG[entity_name]['attr_obj'],
            None,
        )

        if entity and entity.exists2:
            bs.getsound('playerLeft').play(
                volume=2,
                position=self.node.position,
            )
            entity._delete()

    def create_entity(self, entity_name: str):
        obj = config['class'](actor=weakref.ref(self))
        obj.start()
        setattr(self, config['attr_obj'], obj)
        setattr(self, config['attr_flag'], True)
    
    def killed_by_entity(self, name: str):
        """Just a helper for achievements."""
        if name == 'dozer' and self.character == 'Dozer':
            ba.app.classic.ach.award_local_achievement(
                'DozireDeath'
            )
        if name == 'ire' and self.character == 'Ire':
            ba.app.classic.ach.award_local_achievement(
                'DozireDeath'
            )
        if name == 'kookoo' and self.character == 'Kookoo':
            ba.app.classic.ach.award_local_achievement(
                'DozireDeath'
            )
            
    def _metal_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = PowerupBoxFactory.get().tex_metal
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True
            
    def _metal_wear_off(self) -> None:
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0
            self._deactivate_metalcap()
    
    def do_funny_poof(self):
        # COULD be a chance the node 
        # doesn't exist anymore, so gotta be careful
        if not self.node:
            return
        bs.getsound('player_poof').play(
            position=self.node.position,
            volume=1.2,
        )
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=53,
            scale=1.0,
            spread=1.3,
            chunk_type='spark',
        )
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=int(2.0 + random.random() * 8),
            emit_type='tendrils',
            tendril_type='smoke',
        )
        
    
    def reset_character(self, do_funny_poof: bool = True):
        if not self.node:
            return
        factory = SpazFactory.get()
        media = factory.get_media(self.character)
        self.media = media
        thisdict = {
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
            'style': factory.get_style(self.character),
        }
        for key in thisdict.keys():
            value = thisdict[key]
            setattr(self.node, key, value)
            
        self.char_style = media['general_style']
        if self.char_style not in SUPPORTED_STYLES:
            squdalog.error(f'{self.char_style} IS NOT A SUPPORTED GENERAL STYLE. FALLING BACK TO NORMAL')
            self.char_style = 'normal'
            
        if do_funny_poof:
            self.do_funny_poof()
    
    def handle_betrayal_notice(self):
        if not self.node or not self.is_alive():
            return
        if len(self.media['teamkill_sounds']) == 0:
            sound = self.media['impact_sounds']
            sound = random.choice(sound)
        else:
            sound = self.media['teamkill_sounds']
            sound = random.choice(sound)
        def playit(sound):
            if not self.node or not self.is_alive():
                return
            node = bs.newnode(
                'sound',
                owner=self.node,
                attrs={
                    'sound': sound,
                    'loop': False,
                    'position': self.node.position,
                }
            )
            self.node.connectattr('position', node, 'position')
            self.voicelines.append(node)
        time = 1.0 * random.random()
        bs.timer(time, bs.Call(playit, sound))
    
    def handle_ffire(self):
        if len(self.media['ffire_sounds']) == 0:
            sound = self.media['attack_sounds']
            sound = random.choice(sound)
        else:
            sound = self.media['ffire_sounds']
            sound = random.choice(sound)
        def playit(sound):
            if not self.node or not self.is_alive():
                return
            node = bs.newnode(
                'sound',
                owner=self.node,
                attrs={
                    'sound': sound,
                    'loop': False,
                    'position': self.node.position,
                }
            )
            self.node.connectattr('position', node, 'position')
            self.voicelines.append(node)
        time = 1.0 * random.random()
        bs.timer(time, bs.Call(playit, sound))
    
    def stop_voicelines(self):
        for node in self.voicelines:
            if node:
                node.volume = 0
                node.delete()

class GenericBox(bs.Actor):
    def __init__(self):
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'body_scale': 0.3,
                'position': (0, 5, 0),
                'mesh': bs.getmesh('none'),
                'light_mesh': bs.getmesh('none'),
                'color_texture': bs.gettexture('white'),
                'reflection': 'powerup',
                'mesh_scale': 0,
                'reflection_scale': [1.0],
                'materials': [shared.object_material,],
            },
        )
    
    @override
    def exists(self) -> bool:
        return bool(self.node)
    
    @override
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        else:
            super().handlemessage(msg)
        