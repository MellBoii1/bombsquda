"""script for a Hook, and a fireball. Combined!"""
import random
import bascenev1 as bs
import math
from typing import Any, Sequence, override
from bascenev1lib.gameutils import (
    SharedObjects, 
    TouchedMessage, 
    HookedMessage, 
    BounceMessage
)

class UKHook(bs.Actor):
    """A 'hook' that tells a Spaz 
    it's been hooked once it gets touched."""
    node: bs.Node
    
    def __init__(
        self,
        position: Sequence[float],
        owner: bs.Actor,
    ):
        super().__init__()
        self.mesh = bs.getmesh('shrapnel1')
        self.tex = bs.gettexture('eggTex2')
        self.scale = 0.3
        self.bscale = 0.3
        self.hookTimer = None
        self.owner = owner
        self.allowtouches = True
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'body_scale': self.bscale,
                'position': position,
                'mesh': self.mesh,
                'mesh_scale': 0,
                'light_mesh': self.mesh,
                'shadow_size': self.bscale,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (shared.touch_material, shared.object_material),
            },
        )
        self.soundloop = bs.newnode(
            'sound',
            owner=self.node,
            attrs={
                'sound': bs.getsound('hook_pulling'),
                'volume': 0,
                'position': self.node.position,
            }
        )
        self.node.connectattr('position', self.soundloop, 'position')
        bs.animate(self.node, 'mesh_scale', {0: 0, 0.2: self.scale})
        
    def _update_hook(self):
        if (
            not self._hooked_node 
            or not self.node 
            or not self.owner.node
        ):
            if self.soundloop:
                self.soundloop.volume = 0
            if self.node:
                self.node.delete()
            self._hooked_actor = None
            self.hookTimer = None
            return

        target_pos = self._hooked_node.position

        self.node.position = (
            target_pos[0] + self._offset[0],
            target_pos[1] + self._offset[1],
            target_pos[2] + self._offset[2],
        )

        # Check distance between owner and target
        owner_pos = self.owner.node.position
        dx = target_pos[0] - owner_pos[0]
        dy = target_pos[1] - owner_pos[1]
        dz = target_pos[2] - owner_pos[2]

        dist = math.sqrt(dx*dx + dy*dy + dz*dz)

        if dist < 0.5:
            self.handlemessage(bs.DieMessage())
            return
        if self.soundloop:
            self.soundloop.volume = 5
        # Pull owner toward target
        strength = 120.0
        self.owner.node.handlemessage(
            'impulse',
            owner_pos[0],
            owner_pos[1],
            owner_pos[2],
            0, 0, 0,
            80, 80, 0,
            0,
            dx * strength,
            dy * strength,
            dz * strength,
        )
        
    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if not self.node:
                return
            if msg.immediate:
                if self.soundloop:
                    self.soundloop.volume = 0
                    self.soundloop.delete()
                self.node.delete()
            else:
                if self.soundloop:
                    self.soundloop.volume = 0
                    self.soundloop.delete()
                bs.animate(self.node, 'mesh_scale', {0: self.scale, 0.1: 0})
                bs.timer(0.1, self.node.delete)

        elif isinstance(msg, TouchedMessage):
            if not self.node:
                return
            toucher = bs.getcollision().opposingnode
            ishookable = toucher.getnodetype() in ['spaz', 'prop', 'bomb'] 
            actor = toucher.getdelegate(bs.Actor)
            # very long list of conditions
            if (
                not toucher
                or not actor
                or not actor.is_alive()
                or actor == self.owner
                or not self.allowtouches
            ):
                return
            self._hooked_actor = actor
            self._hooked_node = toucher
            bs.getsound('hook_catch').play(position=self.node.position)

            my_pos = self.node.position
            target_pos = toucher.position

            self._offset = (
                my_pos[0] - target_pos[0],
                my_pos[1] - target_pos[1],
                my_pos[2] - target_pos[2],
            )
            self._update_hook()
            self.hookTimer = bs.Timer(0.02, self._update_hook, repeat=True)
            self.allowtouches = False
            toucher.handlemessage(HookedMessage())

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        elif isinstance(msg, bs.HitMessage):
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
            if msg.magnitude >= 200:
                bs.emitfx(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    count=120,
                    scale=4.0,
                    spread=1.5,
                    chunk_type='spark',
                )
                bs.getsound('smb1_kick').play(position=self.node.position)
                bs.getsound('explosion01').play(position=self.node.position)
                self.handlemessage(bs.DieMessage(immediate=True))
        else:
            return super().handlemessage(msg)
        return None

