# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor(s)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs
from bascenev1lib.actor.popuptext import PopupText

from bascenev1lib.gameutils import SharedObjects
import mellboii.mell_resources as mell

if TYPE_CHECKING:
    from typing import Any, Sequence

DEFAULT_POWERUP_INTERVAL = 8

class _TouchedMessage:
    pass


class PowerupBoxFactory:
    """A collection of media and other resources used by bs.Powerups.

    A single instance of this is shared between all powerups
    and can be retrieved via bs.Powerup.get_factory().
    """

    _STORENAME = bs.storagename()

    def __init__(self) -> None:
        """Instantiate a PowerupBoxFactory.

        You shouldn't need to do this; call Powerup.get_factory()
        to get a shared instance.
        """
        from bascenev1 import get_default_powerup_distribution
        from bascenev1._powerup import get_powerup_dist2

        shared = SharedObjects.get()
        self._lastpoweruptype: str | None = None
        self.mesh = bs.getmesh('powerup')
        self.mesh_simple = bs.getmesh('powerupSimple')
        self.health_powerup_sounds = (
            bs.getsound('healthPowerup'),
            bs.getsound('healthPowerup2'),
        )
        self.powerup_sound = bs.getsound('powerup01')
        self.powerdown_sound = bs.getsound('powerdown01')
        self.drop_sound = bs.getsound('boxDrop')

        # Material for powerups.
        self.powerup_material = bs.Material()

        # Material for anyone wanting to accept powerups.
        self.powerup_accept_material = bs.Material()

        # Pass a powerup-touched message to applicable stuff.
        self.powerup_material.add_actions(
            conditions=('they_have_material', self.powerup_accept_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', _TouchedMessage()),
            ),
        )

        # We don't wanna be picked up.
        self.powerup_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'collide', False),
        )

        self.powerup_material.add_actions(
            conditions=('they_have_material', shared.footing_material),
            actions=('impact_sound', self.drop_sound, 0.5, 0.1),
        )

        self._powerupdist: list[str] = []
        self._powerupdist2: list[str] = []
        for powerup, freq in get_default_powerup_distribution():
            for _i in range(int(freq)):
                self._powerupdist.append(powerup)
        
        for powerup, freq in get_powerup_dist2():
            for _i in range(int(freq)):
                self._powerupdist2.append(powerup)
                

    def get_random_powerup_type(
        self,
        forcetype: str | None = None,
        excludetypes: list[str] | None = None,
    ) -> str:
        """Returns a random powerup type (string).

        See bs.Powerup.poweruptype for available type values.

        There are certain non-random aspects to this; a 'curse' powerup,
        for instance, is always followed by a 'health' powerup (to keep things
        interesting). Passing 'forcetype' forces a given returned type while
        still properly interacting with the non-random aspects of the system
        (ie: forcing a 'curse' powerup will result
        in the next powerup being health).
        """
        if excludetypes is None:
            excludetypes = []
        if forcetype:
            ptype = forcetype
        else:
            # If the last one was a curse, make this one a health to
            # provide some hope.
            if self._lastpoweruptype == 'curse':
                ptype = 'health'
            else:
                while True:
                    if len(self._powerupdist) <= 0:
                        return None
                    ptype = self._powerupdist[
                        random.randint(0, len(self._powerupdist) - 1)
                    ]
                    if ptype not in excludetypes:
                        break
        self._lastpoweruptype = ptype
        return ptype
    
    def get_random_powerup_type2(
        self,
        forcetype: str | None = None,
        excludetypes: list[str] | None = None,
    ) -> str:
        if excludetypes is None:
            excludetypes = []
        while True:
            if len(self._powerupdist2) <= 0:
                return None
            ptype = self._powerupdist2[
                random.randint(0, len(self._powerupdist2) - 1)
            ]
            if ptype not in excludetypes:
                break
        return ptype

    @classmethod
    def get(cls) -> PowerupBoxFactory:
        """Return a shared bs.PowerupBoxFactory object, creating if needed."""
        activity = bs.getactivity()
        if activity is None:
            raise bs.ContextError('No current activity.')
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = activity.customdata[cls._STORENAME] = PowerupBoxFactory()
        assert isinstance(factory, PowerupBoxFactory)
        return factory


