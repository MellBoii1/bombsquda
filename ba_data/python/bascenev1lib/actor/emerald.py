"""Actor for a chaos emerald."""
import random
import bascenev1 as bs
from typing import Any, Sequence, override
from bascenev1lib.gameutils import SharedObjects, TouchedMessage
from babase._logging import squdalog

class EmeraldActor(bs.Actor):
    """
    The actor for a chaos emerald.
    To every actor that touches it, it gives out a
    EmeraldMessage() with the type we have.
    """
    node: bs.Node
    
    def __init__(
        self,
        position: Sequence[float],
        force_type = None
    ):
        super().__init__()
        self.mesh = bs.getmesh('chaosEmerald')
        self.texname = force_type if force_type else self.get_fairest_emerald()
        self.tex = bs.gettexture(self.texname)
        shared = SharedObjects.get()
        self.emeralds_die = True
        self.mscale = 0.6
        if self.emeralds_die:
            self.deathTimer = bs.Timer(5, self.scheduled_die_message)
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'body_scale': 0.3,
                'position': position,
                'mesh': self.mesh,
                'mesh_scale': 0,
                'light_mesh': self.mesh,
                'shadow_size': 0.5,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (
                    shared.touch_material, 
                    shared.object_material, 
                    shared.emerald_material
                ),
            },
        )
        bs.animate(self.node, 'mesh_scale', {0: 0, 0.3: self.mscale})
        
    def scheduled_die_message(self):
        if not self.node:
            return
        self.handlemessage(bs.DieMessage())
        
    def get_fairest_emerald(self) -> str:
        from bascenev1lib.actor.spaz import Spaz
        all_types = [f"emerald{i}" for i in range(1, 8)]


        # Initialize counts
        counts = {e: 0 for e in all_types}

        # Count emeralds from *all* spazzes in the activity
        # (not just players; bots too)
        for node in bs.getnodes():
            actor = node.getdelegate(Spaz)
            
            if not actor:
                continue

            emeralds = getattr(actor, "emeralds", [])

            for e in emeralds:
                if e in counts:
                    counts[e] += 1
                    
        min_count = min(counts.values())

        candidates = [e for e, c in counts.items() if c == min_count]

        chosen = random.choice(candidates)

        return chosen

    def _handle_hit(self, msg: Any) -> None:
        if msg.hit_type == 'explosion': # exploded? just die
            self.scheduled_die_message()
        # likely hit by a punch; apply impulse
        self.node.handlemessage(
            'impulse',
            msg.pos[0],
            msg.pos[1],
            msg.pos[2],
            msg.velocity[0],
            msg.velocity[1],
            msg.velocity[2],
            msg.magnitude,
            msg.velocity_magnitude,
            msg.radius,
            0,
            msg.velocity[0],
            msg.velocity[1],
            msg.velocity[2],
        )
        
    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if self.node:
                if msg.immediate:
                    self.node.delete()
                else:
                    bs.animate(self.node, 'mesh_scale', {0: self.mscale, 0.1: 0})
                    bs.timer(0.1, self.node.delete)
                self.deathTimer = None

        elif isinstance(msg, TouchedMessage):
            if not self.node:
                return
            toucher = bs.getcollision().opposingnode
            isspaz = toucher.getnodetype() == 'spaz'
            actor = toucher.getdelegate(bs.Actor)
            # very long list of conditions
            if (
                not toucher
                or not actor
                or not actor.is_alive()
                or not isspaz
            ):
                return
            from bascenev1lib.actor.spaz import EmeraldMessage
            toucher.handlemessage(EmeraldMessage(self.texname, self.node))

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))

        elif isinstance(msg, bs.HitMessage):
            self._handle_hit(msg)
        else:
            return super().handlemessage(msg)
        return None