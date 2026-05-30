"""A multitude of hand-made particles, including a template for one."""
import bascenev1 as bs
import random
from bascenev1lib.gameutils import SharedObjects, FootingMessage, TouchedMessage
from typing import Any, Sequence, override

class ParticleActor(bs.Actor):
    """Base class for a particle."""
    node: bs.Node
    def __init__(self, 
                 mesh: bs.Mesh,
                 texture: bs.Texture,
                 position: Sequence[float],
                 body_scale: int = 0.5,
                 mesh_scale: int = 0.5,
                 reflection: int = 0.6,
                 body_type: str = 'sphere',
    ):
        """
        Initialize a particle actor with physics properties and visual representation.
        Args:
            position: The 3D coordinates where the particle spawns.
            body_scale: The scale factor for the physics body. Defaults to 0.5.
            mesh_scale: The scale factor for the mesh geometry. Defaults to 0.5.
            mesh: The mesh object to use for rendering. Defaults to 'bomb' mesh.
            texture: The texture to apply to the particle. Defaults to 'white' texture.
            body_type: The body type of the particle. Defaults to 'sphere'.
        Attributes:
            material: Custom material with footing interaction handling.
            mesh: The mesh used for rendering.
            tex: The texture applied to the particle.
            bscale: The body scale value.
            mscale: The mesh scale value.
            spawn_pos: The spawn position coordinates.
            node: The physics/render node representing the particle.
            dead: Boolean flag indicating if the particle is dead.
        """
        super().__init__()
        # mats
        shared = SharedObjects.get()
        obj_mat = shared.object_material
        # Footing material is not used by us; It is only here
        # so it can be handled by another actor.
        footing_material = shared.footing_material
        region_material = shared.region_material
        self.material = bs.Material()
        # node
        self.mesh = mesh
        self.tex = texture
        self.bscale = body_scale
        self.mscale = mesh_scale
        self.spawn_pos = position
        self.body = body_type
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': self.body,
                'body_scale': self.bscale,
                'mesh_scale': self.mscale,
                'position': self.spawn_pos,
                'mesh': self.mesh,
                'light_mesh': self.mesh,
                'shadow_size': self.bscale - 0.1,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [reflection],
                'materials': (shared.particle_material, obj_mat),
            },
        )
        bs.animate(
            self.node,
            'mesh_scale',
            {0: 0, 0.2: self.mscale},
        )
        self.dead = False

    @override
    def is_alive(self) -> bool:
        """Simply returns if we dead or nah."""
        return not self.dead
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        """Message handler"""
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if not self.node or not self.is_alive():
                return
            if msg.immediate:
                self.node.delete()
            else:
                bs.animate(self.node, 'mesh_scale', {0: self.mscale, 0.1: 0})
                bs.timer(0.1, self.node.delete)
            self.dead = True

        elif isinstance(msg, bs.OutOfBoundsMessage):
            if not self.node:
                return
            self.handlemessage(bs.DieMessage(immediate=True))
        else:
            return super().handlemessage(msg)
        return None

    def die(self, immediate: bool = False):
        """Kills us. Simple."""
        self.handlemessage(bs.DieMessage(immediate=immediate))

class BloodParticle(ParticleActor):
    """A blood particle."""
    def __init__(self, position: Sequence[float], spaz_type: str):
        texture = (
            'oil' 
            if spaz_type == 'robot' 
            else 'blood'
        )
        self.color = (
            (0.1, 0.1, 0.1) 
            if spaz_type == 'robot' else 
            (1.2, 0.1, 0.1)
        )
        super().__init__(
            position=position,
            texture=bs.gettexture(texture),
            mesh=bs.getmesh('bomb'),
            body_scale=0.4,
            mesh_scale=0.4
        )
    def make_scorch(self):
        """Makes a scorch."""
        pos = self.node.position
        scorch = bs.newnode(
            'scorch',
            attrs={
                'position': pos,
                'size': self.bscale,
            },
        )
        scorch.color = self.color
        bs.animate(scorch, 'presence', {3: self.bscale, 7: 0})
        bs.timer(13.0, scorch.delete)

    @override
    def handlemessage(self, msg: Any) -> Any:
        """Message handler"""
        assert not self.expired
        if isinstance(msg, FootingMessage):
            pos = self.node.position
            self.make_scorch()
            bs.getsound('bdrip').play(position=pos)
            self.die()
        else:
            return super().handlemessage(msg)
        return None

