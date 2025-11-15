# Released under the MIT License. See LICENSE for details.
#
"""Appearance functionality for spazzes."""
from __future__ import annotations

import bascenev1 as bs
import babase as ba


def get_appearances(include_locked: bool = False) -> list[str]:
    """Get the list of available spaz appearances."""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    plus = bs.app.plus
    assert plus is not None

    assert bs.app.classic is not None
    get_purchased = plus.get_v1_account_product_purchased
    disallowed = []
    if not include_locked:
        # alternative to updating modpack since it willt ake too long
        if not get_purchased('characters.santa'):
            disallowed.append('Santa Claus')
        if not ba.app.config.get("unlockedmel", True):
            disallowed.append('Mel')
            
    return [
        s
        for s in list(bs.app.classic.spaz_appearances.keys())
        if s not in disallowed
    ]


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
        self.color_texture = ''
        self.color_mask_texture = ''
        self.icon_texture = ''
        self.earthportrait = ''
        self.icon_mask_texture = ''
        self.head_mesh = ''
        self.torso_mesh = ''
        self.pelvis_mesh = ''
        self.upper_arm_mesh = ''
        self.forearm_mesh = ''
        self.hand_mesh = ''
        self.upper_leg_mesh = ''
        self.lower_leg_mesh = ''
        self.toes_mesh = ''
        self.jump_sounds: list[str] = []
        self.attack_sounds: list[str] = []
        self.impact_sounds: list[str] = []
        self.death_sounds: list[str] = []
        self.pickup_sounds: list[str] = []
        self.victory_sounds: list[str] = []
        self.fall_sounds: list[str] = []
        self.style = 'spaz'
        self.default_color: tuple[float, float, float] | None = None
        self.default_highlight: tuple[float, float, float] | None = None