class Fireball(bs.Actor):
    """A fireball that bounces around, gives a 
    hitmessage when getting touched by a Spaz and dies."""
    node: bs.Node
    
    def __init__(
        self,
        position: Sequence[float],
        owner: bs.Actor,
    ):
        super().__init__()
        self.mesh = bs.getmesh('bomb')
        self.tex = bs.gettexture('confetti_colors/orange')
        self.scale = 0.7
        self.bscale = 0.9
        self.owner = owner
        self.hurtpoints = random.randint(100, 350)
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'sphere',
                'body_scale': self.bscale,
                'position': position,
                'mesh': self.mesh,
                'mesh_scale': 0,
                'light_mesh': self.mesh,
                'shadow_size': self.bscale,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (shared.fireball_material, shared.object_material),
            },
        )
        self.dying = False
        self.deathTimer = bs.Timer(7, self.autodie)
        self.fireTimer = bs.Timer(0.1, self.spark, repeat=True)
        bs.animate(self.node, 'mesh_scale', {0: 0, 0.2: self.scale})
    
    def spark(self):
        if not self.node:
            self.fireTimer = None
            return
        bs.emitfx(
            position=self.node.position,
            chunk_type='sweat',
            velocity=self.node.velocity,
            count=30,
            scale=1.1,
            spread=0.15,
        )
    
    def autodie(self):
        if not self.node or self.expired:
            return None
        self.handlemessage(bs.DieMessage())
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        if self.expired:
            return None
            
        if isinstance(msg, bs.DieMessage):
            self.dying = True
            if msg.immediate:
                self.node.delete()
            else:
                bs.animate(self.node, 'mesh_scale', {0: self.scale, 0.1: 0})
                bs.timer(0.1, self.node.delete)
                
        elif isinstance(msg, TouchedMessage):
            collision = bs.getcollision()
            toucher = collision.opposingnode
            if not toucher:
                return None
            ishittable = toucher.getnodetype() in ['spaz', 'prop', 'bomb', 'flag']
            if not ishittable:
                return None
            actor = toucher.getdelegate(bs.Actor)
            fireball = toucher.getdelegate(Fireball)
            if (
                not actor
                or not actor.is_alive()
                or actor is self.owner
                or fireball
                or self.dying
            ):
                return None
            bs.emitfx(
                position=self.node.position,
                chunk_type='sweat',
                velocity=self.node.velocity,
                count=95,
                scale=3.2,
                spread=0.30,
            )
            srcpl = getattr(self.owner, 'source_player', None)
            toucher.handlemessage(
                bs.HitMessage(
                    magnitude=self.hurtpoints,
                    pos=self.node.position,
                    velocity=self.node.velocity,
                    radius=0,
                    srcnode=self.node,
                    source_player=srcpl,
                    hit_type='fireball',
                )
            )
            bs.getsound('smb1_kick').play(position=self.node.position)
            self.handlemessage(bs.DieMessage())
        
        elif isinstance(msg, BounceMessage):
            y = 120 / self.bscale
            self.node.handlemessage('impulse', 
                self.node.position[0], 
                self.node.position[1], 
                self.node.position[2],
                0, 25, 0,
                y, 0.05, 0, 0,
                0, 20*800, 0
            )
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        else:
            return super().handlemessage(msg)
        return None
        
class Tear(bs.Actor):
    """One of Isaac's tears that flies forward, gives a hitmessage when
    getting touched by a Spaz and dies upon colliding with any surface."""
    node: bs.Node
    
    def __init__(
        self,
        position: Sequence[float],
        owner: bs.Actor,
        body_scale: float = 0.9,
        scale: float = 0.25,
        mesher = 'shield',
        texturer = 'confetti_colors/blue'
    ):
        super().__init__()
        self.mesh = bs.getmesh(mesher)
        self.tex = bs.gettexture(texturer)
        self.scale = scale
        self.bscale = body_scale
        self.owner = owner
        self.hurtpoints = random.randint(80,200)
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'sphere',
                'body_scale': self.bscale,
                'gravity_scale': 0,
                'position': position,
                'mesh': self.mesh,
                'mesh_scale': 0,
                'light_mesh': self.mesh,
                'shadow_size': self.bscale,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (shared.fireball_material, shared.object_material),
            },
        )
        self.dying = False
        self.deathTimer = bs.Timer(7, self.autodie)
        self.fireTimer = bs.Timer(0.1, self.spark, repeat=True)
        bs.animate(self.node, 'mesh_scale', {0: 0, 0.2: self.scale})
    
    def autodie(self):
        if not self.node or self.expired:
            return None
        self.handlemessage(bs.DieMessage())
    
    def spark(self):
        if not self.node:
            self.fireTimer = None
            return
        bs.emitfx(
            position=self.node.position,
            chunk_type='ice',
            velocity=self.node.velocity,
            count=1,
            scale=0.5,
            spread=0.1,
        )
        
    @override
    def handlemessage(self, msg: Any) -> Any:
        if self.expired:
            return None

        if isinstance(msg, bs.DieMessage):
            self.dying = True
            if msg.immediate:
                self.node.delete()
            else:
                bs.animate(self.node, 'mesh_scale', {0: self.scale, 0.1: 0})
                bs.timer(0.1, self.node.delete)
        
        elif isinstance(msg, TouchedMessage):
            collision = bs.getcollision()
            toucher = collision.opposingnode
            if not toucher:
                return None
            ishittable = toucher.getnodetype() in ['spaz', 'prop', 'bomb', 'flag']
            if not ishittable:
                return None
            actor = toucher.getdelegate(bs.Actor)
            fireball = toucher.getdelegate(Fireball)
            if (
                not actor
                or not actor.is_alive()
                or actor is self.owner
                or fireball
                or self.dying
            ):
                return None
            bs.emitfx(
                position=self.node.position,
                chunk_type='ice',
                velocity=self.node.velocity,
                count=10,
                scale=0.6,
                spread=0.30,
            )
            srcpl = getattr(self.owner, 'source_player', None)
            toucher.handlemessage(
                bs.HitMessage(
                    magnitude=self.hurtpoints,
                    pos=self.node.position,
                    velocity=self.node.velocity,
                    radius=0,
                    srcnode=self.node,
                    source_player=srcpl,
                    hit_type='fireball',
                )
            )
            bs.getsound('tear_hit').play(position=self.node.position)
            self.handlemessage(bs.DieMessage())
        
        elif isinstance(msg, BounceMessage):
            bs.emitfx(
                position=self.node.position,
                chunk_type='ice',
                velocity=self.node.velocity,
                count=10,
                scale=0.7,
                spread=0.30,
            )
            self.handlemessage(bs.DieMessage())
            bs.getsound('tear_bonk').play(position=self.node.position)
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))

        else:
            return super().handlemessage(msg)

        return None