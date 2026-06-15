# Released under the MIT License. See LICENSE for details.
#
"""Provides a factory object from creating Spazzes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects, TouchedMessage

if TYPE_CHECKING:
    from typing import Any, Sequence


class SpazFactory:
    """Wraps up media and other resources used by bs.Spaz instances.

    Generally one of these is created per bascenev1.Activity and shared
    between all spaz instances. Use bs.Spaz.get_factory() to return
    the shared factory for the current activity.
    """

    _STORENAME = bs.storagename()

    def _preload(self, character: str) -> None:
        """Preload media needed for a given character."""
        self.get_media(character)

    def __init__(self) -> None:
        """Instantiate a factory object."""
        # pylint: disable=cyclic-import

        plus = bs.app.plus
        assert plus is not None

        # FIXME: should probably put these somewhere common so we don't
        # have to import them from a module that imports us.
        from bascenev1lib.actor.spaz import (
            PickupMessage,
            PunchHitMessage,
            CurseExplodeMessage,
        )

        shared = SharedObjects.get()
        self.impact_sounds_medium = (
            bs.getsound('impactMedium'),
            bs.getsound('impactMedium2'),
        )
        self.impact_sounds_hard = (
            bs.getsound('impactHard'),
            bs.getsound('impactHard2'),
            bs.getsound('impactHard3'),
        )

        self.impact_sounds_harder = (
            bs.getsound('bigImpact'),
            bs.getsound('bigImpact2'),
            bs.getsound('bigImpact3'),
        )
        self.impact_sounds_medium_metal = (
            bs.getsound('bombDrop02'),
        )
        self.impact_sounds_hard_metal = (
            bs.getsound('bombDrop01'),
        )
        self.impact_sounds_harder_metal = (
            bs.getsound('bigImpact2'),
        )
        self.impact_sounds_medium_fancy = (
            bs.getsound('fancyBonk'),
        )
        self.impact_sounds_hard_fancy = (
            bs.getsound('fancyBoing'),
        )
        self.impact_sounds_harder_fancy = (
            bs.getsound('fancyHardBonk01'),
            bs.getsound('fancyHardBonk02'),
            bs.getsound('fancyHardBonk03'),
            bs.getsound('fancyHardBonk04'),
        )
        self.single_player_death_sound = (
            bs.getsound('playerDeath'),
            bs.getsound('playerDeath2'),
            bs.getsound('playerDeath3'),
            bs.getsound('playerDeath4'),
        )
        self.punch_sound_weak = (
            bs.getsound('punchSFX/weak1'),
            bs.getsound('punchSFX/weak2'),
            bs.getsound('punchSFX/weak3'),
            bs.getsound('punchSFX/weak4'),
        )
        self.punch_sound_medium = (
            bs.getsound('punchSFX/medium1'),
            bs.getsound('punchSFX/medium2'),
            bs.getsound('punchSFX/medium3'),
            bs.getsound('punchSFX/medium4'),
        )
        self.punch_sound = bs.getsound('punchSFX/generic')
        strong = ['punchSFX/strong' + str(i + 1) for i in range(15)]
        self.punch_sound_strong = [bs.getsound(s) for s in strong]
        self.punch_sound_stronger = bs.getsound('punchSFX/super')
        self.punch_sound_strongest = bs.getsound('punchSFX/death')
        self.lobotomy = (
            bs.getsound('lobotomized'),
            bs.getsound('owmyorgans'),
        )
        self.swish_sound = bs.getsound('punchSFX/swish')
        self.block_sound = bs.getsound('block')
        self.shatter_sound = bs.getsound('shatter')
        self.splatter_sound = bs.getsound('gibbed')
        self.spaz_material = bs.Material()
        self.roller_material = bs.Material()
        self.punch_material = bs.Material()
        self.pickup_material = bs.Material()
        self.curse_material = bs.Material()

        footing_material = shared.footing_material
        object_material = shared.object_material
        player_material = shared.player_material
        region_material = shared.region_material

        # Send footing messages to spazzes so they know when they're on
        # solid ground.
        # Eww; this probably should just be built into the spaz node.
        self.roller_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('message', 'our_node', 'at_connect', 'footing', 1),
                ('message', 'our_node', 'at_disconnect', 'footing', -1),
            ),
        )

        self.spaz_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('message', 'our_node', 'at_connect', 'footing', 1),
                ('message', 'our_node', 'at_disconnect', 'footing', -1),
            ),
        )

        # Punches.
        self.punch_material.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', PunchHitMessage()),
            ),
        )

        # Pickups.
        self.pickup_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', object_material),
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', PickupMessage()),
            ),
        )

        # Curse.
        self.curse_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', player_material),
            ),
            actions=(
                'message',
                'our_node',
                'at_connect',
                CurseExplodeMessage(),
            ),
        )

        self.foot_impact_sounds = (
            bs.getsound('footImpact01'),
            bs.getsound('footImpact02'),
            bs.getsound('footImpact03'),
        )

        self.foot_skid_sound = bs.getsound('skid01')
        self.foot_roll_sound = bs.getsound('scamper01')

        self.roller_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('impact_sound', self.foot_impact_sounds, 1, 0.2),
                ('skid_sound', self.foot_skid_sound, 20, 0.3),
                ('roll_sound', self.foot_roll_sound, 20, 3.0),
            ),
        )

        self.skid_sound = bs.getsound('gravelSkid')

        self.spaz_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('impact_sound', self.foot_impact_sounds, 20, 6),
                ('skid_sound', self.skid_sound, 2.0, 1),
                ('roll_sound', self.skid_sound, 2.0, 1),
            ),
        )
        
        # Send footing messages to spazzes so they know when they're on
        # solid ground.
        # Eww; this probably should just be built into the spaz node.
        self.roller_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('message', 'our_node', 'at_connect', 'footing', 1),
                ('message', 'our_node', 'at_disconnect', 'footing', -1),
            ),
        )

        self.spaz_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('message', 'our_node', 'at_connect', 'footing', 1),
                ('message', 'our_node', 'at_disconnect', 'footing', -1),
            ),
        )
        from bascenev1lib.actor.spaz import FootingMessage

        self.roller_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('message', 'our_node', 'at_connect', FootingMessage(1)),
                ('message', 'our_node', 'at_disconnect', FootingMessage(-1)),
            ),
        )

        self.spaz_material.add_actions(
            conditions=('they_have_material', player_material),
            actions=(
                ('message', 'our_node', 'at_connect', TouchedMessage(1)),
            ),
        )
        self.spaz_material.add_actions(
            conditions=('they_have_material', object_material),
            actions=(
                ('message', 'our_node', 'at_connect', TouchedMessage(1)),
            ),
        )

        self.shield_up_sound = (
            bs.getsound('shieldUp'),
            bs.getsound('shield2'),
            bs.getsound('shield3'),
        )
        self.shield_down_sound = bs.getsound('shieldDown')
        self.shield_hit_sound = bs.getsound('shieldHit')

        # We don't want to collide with stuff we're initially overlapping
        # (unless its marked with a special region material).
        self.spaz_material.add_actions(
            conditions=(
                (
                    ('we_are_younger_than', 51),
                    'and',
                    ('they_are_different_node_than_us',),
                ),
                'and',
                ('they_dont_have_material', region_material),
            ),
            actions=('modify_node_collision', 'collide', False),
        )

        self.spaz_media: dict[str, Any] = {}

        # Lets load some basic rules.
        # (allows them to be tweaked from the master server)
        self.shield_decay_rate = plus.get_v1_account_misc_read_val('rsdr', 10.0)
        self.punch_cooldown = plus.get_v1_account_misc_read_val('rpc', 100)
        self.punch_cooldown_gloves = plus.get_v1_account_misc_read_val(
            'rpcg', 1050
        )
        self.punch_power_scale = plus.get_v1_account_misc_read_val('rpp', 1.2)
        self.punch_power_scale_gloves = plus.get_v1_account_misc_read_val(
            'rppg', 10000.0
        )
        self.max_shield_spillover_damage = plus.get_v1_account_misc_read_val(
            'rsms', 500
        )

    def get_style(self, character: str) -> str:
        """Return the named style for this character.

        (this influences subtle aspects of their appearance, etc)
        """
        assert bs.app.classic is not None
        return bs.app.classic.spaz_appearances[character].style

    def get_media(self, character: str) -> dict[str, Any]:
        """Return the set of media used by this variant of spaz."""
        assert bs.app.classic is not None
        char = bs.app.classic.spaz_appearances[character]
        if character not in self.spaz_media:
            media = self.spaz_media[character] = {
                'jump_sounds': [bs.getsound(s) for s in char.jump_sounds],
                'attack_sounds': [bs.getsound(s) for s in char.attack_sounds],
                'impact_sounds': [bs.getsound(s) for s in char.impact_sounds],
                'death_sounds': [bs.getsound(s) for s in char.death_sounds],
                'pickup_sounds': [bs.getsound(s) for s in char.pickup_sounds],
                'fall_sounds': [bs.getsound(s) for s in char.fall_sounds],
                'victory_sounds': [bs.getsound(s) for s in char.victory_sounds],
                'gloat_sounds': [bs.getsound(s) for s in char.gloat_sounds],
                'ffire_sounds': [bs.getsound(s) for s in char.ffire_sounds],
                'teamkill_sounds': [bs.getsound(s) for s in char.teamkill_sounds],
                'color_texture': bs.gettexture(char.color_texture),
                'color_mask_texture': bs.gettexture(char.color_mask_texture),
                'icon_texture': bs.gettexture(char.icon_texture),
                'icon_mask_texture': bs.gettexture(char.icon_mask_texture),
                'head_mesh': bs.getmesh(char.head_mesh),
                'torso_mesh': bs.getmesh(char.torso_mesh),
                'pelvis_mesh': bs.getmesh(char.pelvis_mesh),
                'upper_arm_mesh': bs.getmesh(char.upper_arm_mesh),
                'forearm_mesh': bs.getmesh(char.forearm_mesh),
                'hand_mesh': bs.getmesh(char.hand_mesh),
                'upper_leg_mesh': bs.getmesh(char.upper_leg_mesh),
                'lower_leg_mesh': bs.getmesh(char.lower_leg_mesh),
                'toes_mesh': bs.getmesh(char.toes_mesh),
                'earthportrait': bs.gettexture(char.earthportrait),
                'EBlose': bs.gettexture(char.EBlose),
                'EBwin': bs.gettexture(char.EBwin),
                'style': char.style,
                'general_style': char.general_style,
                'expression_changes': char.expression_changes,
                'super_color': char.super_color,
                'super_highlight': char.super_highlight,
                'super_music': char.super_music,
            }
        else:
            media = self.spaz_media[character]
        return media

    @classmethod
    def get(cls) -> SpazFactory:
        """Return the shared bs.SpazFactory, creating it if necessary."""
        # pylint: disable=cyclic-import
        activity = bs.getactivity()
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = activity.customdata[cls._STORENAME] = SpazFactory()
        assert isinstance(factory, SpazFactory)
        return factory
