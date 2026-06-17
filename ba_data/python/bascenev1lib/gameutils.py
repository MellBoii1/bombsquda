# Released under the MIT License. See LICENSE for details.
#
"""Various utilities useful for gameplay."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs
import random

if TYPE_CHECKING:
    pass

class FootingMessage:
    """A message that tells a Spaz it's 
    current state of footing."""
    def __init__(self, footing):
        self.footing = footing

class TouchedMessage:
    """A generic message for 
    when 2 objects touch."""
    def __init__(self, state):
        self.state = state

class BounceMessage:
    """A message that tells a 
    fireball to bounce."""
    pass
    
class HookedMessage:
    """A message that tells a
    whiplash it has hooked onto something."""
    pass
    
class SharedObjects:
    """Various common components for use in games.

    Objects contained here are created on-demand as accessed and shared
    by everything in the current activity. This includes things such as
    standard materials.
    """

    _STORENAME = bs.storagename()

    def __init__(self) -> None:
        activity = bs.getactivity()
        if self._STORENAME in activity.customdata:
            raise RuntimeError(
                'Use SharedObjects.get() to fetch the'
                ' shared instance for this activity.'
            )
        self._object_material: bs.Material | None = None
        self._player_material: bs.Material | None = None
        self._pickup_material: bs.Material | None = None
        self._footing_material: bs.Material | None = None
        self._attack_material: bs.Material | None = None
        self._death_material: bs.Material | None = None
        self._region_material: bs.Material | None = None
        self._railing_material: bs.Material | None = None
        self._particle_material: bs.Material | None = None
        self._sorrowful_material: bs.Material | None = None
        self._touch_material: bs.Material | None = None
        self._fireball_material: bs.Material | None = None
        self._emerald_material: bs.Material | None = None

    @classmethod
    def get(cls) -> SharedObjects:
        """Fetch/create the instance of this class for the current activity."""
        activity = bs.getactivity()
        shobs = activity.customdata.get(cls._STORENAME)
        if shobs is None:
            shobs = SharedObjects()
            activity.customdata[cls._STORENAME] = shobs
        assert isinstance(shobs, SharedObjects)
        return shobs

    @property
    def player_material(self) -> bs.Material:
        """a bascenev1.Material to be applied to player parts. Generally,
        materials related to the process of scoring when reaching a goal, etc
        will look for the presence of this material on things that hit them.
        """
        if self._player_material is None:
            self._player_material = bs.Material()
        return self._player_material

    @property
    def object_material(self) -> bs.Material:
        """A bascenev1.Material that should be applied to any small,
        normal, physical objects such as bombs, boxes, players, etc. Other
        materials often check for the  presence of this material as a
        prerequisite for performing certain actions (such as disabling
        collisions between initially-overlapping objects)
        """
        if self._object_material is None:
            self._object_material = bs.Material()
        return self._object_material

    @property
    def pickup_material(self) -> bs.Material:
        """A bascenev1.Material; collision shapes used for picking things
        up will have this material applied. To prevent an object from being
        picked up, you can add a material that disables collisions against
        things containing this material.
        """
        if self._pickup_material is None:
            self._pickup_material = bs.Material()
        return self._pickup_material

    @property
    def footing_material(self) -> bs.Material:
        """Anything that can be 'walked on' should have this
        bascenev1.Material applied; generally just terrain and whatnot.
        A character will snap upright whenever touching something with this
        material so it should not be applied to props, etc.
        """
        if self._footing_material is None:
            self._footing_material = bs.Material()
        return self._footing_material

    @property
    def attack_material(self) -> bs.Material:
        """A bascenev1.Material applied to explosion shapes, punch
        shapes, etc.  An object not wanting to receive impulse/etc messages can
        disable collisions against this material.
        """
        if self._attack_material is None:
            self._attack_material = bs.Material()
        return self._attack_material

    @property
    def death_material(self) -> bs.Material:
        """A bascenev1.Material that sends a ba.DieMessage() to anything
        that touches it; handy for terrain below a cliff, etc.
        """
        if self._death_material is None:
            mat = self._death_material = bs.Material()
            mat.add_actions(
                ('message', 'their_node', 'at_connect', bs.OutOfBoundsMessage())
            )
        return self._death_material
        
    # Kay so rule of thumb is; Don't make a
    # thousand materials. Just make one shared instance. Learned that the hard way.
    @property
    def particle_material(self) -> bs.Material:
        if self._particle_material is None:
            mat = self._particle_material = bs.Material()
            mat.add_actions(
                conditions=('they_have_material', self.footing_material),
                actions=(
                    ('message', 'our_node', 'at_connect', FootingMessage(1)),
                    ('message', 'our_node', 'at_disconnect', FootingMessage(-1)),
                ),
            )
            mat.add_actions(
                conditions=( 
                    ('they_are_different_node_than_us',),
                    'and',
                    ('they_dont_have_material', self.region_material),
                    'or',
                    ('they_dont_have_material', self.footing_material),
                ),
                actions=('modify_node_collision', 'collide', False),
            )
            mat.add_actions(
                conditions=( 
                    ('they_are_different_node_than_us',),
                    'and',
                    ('they_have_material', self.region_material),
                    'or',
                    ('they_have_material', self.footing_material),
                ),
                actions=('modify_node_collision', 'collide', True),
            )
        return self._particle_material
    
    @property
    def sorrowful_material(self) -> bs.Material:
        """A material that's like... really sad? I dunno."""
        if self._sorrowful_material is None:
            mat = self._sorrowful_material = bs.Material()
            mat.add_actions(
                conditions=('they_have_material', self.footing_material),
                actions=(
                    ('message', 'our_node', 'at_connect', FootingMessage(1)),
                    ('message', 'our_node', 'at_disconnect', FootingMessage(-1)),
                ),
            )
            mat.add_actions(
                conditions=('they_have_material', self.object_material),
                actions=(
                    ('message', 'our_node', 'at_connect', TouchedMessage(1)),
                ),
            )
            mat.add_actions(
                conditions=( 
                    ('they_are_different_node_than_us',),
                    'and',
                    ('they_dont_have_material', self.region_material),
                    'or',
                    ('they_dont_have_material', self.footing_material),
                ),
                actions=('modify_node_collision', 'collide', False),
            )
            mat.add_actions(
                conditions=( 
                    ('they_are_different_node_than_us',),
                    'and',
                    ('they_have_material', self.region_material),
                    'or',
                    ('they_have_material', self.footing_material),
                    'or',
                    ('they_have_material', self.object_material),
                ),
                actions=('modify_node_collision', 'collide', True),
            )
        return self._sorrowful_material
    
    @property
    def touch_material(self) -> bs.Material:
        if self._touch_material is None:
            self._touch_material = mat = bs.Material()
            mat.add_actions(
                conditions=('they_have_material', self.object_material),
                actions=(
                    ('modify_part_collision', 'collide', True),
                    ('modify_part_collision', 'physical', True),
                    ('message', 'our_node', 'at_connect', TouchedMessage(1)),
                ),
            )
            mat.add_actions(
                conditions=('they_have_material', self.player_material),
                actions=(
                    ('modify_part_collision', 'collide', True),
                    ('modify_part_collision', 'physical', True),
                    ('message', 'our_node', 'at_connect', TouchedMessage(1)),
                ),
            )
        return self._touch_material
    
    @property
    def fireball_material(self) -> bs.Material:
        if self._fireball_material is None:
            mat = self._fireball_material = bs.Material()
            mat.add_actions(
                conditions=('they_have_material', self.object_material),
                actions=(
                    ('message', 'our_node', 'at_connect', TouchedMessage(1)),
                ),
            )
            mat.add_actions(
                conditions=('they_have_material', self.player_material),
                actions=(
                    ('message', 'our_node', 'at_connect', TouchedMessage(1)),
                ),
            )
            mat.add_actions(
                conditions=('they_have_material', self.footing_material),
                actions=(
                    ('message', 'our_node', 'at_connect', BounceMessage()),
                ),
            )
            # disallow collisions if we JUST spawned recently
            mat.add_actions(
                conditions=(
                    (
                        ('we_are_younger_than', 70),
                        'and',
                        ('they_are_different_node_than_us',),
                    ),
                    'and',
                    ('they_dont_have_material', self.region_material),
                ),
                actions=('modify_node_collision', 'collide', False),
            )
        return self._fireball_material
    
    @property
    def emerald_material(self) -> bs.Material:
        if self._emerald_material is None:
            mat = self._emerald_material = bs.Material()
            # disallow collisions if we JUST spawned recently
            mat.add_actions(
                conditions=(
                    (
                        ('we_are_younger_than', 70),
                        'and',
                        ('they_are_different_node_than_us',),
                    ),
                    'and',
                    ('they_dont_have_material', self.region_material),
                ),
                actions=('modify_node_collision', 'collide', False),
            )
        return self._emerald_material

    @property
    def region_material(self) -> bs.Material:
        """A bascenev1.Material used for non-physical collision shapes
        (regions); collisions can generally be allowed with this material even
        when initially overlapping since it is not physical.
        """
        if self._region_material is None:
            self._region_material = bs.Material()
        return self._region_material

    @property
    def railing_material(self) -> bs.Material:
        """A bascenev1.Material with a very low friction/stiffness/etc
        that can be applied to invisible 'railings' useful for gently keeping
        characters from falling off of cliffs.
        """
        if self._railing_material is None:
            mat = self._railing_material = bs.Material()
            mat.add_actions(('modify_part_collision', 'collide', False))
            mat.add_actions(('modify_part_collision', 'stiffness', 0.003))
            mat.add_actions(('modify_part_collision', 'damping', 0.00001))
            mat.add_actions(
                conditions=('they_have_material', self.player_material),
                actions=(
                    ('modify_part_collision', 'collide', True),
                    ('modify_part_collision', 'friction', 0.0),
                ),
            )
        return self._railing_material
