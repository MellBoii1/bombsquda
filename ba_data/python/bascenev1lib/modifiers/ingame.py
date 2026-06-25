"""Module for all modifiers."""
from typing import override
import bascenev1 as bs
import random
import math

REGISTERED_MODS = []

class Modifier:
    """A modifier that should alter
    specific in-game functions."""
    #: The name of this modifier.
    name: str = 'Modifier'
    #: A short description of what it does.
    description: str = 'Modifies aspects of the game.'
    #: A single, one line decorative phrase.
    oneliner: str = 'Wow, it\'s just like chaos mode!!!'
    #: A string of the modifier's texture.
    icon: str = 'modifierUnknown'
    
    def apply(self):
        """Called when applying the modifier.
        Override this with your code."""
        pass

def register(cls):
    if cls not in REGISTERED_MODS:
        REGISTERED_MODS.append(cls())
    return cls

# ngl i might remove these; mostly just a test
@register
class AllSuper(Modifier):
    name = 'All Super'
    description = 'Turns **EVERY** Spaz super.'
    oneliner = 'Well, if everyone\'s super, then no one is...'
    @override
    def apply(self):
        from bascenev1lib.actor.spaz import Spaz
        for node in bs.getnodes():
            dele = node.getdelegate(Spaz)
            if dele:
                dele.gosuper()

@register
class BombCrit(Modifier):
    name = 'Incoming Bomb Crit'
    description = 'Spawns a bomb towards every spaz.'
    oneliner = 'Useless...?'
    icon = 'modifierBombCrit'
    @override
    def apply(self):
        from bascenev1lib.actor.spaz import Spaz
        from bascenev1lib.actor.bomb import Bomb
        for node in bs.getnodes():
            dele = node.getdelegate(Spaz)
            if dele:
                pos = (
                    node.position[0],
                    node.position[1] + 1.3,
                    node.position[2],
                )

                spawn_pos = (
                    pos[0] + random.uniform(-5, 5),
                    pos[1] + random.uniform(0.5, 2),
                    pos[2] + random.uniform(-5, 5),
                )

                # Direction from bomb -> player
                dx = pos[0] - spawn_pos[0]
                dy = pos[1] - spawn_pos[1]
                dz = pos[2] - spawn_pos[2]

                length = math.sqrt(dx * dx + dy * dy + dz * dz)

                if length > 0:
                    speed = 70.0
                    spawn_vel = (
                        dx / length * speed,
                        dy / length * speed,
                        dz / length * speed,
                    )
                else:
                    spawn_vel = (0, 0, 0)

                Bomb(
                    position=spawn_pos,
                    velocity=spawn_vel,
                ).autoretain()

@register
class RandomEntity(Modifier):
    name = 'Random Encounter'
    description = 'Gives every spaz their own random entity.'
    oneliner = '"I DON\'T EVEN GET TO CHOSE WHOO!?"'
    icon = 'modifierRandomEntity'
    @override
    def apply(self):
        from bascenev1lib.actor.spaz import Spaz, ENTITY_CONFIG
        for node in bs.getnodes():
            dele = node.getdelegate(Spaz)
            if dele:
                dele.create_entity(
                    random.choice( list(ENTITY_CONFIG.keys()) )
                )