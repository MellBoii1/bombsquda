"""WATERCOOOLERRRRR"""
from typing import override, Any
import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects

class WaterCoolerSpawner(bs.Actor):
    """ just stands there and despawns if not touched
    
    if it does get touched it spawns the regaulr guy
    """

    def __init__(self, position: tuple[float, float, float]):
        super().__init__()
        self.can_spawn = False
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': (position[0], position[1] + 1, position[2]),
                'mesh': bs.getmesh('tnt'),
                'body': 'puck',
                'color_texture': bs.gettexture('tnt'),
                'reflection': 'soft',
                'shadow_size': 0.5,
                'position': (0, 1, 0),
                'mesh_scale': 1.0,
                'gravity_scale': 1.5,
                'materials': [
                    SharedObjects.get().only_collide_with_floor_mat
                ],
            },
        )
        # ????
        self.node.position = (position[0], position[1] + 1, position[2])
        # The one and only chance to fight the water cooler this round
        self.getactivity().water_cooler_spawned = True
        bs.timer(1.6, self.allow_attacks)
        bs.timer(10, bs.Call(self.handlemessage, bs.DieMessage()))
       
    
    def allow_attacks(self):
        from bascenev1lib.actor.spazfactory import SpazFactory
        self.node.materials = []
        self.can_spawn = True
        

    def exists(self):
        return bool(self.node)
    
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            self.can_spawn = False
            if not self.exists():
                return
            if msg.immediate:
                self.node.delete()
            else:
                bs.animate(
                    self.node, 
                    attr='mesh_scale', 
                    keys={0: self.node.mesh_scale, 0.5: 0.0})
                bs.timer(0.5, self.node.delete)
        elif isinstance(msg, bs.HitMessage):
            if not self.exists():
                return
            # spawn the regular watercooler
            if self.can_spawn and self.node:
                WaterCooler(position=self.node.position).autoretain()
                self.handlemessage(bs.DieMessage(True))
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(True))
        return super().handlemessage(msg)

class WaterCooler(bs.Actor):
    """ deltarune water cooler"""
    
    def __init__(self, position: tuple[float, float, float]):
        super().__init__()
        self.hp = 1700 * (10)
        self.node = bs.Node(None)
        self._saved_music = bs.getmusic()
        bs.setmusic(getattr(bs.MusicType, 'WATERCOOLER'))
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': (position[0], position[1] + 0.5, position[2]),
                'mesh': bs.getmesh('tnt'),
                'body': 'puck',
                'color_texture': bs.gettexture('tnt'),
                'reflection': 'soft',
                'shadow_size': 0.5,
                'mesh_scale': 1.0,
                'gravity_scale': 1.5,
                'materials': [
                    SharedObjects.get().only_collide_with_floor_mat
                ],
            },
        )
    
    @override
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            if self._saved_music:
                bs.setmusic(self._saved_music)
                self._saved_music = None
            if self.node:
                self.node.delete()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        else:
            return super().handlemessage(msg)
        return None
    
    @override
    def exists(self):
        return bool(self.node)
    
    @override
    def is_alive(self):
        return self.hp > 0