def register_appearances() -> None:
    """Register our builtin spaz appearances."""

    # This is quite ugly but will be going away so not worth cleaning up.
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    # spazinga #######################################
    t = Appearance('Spaz')
    t.color_texture = 'neoSpazColor'
    t.color_mask_texture = 'neoSpazColorMask'
    t.icon_texture = 'neoSpazIcon'
    t.earthportrait = 'spazbound'
    
    t.icon_mask_texture = 'neoSpazIconColorMask'
    t.head_mesh = 'neoSpazHead'
    t.torso_mesh = 'neoSpazTorso'
    t.pelvis_mesh = 'neoSpazPelvis'
    t.upper_arm_mesh = 'neoSpazUpperArm'
    t.forearm_mesh = 'neoSpazForeArm'
    t.hand_mesh = 'neoSpazHand'
    t.upper_leg_mesh = 'neoSpazUpperLeg'
    t.lower_leg_mesh = 'neoSpazLowerLeg'
    t.toes_mesh = 'neoSpazToes'
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
    t.death_sounds = ['spazDeath01', 'spazDeath02', 'spazDeath03', 'spazDeath04'] # these too
    t.pickup_sounds = ['spazPickup01']
    t.victory_sounds = ['spazWin01']
    t.gloat_sounds = ['spazGloat01']
    t.fall_sounds = ['spazFall01', 'spazFall02', 'spazFall03', 'spazFall04'] # added these because lemon asked for it :sunglassesmoment:
    t.style = 'spaz'

    # Roaring Knight's right hand they/them #####################################
    t = Appearance('Zoe')
    t.color_texture = 'zoeColor'
    t.color_mask_texture = 'zoeColorMask'
    t.icon_texture = 'zoeIcon'
    t.earthportrait = 'krisbound'
    t.icon_mask_texture = 'zoeIconColorMask'
    t.head_mesh = 'zoeHead'
    t.torso_mesh = 'zoeTorso'
    t.pelvis_mesh = 'zoePelvis'
    t.upper_arm_mesh = 'zoeUpperArm'
    t.forearm_mesh = 'zoeForeArm'
    t.hand_mesh = 'zoeHand'
    t.upper_leg_mesh = 'zoeUpperLeg'
    t.lower_leg_mesh = 'zoeLowerLeg'
    t.toes_mesh = 'zoeToes'
    t.jump_sounds = ['zoeJump01', 'zoeJump02', 'zoeJump03']
    t.attack_sounds = [
        'zoeAttack01',
        'zoeAttack02',
        'zoeAttack03',
        'zoeAttack04',
    ]
    t.impact_sounds = [
        'zoeImpact01',
        'zoeImpact02',
        'zoeImpact03',
        'zoeImpact04',
    ]
    t.death_sounds = ['zoeDeath01']
    t.pickup_sounds = ['zoePickup01']
    t.fall_sounds = ['zoeFall01']
    t.victory_sounds = ['zoeWin01']
    t.style = 'female'
    t.default_color = (0.9215686274509803, 0.0, 0.5843137254901961)
    t.default_highlight = (0.4588235294117647, 0.984313725490196, 0.9294117647058824)

    # gummy ##########################################
    t = Appearance('Snake Shadow')
    t.color_texture = 'ninjaColor'
    t.color_mask_texture = 'ninjaColorMask'
    t.icon_texture = 'ninjaIcon'
    t.earthportrait = 'snakebound'
    t.icon_mask_texture = 'ninjaIconColorMask'
    t.head_mesh = 'ninjaHead'
    t.torso_mesh = 'ninjaTorso'
    t.pelvis_mesh = 'ninjaPelvis'
    t.upper_arm_mesh = 'ninjaUpperArm'
    t.forearm_mesh = 'ninjaForeArm'
    t.hand_mesh = 'ninjaHand'
    t.upper_leg_mesh = 'ninjaUpperLeg'
    t.lower_leg_mesh = 'ninjaLowerLeg'
    t.toes_mesh = 'ninjaToes'
    ninja_attacks = ['ninjaAttack' + str(i + 1) + '' for i in range(7)]
    ninja_hits = ['ninjaHit' + str(i + 1) + '' for i in range(8)]
    ninja_jumps = ['ninjaAttack' + str(i + 1) + '' for i in range(7)]
    t.jump_sounds = ninja_jumps
    t.attack_sounds = ninja_attacks
    t.impact_sounds = ninja_hits
    t.death_sounds = ['ninjaDeath1']
    t.pickup_sounds = ninja_attacks
    t.fall_sounds = ['ninjaFall1']
    t.gloat_sounds = ['ninjaGloat1']
    t.victory_sounds = ['ninjaWin1']
    t.style = 'ninja'
    t.default_color = (0.2, 1, 1)
    t.default_highlight = (1, 1, 1)

    # Barney the relentless Killer #####################################
    t = Appearance('Kronk')
    t.color_texture = 'kronk'
    t.color_mask_texture = 'kronkColorMask'
    t.icon_texture = 'kronkIcon'
    t.earthportrait = 'susiebound'
    t.icon_mask_texture = 'kronkIconColorMask'
    t.head_mesh = 'kronkHead'
    t.torso_mesh = 'kronkTorso'
    t.pelvis_mesh = 'kronkPelvis'
    t.upper_arm_mesh = 'kronkUpperArm'
    t.forearm_mesh = 'kronkForeArm'
    t.hand_mesh = 'kronkHand'
    t.upper_leg_mesh = 'kronkUpperLeg'
    t.lower_leg_mesh = 'kronkLowerLeg'
    t.toes_mesh = 'kronkToes'
    kronk_sounds = [
        'kronk1',
        'kronk2',
        'kronk3',
        'kronk4',
        'kronk5',
        'kronk6',
        'kronk7',
        'kronk8',
        'kronk9',
        'kronk10',
    ]
    t.jump_sounds = kronk_sounds
    t.attack_sounds = kronk_sounds
    t.victory_sounds = ['kronk2']
    t.gloat_sounds = ['kronkGloat']
    t.impact_sounds = kronk_sounds
    t.death_sounds = ['kronkDeath']
    t.pickup_sounds = kronk_sounds
    t.fall_sounds = ['kronkFall']
    t.style = 'kronk'
    t.default_color = (0.9725490196078431, 0.5137254901960784, 0.8431372549019608)
    t.default_highlight = (0.5333333333333333, 0.09019607843137255, 0.41568627450980394)

    # fatass ###########################################
    t = Appearance('Mel')
    t.color_texture = 'melColor'
    t.color_mask_texture = 'melColorMask'
    t.icon_texture = 'melIcon'
    t.earthportrait = 'mellbound'
    t.icon_mask_texture = 'melIconColorMask'
    t.head_mesh = 'melHead'
    t.torso_mesh = 'melTorso'
    t.pelvis_mesh = 'kronkPelvis'
    t.upper_arm_mesh = 'melUpperArm'
    t.forearm_mesh = 'melForeArm'
    t.hand_mesh = 'melHand'
    t.upper_leg_mesh = 'melUpperLeg'
    t.lower_leg_mesh = 'melLowerLeg'
    t.toes_mesh = 'melToes'
    mel_sounds = [
        'mel01',
        'mel02',
        'mel03',
        'mel04',
        'mel05',
        'mel06',
        'mel07',
    ]
    t.jump_sounds = mel_sounds
    t.attack_sounds = mel_sounds
    t.impact_sounds = mel_sounds
    t.death_sounds = ['melDeath01']
    t.victory_sounds = ['mel05']
    t.gloat_sounds = ['melGloat01']
    t.pickup_sounds = mel_sounds
    t.fall_sounds = ['melFall01', 'melFall02']
    t.style = 'mel'
    t.default_color = (1, 1, 1)
    t.default_highlight = (0, 1, 0)

    # Noob #######################################
    t = Appearance('Jack Morgan')
    t.color_texture = 'jackColor'
    t.color_mask_texture = 'jackColorMask'
    t.icon_texture = 'jackIcon'
    t.earthportrait = 'noobbound'
    t.icon_mask_texture = 'jackIconColorMask'
    t.head_mesh = 'jackHead'
    t.torso_mesh = 'jackTorso'
    t.pelvis_mesh = 'kronkPelvis'
    t.upper_arm_mesh = 'jackUpperArm'
    t.forearm_mesh = 'jackForeArm'
    t.hand_mesh = 'jackHand'
    t.upper_leg_mesh = 'jackUpperLeg'
    t.lower_leg_mesh = 'jackLowerLeg'
    t.toes_mesh = 'jackToes'
    hit_sounds = [
        'jackHit01',
        'jackHit02',
        'jackHit03',
        'jackHit04',
        'jackHit05',
        'jackHit06',
        'jackHit07',
    ]
    sounds = ['jack01', 'jack02', 'jack03', 'jack04', 'jack05', 'jack06']
    t.jump_sounds = sounds
    t.attack_sounds = sounds
    t.impact_sounds = hit_sounds
    t.death_sounds = ['jackDeath01']
    t.pickup_sounds = sounds
    t.fall_sounds = ['jackFall01']
    t.style = 'pirate'
    t.default_color = (1.0, 0.99, 0.13999999999999968)
    t.default_highlight = (0.30999999999999994, 0.4599999999999999, 1)   
    
    # john fucking grace. #######################################
    t = Appearance('John')
    t.color_texture = 'graceColor'
    t.color_mask_texture = 'graceColorMask'
    t.icon_texture = 'graceIcon'
    t.earthportrait = 'gracebound'
    t.icon_mask_texture = 'graceIconColorMask'
    t.head_mesh = 'graceHead'
    t.torso_mesh = 'graceTorso'
    t.pelvis_mesh = 'kronkHand'
    t.upper_arm_mesh = 'graceArm'
    t.forearm_mesh = 'kronkHand'
    t.hand_mesh = 'kronkHand'
    t.upper_leg_mesh = 'graceLeg'
    t.lower_leg_mesh = 'kronkHand'
    t.toes_mesh = 'kronkHand'
    sounds = ['blank']
    t.jump_sounds = sounds
    t.attack_sounds = sounds
    t.impact_sounds = sounds
    t.death_sounds = sounds
    t.pickup_sounds = sounds
    t.fall_sounds = sounds
    t.style = 'agent'
    t.default_color = (0.1, 0.1, 0.1)
    t.default_highlight = (1.0, 1.0, 1.0)

    # Snowman ###################################
    t = Appearance('Frosty')
    t.color_texture = 'frostyColor'
    t.color_mask_texture = 'frostyColorMask'
    t.icon_texture = 'frostyIcon'
    t.icon_mask_texture = 'frostyIconColorMask'
    t.head_mesh = 'frostyHead'
    t.torso_mesh = 'frostyTorso'
    t.pelvis_mesh = 'frostyPelvis'
    t.upper_arm_mesh = 'frostyUpperArm'
    t.forearm_mesh = 'frostyForeArm'
    t.hand_mesh = 'frostyHand'
    t.upper_leg_mesh = 'frostyUpperLeg'
    t.lower_leg_mesh = 'frostyLowerLeg'
    t.toes_mesh = 'frostyToes'
    frosty_sounds = ['frosty01', 'frosty02', 'frosty03', 'frosty04', 'frosty05']
    frosty_hit_sounds = ['frostyHit01', 'frostyHit02', 'frostyHit03']
    t.jump_sounds = frosty_sounds
    t.attack_sounds = frosty_sounds
    t.impact_sounds = frosty_hit_sounds
    t.death_sounds = ['frostyDeath']
    t.pickup_sounds = frosty_sounds
    t.fall_sounds = ['frostyFall']
    t.style = 'frosty'
    t.default_color = (0.5, 0.5, 1)
    t.default_highlight = (1, 0.5, 0)

    # Rayman! ################################
    t = Appearance('Bones')
    t.color_texture = 'bonesColor'
    t.color_mask_texture = 'bonesColorMask'
    t.icon_texture = 'bonesIcon'
    t.earthportrait = 'raybound'
    t.icon_mask_texture = 'bonesIconColorMask'
    t.head_mesh = 'bonesHead'
    t.torso_mesh = 'bonesTorso'
    t.pelvis_mesh = 'bonesPelvis'
    t.upper_arm_mesh = 'bonesUpperArm'
    t.forearm_mesh = 'bonesForeArm'
    t.hand_mesh = 'bonesHand'
    t.upper_leg_mesh = 'bonesUpperLeg'
    t.lower_leg_mesh = 'bonesLowerLeg'
    t.toes_mesh = 'bonesToes'
    bones_sounds = ['bones1', 'bones2']
    bones_jump_sounds = ['bones3', 'bones4', 'bones5']
    bones_hit_sounds = ['bonesh1', 'bonesh2', 'bonesh3']
    t.jump_sounds = bones_jump_sounds
    t.attack_sounds = bones_sounds
    t.impact_sounds = bones_hit_sounds
    t.victory_sounds = ['bonesWin01']
    t.death_sounds = ['bonesDeath']
    t.pickup_sounds = bones_sounds
    t.fall_sounds = ['bonesFall']
    t.style = 'bones'
    t.default_color = (0.5, 0.25, 1.0)
    t.default_highlight = (1.0, 0.15, 0.15)

    # Shooowwwtime!! ###################################
    t = Appearance('Bernard')
    t.color_texture = 'bearColor'
    t.color_mask_texture = 'bearColorMask'
    t.icon_texture = 'bearIcon'
    t.earthportrait = 'bowser'
    t.icon_mask_texture = 'bearIconColorMask'
    t.head_mesh = 'bearHead'
    t.torso_mesh = 'bearTorso'
    t.pelvis_mesh = 'bearPelvis'
    t.upper_arm_mesh = 'bearUpperArm'
    t.forearm_mesh = 'bearForeArm'
    t.hand_mesh = 'bearHand'
    t.upper_leg_mesh = 'bearUpperLeg'
    t.lower_leg_mesh = 'bearLowerLeg'
    t.toes_mesh = 'bearToes'
    bear_sounds = ['bear1', 'bear2', 'bear3', 'bear4']
    bear_hit_sounds = ['bearHit1', 'bearHit2']
    t.jump_sounds = bear_sounds
    t.attack_sounds = bear_sounds
    t.impact_sounds = bear_hit_sounds
    t.death_sounds = ['bearDeath']
    t.victory_sounds = ['bearWin']
    t.gloat_sounds = ['bearGloat']
    t.pickup_sounds = bear_sounds
    t.fall_sounds = ['bearFall']
    t.style = 'bear'
    t.default_color = (0.996078431372549, 0.8372549019607842, 0.022745098039215678)
    t.default_highlight = (0.0, 0.5686274509803921, 0.22745098039215686)

    # Prince of the Dark ###################################
    t = Appearance('Pascal')
    t.color_texture = 'penguinColor'
    t.color_mask_texture = 'penguinColorMask'
    t.icon_texture = 'penguinIcon'
    t.earthportrait = 'ralseibound'
    t.icon_mask_texture = 'penguinIconColorMask'
    t.head_mesh = 'penguinHead'
    t.torso_mesh = 'penguinTorso'
    t.pelvis_mesh = 'penguinPelvis'
    t.upper_arm_mesh = 'penguinUpperArm'
    t.forearm_mesh = 'penguinForeArm'
    t.hand_mesh = 'penguinHand'
    t.upper_leg_mesh = 'penguinUpperLeg'
    t.lower_leg_mesh = 'penguinLowerLeg'
    t.toes_mesh = 'penguinToes'
    penguin_sounds = ['penguin1', 'penguin2', 'penguin3', 'penguin4']
    penguin_hit_sounds = ['penguinHit1', 'penguinHit2']
    t.jump_sounds = penguin_sounds
    t.attack_sounds = penguin_sounds
    t.impact_sounds = penguin_hit_sounds
    t.death_sounds = ['penguinDeath']
    t.pickup_sounds = penguin_sounds
    t.fall_sounds = ['penguinFall']
    t.victory_sounds = ['penguinWin1']
    t.gloat_sounds = ['penguinGloat']
    t.style = 'penguin'
    t.default_color = (0.0, 0.7699999999999998, 0.11999999999999998)
    t.default_highlight = (1, 0.08, 0.5)

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
    t = Appearance('B-9000')
    t.color_texture = 'cyborgColor'
    t.color_mask_texture = 'cyborgColorMask'
    t.icon_texture = 'cyborgIcon'
    t.earthportrait = 'knightbound'
    t.icon_mask_texture = 'cyborgIconColorMask'
    t.head_mesh = 'cyborgHead'
    t.torso_mesh = 'cyborgTorso'
    t.pelvis_mesh = 'cyborgPelvis'
    t.upper_arm_mesh = 'cyborgUpperArm'
    t.forearm_mesh = 'cyborgForeArm'
    t.hand_mesh = 'cyborgHand'
    t.upper_leg_mesh = 'cyborgUpperLeg'
    t.lower_leg_mesh = 'cyborgLowerLeg'
    t.toes_mesh = 'cyborgToes'
    cyborg_sounds = ['cyborg1', 'cyborg2', 'cyborg3', 'cyborg4']
    cyborg_hit_sounds = ['cyborgHit1', 'cyborgHit2']
    t.jump_sounds = cyborg_sounds
    t.attack_sounds = cyborg_sounds
    t.impact_sounds = cyborg_hit_sounds
    t.death_sounds = ['cyborgDeath']
    t.pickup_sounds = cyborg_sounds
    t.victory_sounds = ['cyborgWin']
    t.gloat_sounds = ['cyborgGloat']
    t.fall_sounds = ['cyborgFall']
    t.style = 'agent'
    t.default_color = (0.0, 0.0, 0.0)
    t.default_highlight = (1, 1, 1)

    # Noise Noise Noise Noise NOise ###################################
    t = Appearance('Agent Johnson')
    t.color_texture = 'agentColor'
    t.color_mask_texture = 'agentColorMask'
    t.icon_texture = 'agentIcon'
    t.earthportrait = 'noisebound'
    t.icon_mask_texture = 'agentIconColorMask'
    t.head_mesh = 'agentHead'
    t.torso_mesh = 'agentTorso'
    t.pelvis_mesh = 'agentPelvis'
    t.upper_arm_mesh = 'agentUpperArm'
    t.forearm_mesh = 'agentForeArm'
    t.hand_mesh = 'agentHand'
    t.upper_leg_mesh = 'agentUpperLeg'
    t.lower_leg_mesh = 'agentLowerLeg'
    t.toes_mesh = 'agentToes'
    agent_sounds = ['agent1', 'agent2', 'agent3', 'agent4']
    agent_hit_sounds = ['agentHit1', 'agentHit2']
    t.jump_sounds = agent_sounds
    t.attack_sounds = agent_sounds
    t.impact_sounds = agent_hit_sounds
    t.death_sounds = ['agentDeath']
    t.pickup_sounds = agent_sounds
    t.victory_sounds = ['agent1']
    t.gloat_sounds = ['agentGloat']
    t.fall_sounds = ['agentFall']
    t.style = 'agent'
    t.default_color = (0.9725490196078431,
    0.8784313725490196,
    0.5019607843137255
    )
    t.default_highlight = (0.8470588235294118,
    0.5333333333333333,
    0.09411764705882353
    )

    # orange guy with the cap... like some kinda buddy... ###################################
    t = Appearance('Grumbledorf')
    t.color_texture = 'wizardColor'
    t.color_mask_texture = 'wizardColorMask'
    t.icon_texture = 'wizardIcon'
    t.earthportrait = 'capbound'
    t.icon_mask_texture = 'wizardIconColorMask'
    t.head_mesh = 'wizardHead'
    t.torso_mesh = 'wizardTorso'
    t.pelvis_mesh = 'wizardPelvis'
    t.upper_arm_mesh = 'wizardUpperArm'
    t.forearm_mesh = 'wizardForeArm'
    t.hand_mesh = 'wizardHand'
    t.upper_leg_mesh = 'wizardUpperLeg'
    t.lower_leg_mesh = 'wizardLowerLeg'
    t.toes_mesh = 'wizardToes'
    wizard_sounds = ['wizard1', 'wizard2', 'wizard3', 'wizard4']
    wizard_hit_sounds = ['wizardHit1', 'wizardHit2']
    t.jump_sounds = wizard_sounds
    t.attack_sounds = wizard_sounds
    t.impact_sounds = wizard_hit_sounds
    t.death_sounds = ['wizardDeath']
    t.pickup_sounds = wizard_sounds
    t.fall_sounds = ['wizardFall']
    t.style = 'agent'
    t.default_color = (0.2, 0.4, 1.0)
    t.default_highlight = (0.06, 0.15, 0.4)

    # The Original      Spaz ###################################
    t = Appearance('OldLady')
    t.color_texture = 'oldLadyColor'
    t.color_mask_texture = 'oldLadyColorMask'
    t.icon_texture = 'oldLadyIcon'
    t.icon_mask_texture = 'oldLadyIconColorMask'
    t.head_mesh = 'oldLadyHead'
    t.torso_mesh = 'oldLadyTorso'
    t.pelvis_mesh = 'oldLadyPelvis'
    t.upper_arm_mesh = 'oldLadyUpperArm'
    t.forearm_mesh = 'oldLadyForeArm'
    t.hand_mesh = 'oldLadyHand'
    t.upper_leg_mesh = 'oldLadyUpperLeg'
    t.lower_leg_mesh = 'oldLadyLowerLeg'
    t.toes_mesh = 'oldLadyToes'
    old_lady_sounds = ['oldLady1', 'oldLady2', 'oldLady3', 'oldLady4']
    old_lady_hit_sounds = ['oldLadyHit1', 'oldLadyHit2', 'spazogImpact03', 'spazogImpact04']
    t.jump_sounds = ['spazogJump01', 'spazogJump02', 'spazogJump03', 'spazogJump04']
    t.attack_sounds = old_lady_sounds
    t.impact_sounds = old_lady_hit_sounds
    t.death_sounds = ['oldLadyDeath']
    t.pickup_sounds = ['spazogPickup']
    t.victory_sounds = ['spazogJump01']
    t.fall_sounds = ['oldLadyFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    
    # Pixie ###################################
    t = Appearance('Pixel')
    t.color_texture = 'pixieColor'
    t.color_mask_texture = 'pixieColorMask'
    t.icon_texture = 'pixieIcon'
    t.icon_mask_texture = 'pixieIconColorMask'
    t.head_mesh = 'pixieHead'
    t.torso_mesh = 'pixieTorso'
    t.pelvis_mesh = 'pixiePelvis'
    t.upper_arm_mesh = 'pixieUpperArm'
    t.forearm_mesh = 'pixieForeArm'
    t.hand_mesh = 'pixieHand'
    t.upper_leg_mesh = 'pixieUpperLeg'
    t.lower_leg_mesh = 'pixieLowerLeg'
    t.toes_mesh = 'pixieToes'
    pixie_sounds = ['pixie1', 'pixie2', 'pixie3', 'pixie4']
    pixie_hit_sounds = ['pixieHit1', 'pixieHit2']
    t.jump_sounds = pixie_sounds
    t.attack_sounds = pixie_sounds
    t.impact_sounds = pixie_hit_sounds
    t.death_sounds = ['pixieDeath']
    t.pickup_sounds = pixie_sounds
    t.fall_sounds = ['pixieFall']
    t.style = 'pixie'
    t.default_color = (0, 1, 0.7)
    t.default_highlight = (0.65, 0.35, 0.75)

    # Bombgeon's Ninja ###################################
    t = Appearance('Robot')
    t.color_texture = 'robotColor'
    t.color_mask_texture = 'robotColorMask'
    t.icon_texture = 'robotIcon'
    t.icon_mask_texture = 'robotIconColorMask'
    t.head_mesh = 'robotHead'
    t.torso_mesh = 'robotTorso'
    t.pelvis_mesh = 'robotPelvis'
    t.upper_arm_mesh = 'robotUpperArm'
    t.forearm_mesh = 'robotForeArm'
    t.hand_mesh = 'robotHand'
    t.upper_leg_mesh = 'robotUpperLeg'
    t.lower_leg_mesh = 'robotLowerLeg'
    t.toes_mesh = 'robotToes'
    ninja_attacks = ['ninjaAttack' + str(i + 1) + '' for i in range(7)]
    ninja_hits = ['ninjaHit' + str(i + 1) + '' for i in range(8)]
    ninja_jumps = ['ninjaAttack' + str(i + 1) + '' for i in range(7)]
    t.jump_sounds = ninja_jumps
    t.attack_sounds = ninja_attacks
    t.impact_sounds = ninja_hits
    t.death_sounds = ['ninjaDeath1']
    t.pickup_sounds = ninja_attacks
    t.fall_sounds = ['ninjaFall2']
    t.style = 'ninja'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Bunny ###################################
    t = Appearance('Easter Bunny')
    t.color_texture = 'bunnyColor'
    t.color_mask_texture = 'bunnyColorMask'
    t.icon_texture = 'bunnyIcon'
    t.icon_mask_texture = 'bunnyIconColorMask'
    t.head_mesh = 'bunnyHead'
    t.torso_mesh = 'bunnyTorso'
    t.pelvis_mesh = 'bunnyPelvis'
    t.upper_arm_mesh = 'bunnyUpperArm'
    t.forearm_mesh = 'bunnyForeArm'
    t.hand_mesh = 'bunnyHand'
    t.upper_leg_mesh = 'bunnyUpperLeg'
    t.lower_leg_mesh = 'bunnyLowerLeg'
    t.toes_mesh = 'bunnyToes'
    bunny_sounds = ['bunny1', 'bunny2', 'bunny3', 'bunny4']
    bunny_hit_sounds = ['bunnyHit1', 'bunnyHit2']
    t.jump_sounds = ['bunnyJump']
    t.attack_sounds = bunny_sounds
    t.impact_sounds = bunny_hit_sounds
    t.death_sounds = ['bunnyDeath']
    t.pickup_sounds = bunny_sounds
    t.fall_sounds = ['bunnyFall']
    t.style = 'bunny'
    t.default_color = (1, 1, 1)
    t.default_highlight = (1, 0.5, 0.5)