class PowerupBox(bs.Actor):
    """A box that grants a powerup.

    This will deliver a :class:`~bascenev1.PowerupMessage` to anything
    that touches it which has the
    :class:`~PowerupBoxFactory.powerup_accept_material` applied.
    """
    poweruptype: str

    node: bs.Node
    """The 'prop' node representing this box."""

    def __init__(
        self,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        poweruptype: str = 'triple_bombs',
        expire: bool = True,
    ):
        """Create a powerup-box of the requested type at the given position.

        see bs.Powerup.poweruptype for valid type strings.
        """
        super().__init__()
        if poweruptype is None:
            self = None
            return
        # ugliest sanity check but eh
        if not isinstance(poweruptype, str): 
            if None in poweruptype:
                self = None
                return
        factory = PowerupBoxFactory.get()
        # If powerup was a watercooler but 
        # if it had already spawned or we're in coop, 
        # randomize it to another one instead.
        if (
            poweruptype == 'watercooler'
            and (
                isinstance(
                    self.getactivity().session, 
                    bs.CoopSession
                )
                or self.getactivity().water_cooler_spawned
            )
        ):
            poweruptype = random.choice(
                list(
                    pwup for pwup in factory._powerupdist
                    if pwup != 'watercooler'
                )
            )
        shared = SharedObjects.get()
        self.interval = DEFAULT_POWERUP_INTERVAL
        if self.getactivity().hardmode:
            self.interval = 5.5
        self.poweruptype = poweruptype
        self._powersgiven = False

        tex = mell.get_texture_for_powerup(poweruptype)

        if len(position) != 3:
            raise ValueError('expected 3 floats for position')

        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'position': position,
                'mesh': factory.mesh,
                'light_mesh': factory.mesh_simple,
                'shadow_size': 0.5,
                'color_texture': tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (factory.powerup_material, shared.object_material),
            },
        )

        # Animate in.
        curve = bs.animate(self.node, 'mesh_scale', {0: 0, 0.14: 1.6, 0.2: 1})
        bs.timer(0.2, curve.delete)

        if expire:
            bs.timer(
                self.interval - 3.5,
                bs.WeakCall(self._start_flashing),
            )
            bs.timer(
                self.interval - 1.5,
                bs.WeakCall(self.handlemessage, bs.DieMessage()),
            )

    def _start_flashing(self) -> None:
        if self.node:
            self.node.flashing = True

    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired

        if isinstance(msg, bs.PowerupAcceptMessage):
            factory = PowerupBoxFactory.get()
            assert self.node
            if self.poweruptype == 'health':
                sounds = factory.health_powerup_sounds
                sound = sounds[random.randrange(len(sounds))]
                sound.play(position=self.node.position, volume=3.0)
            factory.powerup_sound.play(3, position=self.node.position)
            self._powersgiven = True
            self.handlemessage(bs.DieMessage())

        elif isinstance(msg, _TouchedMessage):
            if not self._powersgiven:
                node = bs.getcollision().opposingnode
                node.handlemessage(
                    bs.PowerupMessage(self.poweruptype, sourcenode=self.node)
                )

        elif isinstance(msg, bs.DieMessage):
            if self.node:
                if msg.immediate:
                    self.node.delete()
                else:
                    bs.animate(self.node, 'mesh_scale', {0: 1, 0.1: 0})
                    bs.timer(0.1, self.node.delete)

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())

        elif isinstance(msg, bs.HitMessage):
            self.handlemessage(bs.DieMessage())
        else:
            return super().handlemessage(msg)
        return None
