# Released under the MIT License. See LICENSE for details.
#
"""Appearance functionality for spazzes."""
from __future__ import annotations

import bascenev1 as bs
import babase as ba
import fromgoverhaul.mell_resources as mell

def clean_account_name(s: str) -> str:
    return "".join(c for c in s if not (0xE000 <= ord(c) <= 0xF8FF))

def get_appearances(include_locked: bool = False) -> list[str]:
    """Get the list of available spaz appearances."""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    plus = bs.app.plus
    assert plus is not None

    assert bs.app.classic is not None
    applist = []
    get_purchased = plus.get_v1_account_product_purchased
    disallowed = []
    display = plus.get_v1_account_display_string()
    name = clean_account_name(display)
    character_dict = mell.appearance_dict
    if not include_locked:
        # get store purchases
        # dicts always come to clutch!
        owned = ba.app.config.get('squda_storeowned')
        for item in character_dict.keys():
            if item not in owned:
                disallowed.append(character_dict[item])
    for s in list(bs.app.classic.spaz_appearances.keys()):
        if bs.app.classic.spaz_appearances[s].hidden:
            disallowed.append(s)
        if s not in disallowed:
            applist.append(s)
    for name in bs.app.classic.spaz_appearances:
        validate_appearance(name, bs.app.classic.spaz_appearances[name])
    return applist


class Appearance:
    """Create and fill out one of these suckers to define a spaz appearance."""

    def __init__(self, name: str):
        assert bs.app.classic is not None
        self.name = name
        if self.name in bs.app.classic.spaz_appearances:
            raise RuntimeError(
                f'spaz appearance name "{self.name}" already exists.'
            )
        bs.app.classic.spaz_appearances[self.name] = self
        self.skin_name = ''
        self.hidden = False
        self.color_texture = 'white'
        self.color_mask_texture = 'white'
        self.icon_texture = 'white'
        self.earthportrait = 'earthbound/spazbound'
        self.EBlose = 'earthbound/spazbound_lose'
        self.EBwin = 'earthbound/spazbound_win'
        self.icon_mask_texture = 'white'
        self.head_mesh = 'none'
        self.torso_mesh = 'none'
        self.pelvis_mesh = 'none'
        self.upper_arm_mesh = 'none'
        self.forearm_mesh = 'none'
        self.hand_mesh = 'none'
        self.upper_leg_mesh = 'none'
        self.lower_leg_mesh = 'none'
        self.toes_mesh = 'none'
        self.jump_sounds: list[str] = ['trublank']
        self.attack_sounds: list[str] = ['trublank']
        self.impact_sounds: list[str] = ['trublank']
        self.death_sounds: list[str] = ['trublank']
        self.pickup_sounds: list[str] = ['trublank']
        self.victory_sounds: list[str] = ['default_win']
        self.gloat_sounds: list[str] = ['default_gloat']
        self.fall_sounds: list[str] = []
        self.ffire_sounds: list[str] = []
        self.teamkill_sounds: list[str] = []
        self.style = 'spaz'
        self.expression_changes = {}
        self.general_style = 'normal'
        self.default_color: tuple[float, float, float] | None = None
        self.default_highlight: tuple[float, float, float] | None = None
        self.super_color: list[
            tuple[float, float, float], 
            tuple[float, float, float]
        ] = [(1, 1, 0), (1, 1, 1)]
        self.super_highlight: list[
            tuple[float, float, float], 
            tuple[float, float, float]
        ] = [(1, 1, 0), (1, 1, 1)]
        self.super_music: bs.MusicType = bs.MusicType.SUPER
        self.is_gimmick_character: bool = False

def validate_appearance(name, app):
    required = [
        "jump_sounds",
        "attack_sounds",
        "impact_sounds",
        "death_sounds",
        "pickup_sounds",
        "fall_sounds",
        "victory_sounds",
        "gloat_sounds",
        "earthportrait",
        "EBwin",
        "EBlose",
    ]

    missing = []

    for field in required:
        if not hasattr(app, field):
            missing.append(field)

    if missing:
        print(f"[APPEARANCE MISSING ASSETS] {name}: {', '.join(missing)}")