class ConfettiParticle(ParticleActor):
    """Confetti particles! Usually a replacement for blood."""
    def __init__(self, position: Sequence[float], spaz_type: str):
        # delete spaz type (unused)
        del spaz_type
        # Choose between a random color
        # tex before we initiate
        choices = [
            'red', 'blue',
            'green', 'yellow', 
            'orange', 'purple',
        ]
        choice = random.choice(choices)
        full_str = 'confetti_colors/' + choice
        chosentex = bs.gettexture(full_str)
        super().__init__(
            position=position,
            texture=chosentex,
            mesh=bs.getmesh('shrapnel1'),
            body_scale=0.4,
            mesh_scale=0.2,
        )
        self.scheduling = False

    def schedule_death(self, time: int = 5.0):
        """Schedule a time where we will die."""
        if self.scheduling or not self.node:
            return
        self.scheduling = True
        self.deathTimer = bs.Timer(time, self.die)

    @override
    def handlemessage(self, msg: Any) -> Any:
        """Message handler"""
        assert not self.expired
        if isinstance(msg, FootingMessage):
            self.schedule_death()
        else:
            return super().handlemessage(msg)
        return None

class SparkParticle(ParticleActor):
    """
    Particle for a spark-ish... particle.
    Used usually for super periodically.
    """
    def __init__(self, position: Sequence[float]):
        tex = 'confetti_colors/yellow'
        super().__init__(
            position=position,
            texture=bs.gettexture(tex),
            mesh=bs.getmesh('flash'),
            body_scale=0.2,
            mesh_scale=0.2,
            reflection=1.4
        )
        self.scheduling = False

    def schedule_death(self, time: int = 1.0):
        """Schedule a time where we will die."""
        if self.scheduling or not self.node:
            return
        self.scheduling = True
        self.deathTimer = bs.Timer(time, self.die)

    @override
    def handlemessage(self, msg: Any) -> Any:
        """Message handler"""
        assert not self.expired
        if isinstance(msg, FootingMessage):
            self.schedule_death()
        else:
            return super().handlemessage(msg)
        return None
   

class BloodRaindrop(bs.Actor):
    """bloody-red raindrops used by sorrow. can put out 
    bombs and will make a red scorch where it lands"""
    def __init__(self, position: Sequence[float]):
        super().__init__()
        # mats
        shared = SharedObjects.get()
        obj_mat = shared.object_material
        # Footing material is not used by us; It is only here
        # so it can be handled by another actor.
        footing_material = shared.footing_material
        object_material = shared.object_material
        region_material = shared.region_material
        self.material = shared.sorrowful_material
        # node
        self.mesh = bs.getmesh('bomb')
        self.tex = bs.gettexture('blood')
        self.bscale = 0.5
        self.mscale = 0.5
        self.spawn_pos = position
        self.body = 'sphere'
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': self.body,
                'body_scale': self.bscale,
                'mesh_scale': self.mscale,
                'position': self.spawn_pos,
                'mesh': self.mesh,
                'light_mesh': self.mesh,
                'shadow_size': self.bscale - 0.1,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [0.6],
                'materials': (self.material, obj_mat),
            },
        )
        bs.animate(
            self.node,
            'mesh_scale',
            {0: 0, 0.1: self.mscale},
        )
        self.dead = False

    @override
    def is_alive(self) -> bool:
        """check if we're alive. simple."""
        return not self.dead
    
    def die(self, immediate: bool = False):
        """shortcut to call diemessage, where we die"""
        self.handlemessage(bs.DieMessage(immediate=immediate))
        
    def make_scorch(self):
        """taint the ground of whereever we go..."""
        pos = self.node.position
        antimulti = 0.9
        scorch = bs.newnode(
            'scorch',
            attrs={
                'position': pos,
                'size': self.bscale * antimulti,
            },
        )
        scorch.color = (1.3, 0, 0)
        bs.animate(scorch, 'presence', {3: self.bscale * antimulti, 5: 0})
        bs.timer(5.0, scorch.delete)

    @override
    def handlemessage(self, msg: Any) -> Any:
        """Message handler"""
        assert not self.expired
        if isinstance(msg, FootingMessage):
            pos = self.node.position
            self.make_scorch()
            bs.getsound('bdrip').play(position=pos)
            self.die()
        elif isinstance(msg, TouchedMessage):
            from bascenev1lib.actor.bomb import Bomb
            toucher = bs.getcollision().opposingnode
            actor = toucher.getdelegate(Bomb)
            if (
                not toucher
                or not actor
            ):
                return
            # the drops of sorrow wither away a explosive device's will to explode...
            # basically, defuse any bombs we come in contact with.
            actor.defuse() 
            self.die()
        elif isinstance(msg, bs.DieMessage):
            if not self.node or not self.is_alive():
                return
            if msg.immediate:
                self.node.delete()
            else:
                bs.animate(self.node, 'mesh_scale', {0: self.mscale, 0.1: 0})
                bs.timer(0.1, self.node.delete)
            self.dead = True
        elif isinstance(msg, bs.OutOfBoundsMessage):
            if not self.node:
                return
            self.handlemessage(bs.DieMessage(immediate=True))
        else:
            return super().handlemessage(msg)
        return None