def register_appearances() -> None:
    """Register our builtin spaz appearances."""

    # This is quite ugly but will be going away so not worth cleaning up.
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    # spazling #######################################
    t = Appearance('Spaz')
    t.color_texture = 'spazlingColor'
    t.color_mask_texture = 'spazlingColorMask'
    t.icon_texture = 'spazlingIcon'
    t.earthportrait = 'earthbound/spazbound'
    t.EBwin = 'earthbound/spazbound_win'
    t.EBlose = 'earthbound/spazbound_lose'
    t.icon_mask_texture = 'spazlingIconCM'
    t.head_mesh = 'spazlingHead'
    t.torso_mesh = 'spazlingTorso'
    t.pelvis_mesh = 'spazlingPelvis'
    t.upper_arm_mesh = 'spazlingUpperArm'
    t.forearm_mesh = 'spazlingForeArm'
    t.hand_mesh = 'spazlingHand'
    t.upper_leg_mesh = 'spazlingUpperLeg'
    t.lower_leg_mesh = 'spazlingLowerLeg'
    t.toes_mesh = 'spazlingToes'
    t.jump_sounds = ['voicelines/spaz/jump0' + str(i + 1) + '' for i in range(4)]
    t.attack_sounds = ['voicelines/spaz/attack0' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/spaz/hurt0' + str(i + 1) + '' for i in range(4)]
    t.death_sounds = ['voicelines/spaz/death0' + str(i + 1) + '' for i in range(4)]
    t.pickup_sounds = ['voicelines/spaz/pickup']
    t.victory_sounds = ['voicelines/spaz/win']
    t.gloat_sounds = ['voicelines/spaz/gloat']
    t.fall_sounds = ['voicelines/spaz/fall0' + str(i + 1) + '' for i in range(4)]
    t.style = 'agent'

    # Roaring Knight's right hand they/them #####################################
    t = Appearance('Kris')
    t.color_texture = 'krisColor'
    t.color_mask_texture = 'krisColorMask'
    t.icon_texture = 'krisIcon'
    t.earthportrait = 'earthbound/krisbound'
    t.EBwin = 'earthbound/krisbound'
    t.EBlose = 'earthbound/krisbound_lose'
    t.icon_mask_texture = 'krisIconCM'
    t.head_mesh = 'krisHead'
    t.torso_mesh = 'krisTorso'
    t.pelvis_mesh = 'krisPelvis'
    t.upper_arm_mesh = 'krisUpperArm'
    t.forearm_mesh = 'krisForeArm'
    t.hand_mesh = 'krisHand'
    t.upper_leg_mesh = 'krisUpperLeg'
    t.lower_leg_mesh = 'krisLowerLeg'
    t.toes_mesh = 'krisToes'
    t.jump_sounds = ['voicelines/kris/jump']
    t.attack_sounds = ['voicelines/kris/attack' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/kris/hurt' + str(i + 1) + '' for i in range(4)]
    t.death_sounds = ['voicelines/kris/death']
    t.pickup_sounds = ['voicelines/kris/pickup']
    t.fall_sounds = ['voicelines/kris/fall']
    t.victory_sounds = ['voicelines/kris/win']
    t.gloat_sounds = ['voicelines/kris/gloat']
    t.style = 'agent'
    t.default_color = (0.4588235294117647, 0.984313725490196, 0.9294117647058824)
    t.default_highlight = (0.9215686274509803, 0.0, 0.5843137254901961)

    # Prince of the Dark ###################################
    t = Appearance('Ralsei')
    t.color_texture = 'ralseiColor'
    t.color_mask_texture = 'ralseiColorMask'
    t.icon_texture = 'ralsIcon'
    t.earthportrait = 'earthbound/ralseibound'
    t.EBlose = 'earthbound/ralseibound_lose'
    t.EBwin = 'earthbound/ralseibound_win'
    t.icon_mask_texture = 'ralsIconCM'
    t.head_mesh = 'ralseiHead'
    t.torso_mesh = 'ralseiTorso'
    t.pelvis_mesh = 'ralseiPelvis'
    t.upper_arm_mesh = 'ralseiUpperArm'
    t.forearm_mesh = 'ralseiForeArm'
    t.hand_mesh = 'ralseiHand'
    t.upper_leg_mesh = 'ralseiUpperLeg'
    t.lower_leg_mesh = 'ralseiLowerLeg'
    t.toes_mesh = 'none'
    ralsei_sounds = ['voicelines/ralsei/sound' + str(i + 1) + '' for i in range(4)]
    ralsei_hit_sounds = ['voicelines/ralsei/hit']
    t.jump_sounds = ralsei_sounds
    t.attack_sounds = ralsei_sounds
    t.impact_sounds = ralsei_hit_sounds
    t.death_sounds = ['voicelines/ralsei/death']
    t.pickup_sounds = ralsei_sounds
    t.fall_sounds = ['voicelines/ralsei/fall']
    t.victory_sounds = ['voicelines/ralsei/win']
    t.gloat_sounds = ['voicelines/ralsei/gloat']
    t.style = 'bones'
    t.default_color = (0.0, 0.7699999999999998, 0.11999999999999998)
    t.default_highlight = (1, 0.08, 0.5)
    
    # jump twinny ###################################
    t = Appearance('Ire')
    t.color_texture = 'ireColor'
    t.color_mask_texture = 'ireColorMask'
    t.icon_texture = 'ireIcon'
    t.earthportrait = 'earthbound/irebound'
    t.EBlose = 'earthbound/irebound_lose'
    t.EBwin = 'earthbound/irebound_win'
    t.icon_mask_texture = 'ireIconCM'
    t.head_mesh = 'ireHead'
    t.torso_mesh = 'ireTorso'
    t.pelvis_mesh = 'irePelvis'
    t.upper_arm_mesh = 'ireUpperArm'
    t.forearm_mesh = 'ireForeArm'
    t.hand_mesh = 'ireHand'
    t.upper_leg_mesh = 'ireUpperLeg'
    t.lower_leg_mesh = 'ireLowerLeg'
    t.toes_mesh = 'none'
    t.jump_sounds = ['voicelines/hatkid/jump' + str(i + 1) + '' for i in range(4)]
    t.attack_sounds = ['voicelines/hatkid/attack' + str(i + 1) + '' for i in range(6)]
    t.impact_sounds = ['voicelines/hatkid/hurt' + str(i + 1) + '' for i in range(5)]
    t.death_sounds = ['voicelines/hatkid/death']
    t.pickup_sounds = t.attack_sounds
    t.fall_sounds = ['voicelines/hatkid/fall']
    t.victory_sounds = ['voicelines/hatkid/win']
    t.gloat_sounds = ['voicelines/hatkid/gloat']
    t.style = 'bones'
    t.default_color = (1, 1, 1)
    t.default_highlight = (0, 0, 0)

    # crouch twinny ###################################
    t = Appearance('Dozer')
    t.color_texture = 'dozerColor'
    t.color_mask_texture = 'dozerColorMask'
    t.icon_texture = 'dozerIcon'
    t.icon_mask_texture = 'dozerIconCM'
    t.earthportrait = 'earthbound/dozerbound'
    t.EBlose = 'earthbound/dozerbound_lose'
    t.EBwin = 'earthbound/dozerbound_win'
    t.head_mesh = 'dozerHead'
    t.torso_mesh = 'dozerTorso'
    t.pelvis_mesh = 'dozerPelvis'
    t.upper_arm_mesh = 'dozerUpperArm'
    t.forearm_mesh = 'dozerForeArm'
    t.hand_mesh = 'dozerHand'
    t.upper_leg_mesh = 'dozerUpperLeg'
    t.lower_leg_mesh = 'dozerLowerLeg'
    t.toes_mesh = 'none'
    t.jump_sounds = ['voicelines/snakey/attack' + str(i + 1) + '' for i in range(7)]
    t.attack_sounds = ['voicelines/snakey/attack' + str(i + 1) + '' for i in range(7)]
    t.impact_sounds = ['voicelines/snakey/hurt' + str(i + 1) + '' for i in range(8)]
    t.death_sounds = ['voicelines/snakey/death']
    t.pickup_sounds = ['voicelines/snakey/attack' + str(i + 1) + '' for i in range(7)]
    t.fall_sounds = ['voicelines/snakey/fall' + str(i + 1) + '' for i in range(2)]
    t.gloat_sounds = ['voicelines/snakey/gloat']
    t.victory_sounds = ['voicelines/snakey/win']
    t.style = 'bones'
    t.default_color = (1, 1, 0)
    t.default_highlight = (0, 0.3, 1)
    
    # stop holding stuff twinny ###################################
    t = Appearance('Kookoo')
    t.color_texture = 'kookuColor'
    t.color_mask_texture = 'kookuColorMask'
    t.icon_texture = 'kookuIcon'
    t.icon_mask_texture = 'kookuIconCM'
    t.earthportrait = 'earthbound/dozerbound'
    t.EBlose = 'earthbound/dozerbound_lose'
    t.EBwin = 'earthbound/dozerbound_win'
    t.head_mesh = 'kookuHead'
    t.torso_mesh = 'kookuTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'kookuUpperArm'
    t.forearm_mesh = 'kookuForeArm'
    t.hand_mesh = 'kookuHand'
    t.upper_leg_mesh = 'kookuUpperLeg'
    t.lower_leg_mesh = 'kookuLowerLeg'
    t.toes_mesh = 'none'
    noob_sounds = ['voicelines/noob/sound' + str(i + 1) + '' for i in range(6)]
    t.jump_sounds = noob_sounds
    t.attack_sounds = noob_sounds
    t.impact_sounds = ['voicelines/noob/hurt' + str(i + 1) + '' for i in range(7)]
    t.death_sounds = ['voicelines/noob/death']
    t.pickup_sounds = noob_sounds
    t.fall_sounds = ['voicelines/noob/fall']
    t.style = 'bones'
    t.default_color = (0.1, 0.1, 1)
    t.default_highlight = (0.2, 0.2, 1)

    # that fucking ninja that i hate ##########################################
    t = Appearance('GummyBoiYT')
    t.color_texture = 'snakeyColor'
    t.color_mask_texture = 'snakeyColorMask'
    t.icon_texture = 'snakeyIcon'
    t.earthportrait = 'earthbound/snakebound'
    t.EBwin = 'earthbound/snakebound_win'
    t.EBlose = 'earthbound/snakebound_lose'
    t.icon_mask_texture = 'snakeyIconCM'
    t.head_mesh = 'snakeyHead'
    t.torso_mesh = 'snakeyTorso'
    t.pelvis_mesh = 'snakeyPelvis'
    t.upper_arm_mesh = 'snakeyUpperArm'
    t.forearm_mesh = 'snakeyForeArm'
    t.hand_mesh = 'snakeyHand'
    t.upper_leg_mesh = 'snakeyUpperLeg'
    t.lower_leg_mesh = 'snakeyLowerLeg'
    t.toes_mesh = 'snakeyToes'
    t.jump_sounds = ['voicelines/snakey/attack' + str(i + 1) + '' for i in range(7)]
    t.attack_sounds = ['voicelines/snakey/attack' + str(i + 1) + '' for i in range(7)]
    t.impact_sounds = ['voicelines/snakey/hurt' + str(i + 1) + '' for i in range(8)]
    t.death_sounds = ['voicelines/snakey/death']
    t.pickup_sounds = ['voicelines/snakey/attack' + str(i + 1) + '' for i in range(7)]
    t.fall_sounds = ['voicelines/snakey/fall' + str(i + 1) + '' for i in range(2)]
    t.gloat_sounds = ['voicelines/snakey/gloat']
    t.victory_sounds = ['voicelines/snakey/win']
    t.style = 'agent'
    t.default_color = (0.2, 1, 1)
    t.default_highlight = (1, 1, 1)

    # barney wannabe #####################################
    t = Appearance('Susie')
    t.color_texture = 'susieColor'
    t.color_mask_texture = 'susieColorMask'
    t.icon_texture = 'susieIcon'
    t.earthportrait = 'earthbound/susiebound'
    t.EBwin = 'earthbound/susiebound_win'
    t.EBlose = 'earthbound/susiebound_lose'
    t.icon_mask_texture = 'susieIconCM'
    t.head_mesh = 'susieHead'
    t.torso_mesh = 'susieTorso'
    t.pelvis_mesh = 'susiePelvis'
    t.upper_arm_mesh = 'susieUpperArm'
    t.forearm_mesh = 'susieForeArm'
    t.hand_mesh = 'susieHand'
    t.upper_leg_mesh = 'susieUpperLeg'
    t.lower_leg_mesh = 'susieLowerLeg'
    t.toes_mesh = 'susieToes'
    t.jump_sounds = ['voicelines/susie/jump' + str(i + 1) + '' for i in range(4)]
    t.attack_sounds = ['voicelines/susie/attack' + str(i + 1) + '' for i in range(4)]
    t.victory_sounds = ['voicelines/susie/win']
    t.gloat_sounds = ['voicelines/susie/gloat']
    t.impact_sounds = ['voicelines/susie/hurt' + str(i + 1) + '' for i in range(2)]
    t.death_sounds = ['voicelines/susie/death']
    t.pickup_sounds = ['voicelines/susie/attack' + str(i + 1) + '' for i in range(4)]
    t.fall_sounds = ['voicelines/susie/fall']
    t.style = 'agent'
    t.default_color = (0.9725490196078431, 0.5137254901960784, 0.8431372549019608)
    t.default_highlight = (0.5333333333333333, 0.09019607843137255, 0.41568627450980394)

    # fatass ###########################################
    # thank you lemon for this incredible voice acting #
    t = Appearance('Mell')
    t.color_texture = 'mellColor'
    t.color_mask_texture = 'mellColorMask'
    t.icon_texture = 'mellIcon'
    t.earthportrait = 'earthbound/mellbound'
    t.EBlose = 'earthbound/mellbound_lose'
    t.EBwin = 'earthbound/mellbound_win'
    t.icon_mask_texture = 'mellIconCM'
    t.head_mesh = 'mellHead'
    t.torso_mesh = 'mellTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'mellUpperArm'
    t.forearm_mesh = 'mellForeArm'
    t.hand_mesh = 'mellHand'
    t.upper_leg_mesh = 'mellUpperLeg'
    t.lower_leg_mesh = 'mellLowerLeg'
    t.toes_mesh = 'mellToes'
    mell_sounds = ['voicelines/mell/sound' + str(i + 1) + '' for i in range(7)]
    t.jump_sounds = mell_sounds
    t.attack_sounds = mell_sounds
    t.impact_sounds = mell_sounds
    t.death_sounds = ['voicelines/mell/death']
    t.victory_sounds = mell_sounds
    t.gloat_sounds = ['voicelines/mell/gloat']
    t.pickup_sounds = mell_sounds
    t.fall_sounds = ['voicelines/mell/fall' + str(i + 1) + '' for i in range(2)]
    t.style = 'ali'
    t.default_color = (1, 1, 1)
    t.default_highlight = (0, 1, 0)

    # Noob #######################################
    t = Appearance('Noob')
    t.color_texture = 'noobColor'
    t.color_mask_texture = 'noobColorMask'
    t.icon_texture = 'noobIcon'
    t.earthportrait = 'earthbound/noobbound'
    t.EBlose = 'earthbound/noobbound_lose'
    t.EBwin = 'earthbound/noobbound_win'
    t.icon_mask_texture = 'noobIconColorMask'
    t.head_mesh = 'noobHead'
    t.torso_mesh = 'noobTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'noobUpperArm'
    t.forearm_mesh = 'none'
    t.hand_mesh = 'none'
    t.upper_leg_mesh = 'noobUpperLeg'
    t.lower_leg_mesh = 'none'
    t.toes_mesh = 'none'
    noob_sounds = ['voicelines/noob/sound' + str(i + 1) + '' for i in range(6)]
    t.jump_sounds = noob_sounds
    t.attack_sounds = noob_sounds
    t.impact_sounds = ['voicelines/noob/hurt' + str(i + 1) + '' for i in range(7)]
    t.death_sounds = ['voicelines/noob/death']
    t.pickup_sounds = noob_sounds
    t.fall_sounds = ['voicelines/noob/fall']
    t.style = 'bones'
    t.default_color = (1.0, 0.99, 0.13999999999999968)
    t.default_highlight = (0.30999999999999994, 0.4599999999999999, 1)

    # wait this isnt noob holy shit hes back #######################################
    t = Appearance('John Grace')
    t.color_texture = 'graceColor'
    t.color_mask_texture = 'graceColorMask'
    t.icon_texture = 'graceIcon'
    t.earthportrait = 'earthbound/gracebound'
    t.EBlose = 'earthbound/gracebound_lose'
    t.EBwin = 'earthbound/gracebound_win'
    t.icon_mask_texture = 'graceIconCM'
    t.head_mesh = 'graceHead'
    t.torso_mesh = 'graceTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'noobUpperArm'
    t.forearm_mesh = 'none'
    t.hand_mesh = 'none'
    t.upper_leg_mesh = 'graceUpperLeg'
    t.lower_leg_mesh = 'none'
    t.toes_mesh = 'none'
    t.jump_sounds = ['voicelines/link/jump' + str(i + 1) + '' for i in range(6)]
    t.attack_sounds = ['voicelines/link/attack' + str(i + 1) + '' for i in range(6)]
    t.pickup_sounds = ['voicelines/link/pickup']
    t.impact_sounds = ['voicelines/link/hurt' + str(i + 1) + '' for i in range(8)]
    t.death_sounds = ['voicelines/link/death']
    t.fall_sounds = ['voicelines/link/fall']
    t.victory_sounds = ['voicelines/link/win']
    t.gloat_sounds = ['voicelines/link/gloat']
    t.style = 'bones'
    t.default_color = (0, 0, 0)
    t.default_highlight = (1.2, 1.2, 1.2)  

    # I will swallow you and spit you out at other enemies. ######################################
    t = Appearance('Kirby')
    t.color_texture = 'kirbyColor'
    t.color_mask_texture = 'kirbyColorMask'
    t.icon_texture = 'kirbyIcon'
    t.icon_mask_texture = 'kirbyIconCM'
    t.earthportrait = 'earthbound/kirbybound'
    t.EBlose = 'earthbound/kirbybound_lose'
    t.EBwin = 'earthbound/kirbybound_win'
    t.head_mesh = 'none'
    t.torso_mesh = 'kirbyTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'none'
    t.forearm_mesh = 'none'
    t.hand_mesh = 'kirbyHand'
    t.upper_leg_mesh = 'none'
    t.lower_leg_mesh = 'kirbyLowerLeg'
    t.toes_mesh = 'none'
    t.jump_sounds = ['voicelines/kirby/jump' + str(i + 1) + '' for i in range(3)]
    kirbyattack = ['voicelines/kirby/attack' + str(i + 1) + '' for i in range(4)]
    t.attack_sounds = kirbyattack
    t.pickup_sounds = kirbyattack
    t.impact_sounds = ['voicelines/kirby/hurt' + str(i + 1) + '' for i in range(6)]
    t.death_sounds = ['voicelines/kirby/death']
    t.fall_sounds = ['voicelines/kirby/fall' + str(i + 1) + '' for i in range(2)]
    t.victory_sounds = ['voicelines/kirby/win' + str(i + 1) + '' for i in range(4)]
    t.gloat_sounds = ['voicelines/kirby/gloat' + str(i + 1) + '' for i in range(6)]
    t.style = 'agent'
    t.default_color = (0.9, 0.35, 0.9)
    t.default_highlight = (1, 0.1, 0.1)
    
    # tubby plumber man ######################################
    t = Appearance('SM64 Mario')
    t.color_texture = 'marioColor'
    t.color_mask_texture = 'marioColorMask'
    t.icon_texture = 'marioIcon'
    t.icon_mask_texture = 'marioIconCM'
    t.earthportrait = 'earthbound/mariobound'
    t.head_mesh = 'santaHead'
    t.torso_mesh = 'santaTorso'
    t.pelvis_mesh = 'santaPelvis'
    t.upper_arm_mesh = 'santaUpperArm'
    t.forearm_mesh = 'santaForeArm'
    t.hand_mesh = 'santaHand'
    t.upper_leg_mesh = 'santaUpperLeg'
    t.lower_leg_mesh = 'santaLowerLeg'
    t.toes_mesh = 'santaToes'
    t.jump_sounds = ['voicelines/mario64/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/mario64/attack' + str(i + 1) + '' for i in range(3)]
    t.impact_sounds = ['voicelines/mario64/hurt' + str(i + 1) + '' for i in range(3)]
    t.death_sounds = ['voicelines/mario64/death']
    t.pickup_sounds = ['voicelines/mario64/pickup']
    t.fall_sounds = ['voicelines/mario64/fall']
    t.victory_sounds = ['voicelines/mario64/win']
    t.gloat_sounds = ['voicelines/mario64/gloat']
    t.ffire_sounds = ['voicelines/mario64/ffire']
    t.teamkill_sounds = ['voicelines/mario64/teamkill']
    t.style = 'bones'
    t.default_color = (1, 0, 0)
    t.default_highlight = (0.1, 0.1, 1)
    t.super_music = bs.MusicType.RAINBOW_ROAD

    # that one character from the asym they canceled because why not ######################################
    t = Appearance('Sonic')
    t.color_texture = 'sonicColor'
    t.color_mask_texture = 'sonicColorMask'
    t.icon_texture = 'sonicIcon'
    t.icon_mask_texture = 'sonicIconCM'
    t.earthportrait = 'earthbound/sonicbound'
    t.head_mesh = 'sonicHead'
    t.torso_mesh = 'sonicTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'sonicUpperArm'
    t.forearm_mesh = 'sonicForeArm'
    t.hand_mesh = 'sonicHand'
    t.upper_leg_mesh = 'sonicUpperLeg'
    t.lower_leg_mesh = 'sonicLowerLeg'
    t.toes_mesh = 'none'
    t.jump_sounds = ['voicelines/sonic/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/sonic/attack' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/sonic/hit' + str(i + 1) + '' for i in range(5)]
    t.death_sounds = ['voicelines/sonic/death']
    t.pickup_sounds = ['voicelines/sonic/attack' + str(i + 1) + '' for i in range(4)]
    t.fall_sounds = ['voicelines/sonic/fall']
    t.victory_sounds = ['voicelines/sonic/win']
    t.gloat_sounds = ['voicelines/sonic/gloat']
    t.style = 'agent'
    t.default_color = (0.2, 0.2, 0.9)
    t.default_highlight = (1, 0.1, 0.1)

    # colas del fox ######################################
    t = Appearance('Tails')
    t.color_texture = 'tailsColor'
    t.color_mask_texture = 'tailsColorMask'
    t.icon_texture = 'tailsIcon'
    t.icon_mask_texture = 'tailsIconCM'
    t.earthportrait = 'earthbound/tailsbound'
    t.head_mesh = 'tailsHead'
    t.torso_mesh = 'tailsTorso'
    t.pelvis_mesh = 'tailsPelvis'
    t.upper_arm_mesh = 'tailsUpperArm'
    t.forearm_mesh = 'tailsForeArm'
    t.hand_mesh = 'tailsHand'
    t.upper_leg_mesh = 'tailsUpperLeg'
    t.lower_leg_mesh = 'tailsLowerLeg'
    t.toes_mesh = 'tailsToes'
    t.jump_sounds = ['voicelines/sonic/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/sonic/attack' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/sonic/hit' + str(i + 1) + '' for i in range(5)]
    t.death_sounds = ['voicelines/sonic/death']
    t.pickup_sounds = ['voicelines/sonic/attack' + str(i + 1) + '' for i in range(4)]
    t.fall_sounds = ['voicelines/sonic/fall']
    t.victory_sounds = ['voicelines/sonic/win']
    t.gloat_sounds = ['voicelines/sonic/gloat']
    t.style = 'agent'
    t.default_color = (1, 0.6, 0)
    t.default_highlight = (1, 0.1, 0.1)

    # Rayman! ################################
    t = Appearance('Rayman')
    t.color_texture = 'raymanColor'
    t.color_mask_texture = 'raymanColorMask'
    t.icon_texture = 'raymanIcon'
    t.earthportrait = 'earthbound/raybound'
    t.EBlose = 'earthbound/raybound_lose'
    t.EBwin = 'earthbound/raybound_win'
    t.icon_mask_texture = 'raymanIconColorMask'
    t.head_mesh = 'raymanHead'
    t.torso_mesh = 'raymanTorso'
    t.pelvis_mesh = 'raymanPelvis'
    t.upper_arm_mesh = 'raymanUpperArm'
    t.forearm_mesh = 'raymanForeArm'
    t.hand_mesh = 'raymanHand'
    t.upper_leg_mesh = 'raymanUpperLeg'
    t.lower_leg_mesh = 'raymanLowerLeg'
    t.toes_mesh = 'raymanToes'
    t.jump_sounds = ['voicelines/rayman/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/rayman/attack' + str(i + 1) + '' for i in range(2)]
    t.impact_sounds = ['voicelines/rayman/hurt' + str(i + 1) + '' for i in range(3)]
    t.victory_sounds = ['voicelines/rayman/win']
    t.death_sounds = ['voicelines/rayman/death']
    t.pickup_sounds = ['voicelines/rayman/attack' + str(i + 1) + '' for i in range(2)]
    t.fall_sounds = ['voicelines/rayman/fall']
    t.style = 'bones'
    t.default_color = (0.5, 0.25, 1.0)
    t.default_highlight = (1.0, 0.15, 0.15)

    # Shooowwwtime!! ###################################
    t = Appearance('Bowser')
    t.color_texture = 'bowserColor'
    t.color_mask_texture = 'bowserColorMask'
    t.icon_texture = 'bowserIcon'
    t.earthportrait = 'earthbound/bowserbound'
    t.EBwin = 'earthbound/bowserbound'
    t.EBlose = 'earthbound/bowserbound_lose'
    t.icon_mask_texture = 'bowserIconColorMask'
    t.head_mesh = 'bowserHead'
    t.torso_mesh = 'bowserTorso'
    t.pelvis_mesh = 'bowserPelvis'
    t.upper_arm_mesh = 'bowserUpperArm'
    t.forearm_mesh = 'bowserForeArm'
    t.hand_mesh = 'bowserHand'
    t.upper_leg_mesh = 'bowserUpperLeg'
    t.lower_leg_mesh = 'bowserLowerLeg'
    t.toes_mesh = 'bowserToes'
    bowser_sounds = ['voicelines/bowser/sound' + str(i + 1) + '' for i in range(4)]
    bowser_hit_sounds = ['voicelines/bowser/hurt' + str(i + 1) + '' for i in range(2)]
    t.jump_sounds = bowser_sounds
    t.attack_sounds = bowser_sounds
    t.pickup_sounds = bowser_sounds
    t.impact_sounds = bowser_hit_sounds
    t.death_sounds = ['voicelines/bowser/death']
    t.victory_sounds = ['voicelines/bowser/win']
    t.gloat_sounds = ['voicelines/bowser/gloat']
    t.fall_sounds = ['voicelines/bowser/fall']
    t.style = 'ali'
    t.default_color = (
        0.996078431372549, 
        0.8372549019607842, 
        0.022745098039215678
    )
    t.default_highlight = (
        0.0, 
        0.5686274509803921, 
        0.22745098039215686
    )

    # Ali ###################################
    t = Appearance('Taobao Mascot')
    t.color_texture = 'aliColor'
    t.color_mask_texture = 'aliColorMask'
    t.icon_texture = 'aliIcon'
    t.icon_mask_texture = 'aliIconColorMask'
    t.head_mesh = 'aliHead'
    t.torso_mesh = 'aliTorso'
    t.pelvis_mesh = 'aliPelvis'
    t.upper_arm_mesh = 'aliUpperArm'
    t.forearm_mesh = 'aliForeArm'
    t.hand_mesh = 'aliHand'
    t.upper_leg_mesh = 'aliUpperLeg'
    t.lower_leg_mesh = 'aliLowerLeg'
    t.toes_mesh = 'aliToes'
    ali_sounds = ['ali1', 'ali2', 'ali3', 'ali4']
    ali_hit_sounds = ['aliHit1', 'aliHit2']
    t.jump_sounds = ali_sounds
    t.attack_sounds = ali_sounds
    t.impact_sounds = ali_hit_sounds
    t.death_sounds = ['aliDeath']
    t.pickup_sounds = ali_sounds
    t.fall_sounds = ['aliFall']
    t.style = 'ali'
    t.default_color = (1, 0.5, 0)
    t.default_highlight = (1, 1, 1)

    # knite. ###################################
    t = Appearance('Roaring Knight')
    t.color_texture = 'knightColor'
    t.color_mask_texture = 'knightColorMask'
    t.icon_texture = 'knightIcon'
    t.earthportrait = 'earthbound/knightbound'
    t.EBlose = 'earthbound/knightbound_lose'
    t.EBwin = 'earthbound/knightbound_win'
    t.icon_mask_texture = 'knightIconCM'
    t.head_mesh = 'knightHead'
    t.torso_mesh = 'knightTorso'
    t.pelvis_mesh = 'knightPelvis'
    t.upper_arm_mesh = 'knightUpperArm'
    t.forearm_mesh = 'knightForeArm'
    t.hand_mesh = 'knightHand'
    t.upper_leg_mesh = 'knightUpperLeg'
    t.lower_leg_mesh = 'knightLowerLeg'
    t.toes_mesh = 'knightToes'
    knightsounds = ['voicelines/knight/sound' + str(i + 1) + '' for i in range(4)]
    t.jump_sounds = knightsounds
    t.attack_sounds = knightsounds
    t.impact_sounds = ['voicelines/knight/hurt' + str(i + 1) + '' for i in range(2)]
    t.death_sounds = ['voicelines/knight/death']
    t.pickup_sounds = knightsounds
    t.victory_sounds = ['voicelines/knight/win']
    t.gloat_sounds = ['voicelines/knight/gloat']
    t.fall_sounds = ['voicelines/knight/fall']
    t.style = 'agent'
    t.default_color = (0.0, 0.0, 0.0)
    t.default_highlight = (1, 1, 1)
    t.super_color = [(1, 1, 1), (0, 0, 0)]
    t.super_highlight = [
        mell.hex_to_color('4a6ce8'), 
        mell.hex_to_color('080afb')
    ]
    t.super_music = bs.MusicType.KAIZOKNIGHT

    # Noise Noise Noise Noise NOise ###################################
    t = Appearance('The Noise')
    t.color_texture = 'noiseColor'
    t.color_mask_texture = 'noiseColorMask'
    t.icon_texture = 'noiseIcon'
    t.earthportrait = 'earthbound/noisebound'
    t.EBlose = 'earthbound/noisebound_lose'
    t.EBwin = 'earthbound/noisebound_win'
    t.icon_mask_texture = 'noiseIconCM'
    t.head_mesh = 'noiseHead'
    t.torso_mesh = 'noiseTorso'
    t.pelvis_mesh = 'noisePelvis'
    t.upper_arm_mesh = 'noiseUpperArm'
    t.forearm_mesh = 'noiseForeArm'
    t.hand_mesh = 'noiseHand'
    t.upper_leg_mesh = 'noiseUpperLeg'
    t.lower_leg_mesh = 'noiseLowerLeg'
    t.toes_mesh = 'noiseToes'
    noise_sounds = ['voicelines/noise/sound' + str(i + 1) + '' for i in range(4)]
    noise_hit_sounds = ['voicelines/noise/hit' + str(i + 1) + '' for i in range(2)]
    t.jump_sounds = noise_sounds
    t.attack_sounds = noise_sounds
    t.impact_sounds = noise_hit_sounds
    t.death_sounds = ['voicelines/noise/death']
    t.pickup_sounds = noise_sounds
    t.victory_sounds = ['voicelines/noise/sound1']
    t.gloat_sounds = ['voicelines/noise/gloat']
    t.fall_sounds = ['voicelines/noise/fall']
    t.style = 'agent'
    t.default_color = (
        0.9725490196078431,
        0.8784313725490196,
        0.5019607843137255
    )
    t.default_highlight = (
        0.8470588235294118,
        0.5333333333333333,
        0.09411764705882353
    )
    t.super_music = bs.MusicType.NOISESUPER
    
    # homero doh homero cerveza ###################################
    t = Appearance('Homer')
    t.color_texture = 'theSimpsonColor'
    t.color_mask_texture = 'theSimpsonColorMask'
    t.icon_texture = 'tsHomerIconColor'
    t.icon_mask_texture = 'tsHomerIconColorMask'
    t.earthportrait = 'earthbound/homerbound'
    t.EBlose = 'earthbound/homerbound_lose'
    t.EBwin = 'earthbound/homerbound_win'
    t.head_mesh = 'tsHomerHead'
    t.torso_mesh = 'tsHomerTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'tsHomerUpperArm'
    t.forearm_mesh = 'tsHomerForeArm'
    t.hand_mesh = 'tsHomerHand'
    t.upper_leg_mesh = 'tsHomerUpperLeg'
    t.lower_leg_mesh = 'tsHomerLowerLeg'
    t.toes_mesh = 'tsHomerToes'
    homersounds = ['voicelines/homer/sound' + str(i + 1) + '' for i in range(2)]
    homerhurtsfx = ['voicelines/homer/hit' + str(i + 1) + '' for i in range(3)]
    t.jump_sounds = homersounds
    t.attack_sounds = homersounds
    t.impact_sounds = homerhurtsfx
    t.death_sounds = ['voicelines/homer/death']
    t.pickup_sounds = ['voicelines/homer/pickup']
    t.victory_sounds = ['voicelines/homer/sound3']
    t.gloat_sounds = ['voicelines/homer/fall']
    t.fall_sounds = ['voicelines/homer/fall']
    t.style = 'agent'
    t.default_color = (1, 1, 1)
    t.default_highlight = (0, 0.4, 1)

    # orange guy with the cap... like some kinda buddy... ###################################
    t = Appearance('Orangecap')
    t.color_texture = 'ocapColor'
    t.color_mask_texture = 'ocapColorMask'
    t.icon_texture = 'ocapIcon'
    t.earthportrait = 'earthbound/capbound'
    t.EBlose = 'earthbound/capbound_lose'
    t.EBwin = 'earthbound/capbound_win'
    t.icon_mask_texture = 'ocapIconCM'
    t.head_mesh = 'ocapHead'
    t.torso_mesh = 'ocapTorso'
    t.pelvis_mesh = 'ocapPelvis'
    t.upper_arm_mesh = 'ocapUpperArm'
    t.forearm_mesh = 'ocapForeArm'
    t.hand_mesh = 'ocapHand'
    t.upper_leg_mesh = 'ocapUpperLeg'
    t.lower_leg_mesh = 'ocapLowerLeg'
    t.toes_mesh = 'ocapToes'
    t.jump_sounds = ['voicelines/ocap/jump' + str(i + 1) + '' for i in range(4)]
    t.attack_sounds = ['voicelines/ocap/punch' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/ocap/hurt1']
    t.death_sounds = ['voicelines/ocap/death' + str(i + 1) + '' for i in range(2)]
    t.pickup_sounds = ['voicelines/ocap/pickup' + str(i + 1) + '' for i in range(4)]
    t.fall_sounds = ['voicelines/ocap/fall' + str(i + 1) + '' for i in range(3)]
    t.style = 'agent'
    t.default_color = (0.87, 0.44, 0.15)
    t.default_highlight = (0.46, 0.26, 0.54)
    
    # now here's the real buddy ###################################
    t = Appearance('Buddie')
    t.color_texture = 'buddieColor'
    t.color_mask_texture = 'buddieColorMask'
    t.icon_texture = 'buddieIcon'
    t.earthportrait = 'earthbound/budbound'
    t.EBlose = 'earthbound/budbound_lose'
    t.EBwin = 'earthbound/budbound_win'
    t.icon_mask_texture = 'buddieIconCM'
    t.head_mesh = 'buddieHead'
    t.torso_mesh = 'buddieTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'buddieUpperArm'
    t.forearm_mesh = 'buddieForeArm'
    t.hand_mesh = 'buddieHand'
    t.upper_leg_mesh = 'buddieUpperLeg'
    t.lower_leg_mesh = 'buddieLowerLeg'
    t.toes_mesh = 'buddieToes'
    t.jump_sounds = ['voicelines/buddie/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/buddie/punch' + str(i + 1) + '' for i in range(2)]
    t.impact_sounds = ['voicelines/buddie/hurt' + str(i + 1) + '' for i in range(5)]
    t.death_sounds = ['voicelines/buddie/death' + str(i + 1) + '' for i in range(4)]
    t.pickup_sounds = ['voicelines/buddie/pickup' + str(i + 1) + '' for i in range(4)]
    t.fall_sounds = ['voicelines/buddie/fall' + str(i + 1) + '' for i in range(3)]
    t.victory_sounds = t.jump_sounds
    t.style = 'bones'
    t.default_color = (251 / 255, 242 / 255, 51 / 255)
    t.default_highlight = (43 / 255, 41 / 255, 65 / 255)
    
    # buddie's Buddy ###################################
    t = Appearance('Rem')
    t.color_texture = 'remColor'
    t.color_mask_texture = 'remColorMask'
    t.earthportrait = 'earthbound/rembound'
    t.EBlose = 'earthbound/rembound_lose'
    t.EBwin = 'earthbound/rembound_win'
    t.icon_texture = 'remIcon'
    t.icon_mask_texture = 'remIconCM'
    t.head_mesh = 'remHead'
    t.torso_mesh = 'remTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'remUpperArm'
    t.forearm_mesh = 'remForeArm'
    t.hand_mesh = 'remHand'
    t.upper_leg_mesh = 'remUpperLeg'
    t.lower_leg_mesh = 'remLowerLeg'
    t.toes_mesh = 'remToes'
    t.jump_sounds = ['voicelines/rem/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/rem/attack' + str(i + 1) + '' for i in range(3)]
    t.impact_sounds = ['voicelines/rem/hurt' + str(i + 1) + '' for i in range(3)]
    t.death_sounds = ['voicelines/rem/death']
    t.pickup_sounds = t.attack_sounds
    t.fall_sounds = ['voicelines/rem/fall']
    t.victory_sounds = ['voicelines/rem/win']
    t.gloat_sounds = ['voicelines/rem/gloat']
    t.style = 'bones'
    t.default_color = (232 / 255, 17 / 255, 17 / 255)
    t.default_highlight = (240 / 255, 14 / 255, 14 / 255)
    
    # object show reference, but also like not ###################################
    t = Appearance('Sparkii')
    t.color_texture = 'sparkiiColor'
    t.color_mask_texture = 'sparkiiColorMask'
    t.icon_texture = 'sparkiiIcon'
    t.icon_mask_texture = 'sparkiiIconCM'
    t.head_mesh = 'sparkiiHead'
    t.torso_mesh = 'sparkiiTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'sparkiiUpperArm'
    t.forearm_mesh = 'sparkiiForeArm'
    t.hand_mesh = 'sparkiiHand'
    t.upper_leg_mesh = 'sparkiiUpperLeg'
    t.lower_leg_mesh = 'sparkiiLowerLeg'
    t.toes_mesh = 'sparkiiToes'
    t.jump_sounds = ['voicelines/toad/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/toad/attack' + str(i + 1) + '' for i in range(3)]
    t.impact_sounds = ['voicelines/toad/hurt' + str(i + 1) + '' for i in range(3)]
    t.death_sounds = ['voicelines/toad/death']
    t.pickup_sounds = ['voicelines/toad/pickup']
    t.fall_sounds = ['voicelines/toad/fall']
    t.victory_sounds = ['voicelines/toad/win']
    t.gloat_sounds = ['voicelines/toad/gloat']
    t.style = 'bones'
    t.general_style = 'robot'
    t.default_color = mell.hex_to_color('2a3ba4')
    t.default_highlight = mell.hex_to_color('c6a598')
    
    # ow! ###################################
    t = Appearance('Fancy Pants')
    t.color_texture = 'fancyColor'
    t.color_mask_texture = 'fancyColorMask'
    t.icon_texture = 'fancyIcon'
    t.icon_mask_texture = 'fancyIconCM'
    t.earthportrait = 'earthbound/fancybound'
    t.EBlose = 'earthbound/fancybound_lose'
    t.EBwin = 'earthbound/fancybound_win'
    t.head_mesh = 'fancyHead'
    t.torso_mesh = 'fancyTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'fancyUpperArm'
    t.forearm_mesh = 'fancyForeArm'
    t.hand_mesh = 'fancyHand'
    t.upper_leg_mesh = 'fancyUpperLeg'
    t.lower_leg_mesh = 'fancyLowerLeg'
    t.toes_mesh = 'fancyToes'
    t.jump_sounds = ['voicelines/fancy/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/fancy/attack' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/fancy/hurt']
    t.death_sounds = ['voicelines/fancy/death']
    t.pickup_sounds = t.attack_sounds
    t.fall_sounds = ['voicelines/fancy/fall']
    t.victory_sounds = ['voicelines/fancy/win']
    t.style = 'bones'
    t.general_style = 'fancy'
    t.default_color = mell.hex_to_color('f89a04')
    t.default_highlight = (0, 0, 0)

    # Isaac of the Binding ###################################
    t = Appearance('Isaac')
    t.color_texture = 'isaacColor'
    t.color_mask_texture = 'isaacColorMask'
    t.icon_texture = 'isaacIcon'
    t.earthportrait = 'earthbound/isaacbound'
    t.EBlose = 'earthbound/isaacbound_lose'
    t.EBwin = 'earthbound/isaacbound_win'
    t.icon_mask_texture = 'isaacIconCM'
    t.head_mesh = 'isaacHead'
    t.torso_mesh = 'isaacTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'isaacUpperArm'
    t.forearm_mesh = 'isaacForeArm'
    t.hand_mesh = 'isaacHand'
    t.upper_leg_mesh = 'isaacUpperLeg'
    t.lower_leg_mesh = 'isaacLowerLeg'
    t.toes_mesh = 'isaacToes'
    t.impact_sounds = ['voicelines/isaac/hurt' + str(i + 1) + '' for i in range(3)]
    t.death_sounds = ['voicelines/isaac/death']
    t.fall_sounds = ['voicelines/isaac/fall']
    t.victory_sounds = ['voicelines/isaac/win']
    t.gloat_sounds = ['voicelines/isaac/win']
    t.style = 'ali'
    t.is_gimmick_character = True
    t.default_color = mell.hex_to_color('ffdcda')
    t.default_highlight = mell.hex_to_color('7cf4ff')

    # The Original      Spaz ###################################
    t = Appearance('OG Spaz')
    t.color_texture = 'spazColor'
    t.color_mask_texture = 'spazColorMask'
    t.icon_texture = 'spazIcon'
    t.icon_mask_texture = 'spazIconCM'
    t.head_mesh = 'spazHead'
    t.torso_mesh = 'spazTorso'
    t.pelvis_mesh = 'spazPelvis'
    t.upper_arm_mesh = 'spazUpperArm'
    t.forearm_mesh = 'spazForeArm'
    t.hand_mesh = 'spazHand'
    t.upper_leg_mesh = 'spazUpperLeg'
    t.lower_leg_mesh = 'spazLowerLeg'
    t.toes_mesh = 'spazToes'
    t.jump_sounds = ['spazJump01', 'spazJump02', 'spazJump03', 'spazJump04']
    t.attack_sounds = [
        'spazAttack01',
        'spazAttack02',
        'spazAttack03',
        'spazAttack04',
    ]
    t.impact_sounds = [
        'spazImpact01',
        'spazImpact02',
        'spazImpact03',
        'spazImpact04',
    ]
    t.death_sounds = ['spazDeath01']
    t.pickup_sounds = ['spazPickup01']
    t.fall_sounds = ['spazFall01']
    t.style = 'spaz'
    t.victory_sounds = ['spazJump01']

    # wait this is a ACTUAL entity! why is this here! ###################################
    t = Appearance('RueEntityDataLmfao')
    t.hidden = True
    t.color_texture = 'rueColor'
    t.color_mask_texture = 'white'
    t.torso_mesh = 'rue'
    
    
    # ---------------------------- SKINS --------------------------------------------
    
    # The Original      Spaz ###################################
    t = Appearance('OGSpazMetal')
    # skin name is a simple, neutral version of
    # the skin's name, so in this case 'Metal OG Spaz' (metal skin for og spaz)
    # would just be called Metal, or something of the sorts.
    t.skin_name = 'Metal'
    # ALWAYS set a skin as hidden.
    t.hidden = True
    t.color_texture = 'metalSpazColor'
    t.color_mask_texture = 'metalSpazCM'
    t.icon_texture = 'spazIcon'
    t.icon_mask_texture = 'spazIconCM'
    t.head_mesh = 'spazHead'
    t.torso_mesh = 'spazTorso'
    t.pelvis_mesh = 'spazPelvis'
    t.upper_arm_mesh = 'spazUpperArm'
    t.forearm_mesh = 'spazForeArm'
    t.hand_mesh = 'spazHand'
    t.upper_leg_mesh = 'spazUpperLeg'
    t.lower_leg_mesh = 'spazLowerLeg'
    t.toes_mesh = 'spazToes'
    t.jump_sounds = ['spazJump01', 'spazJump02', 'spazJump03', 'spazJump04']
    t.attack_sounds = [
        'spazAttack01',
        'spazAttack02',
        'spazAttack03',
        'spazAttack04',
    ]
    t.impact_sounds = [
        'spazImpact01',
        'spazImpact02',
        'spazImpact03',
        'spazImpact04',
    ]
    t.death_sounds = ['spazDeath01']
    t.pickup_sounds = ['spazPickup01']
    t.fall_sounds = ['spazFall01']
    t.style = 'cyborg'
    t.general_style = 'metallic'
    t.victory_sounds = ['spazJump01']
    
    # spazling #######################################
    t = Appearance('SMB1Spaz')
    t.skin_name = 'SMB1'
    t.hidden = True
    t.color_texture = 'retroSpazColor'
    t.color_mask_texture = 'retroSpazColorMask'
    t.icon_texture = 'spazlingIcon'
    t.icon_mask_texture = 'spazlingIconCM'    
    t.earthportrait = 'earthbound/spazbound'
    t.EBwin = 'earthbound/spazbound_win'
    t.EBlose = 'earthbound/spazbound_lose'
    t.head_mesh = 'retroSpazHead'
    t.torso_mesh = 'retroSpazTorso'
    t.pelvis_mesh = 'retroSpazPelvis'
    t.upper_arm_mesh = 'retroSpazUpperArm'
    t.forearm_mesh = 'retroSpazForeArm'
    t.hand_mesh = 'retroSpazHand'
    t.upper_leg_mesh = 'retroSpazUpperLeg'
    t.lower_leg_mesh = 'retroSpazLowerLeg'
    t.toes_mesh = 'retroSpazToes'
    t.jump_sounds = ['voicelines/spaz/jump0' + str(i + 1) + '' for i in range(4)]
    t.attack_sounds = ['voicelines/spaz/attack0' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/spaz/hurt0' + str(i + 1) + '' for i in range(4)]
    t.death_sounds = ['voicelines/spaz/death0' + str(i + 1) + '' for i in range(4)]
    t.pickup_sounds = ['voicelines/spaz/pickup']
    t.victory_sounds = ['voicelines/spaz/win']
    t.gloat_sounds = ['voicelines/spaz/gloat']
    t.fall_sounds = ['voicelines/spaz/fall0' + str(i + 1) + '' for i in range(4)]
    t.style = 'agent'
