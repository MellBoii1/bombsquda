"""A toaster that toastes spazzes."""
from typing import override, Any
from bascenev1lib.gameutils import SharedObjects, TouchedMessage
from bascenev1lib.actor.spaz import Spaz
import bascenev1 as bs
import random

class Toaster(bs.Actor):
    """Toast TOAST!"""
    def __init__(self, position: tuple):
        super().__init__()
        self._area_scale = 3.3
        shared = SharedObjects.get()
        self._can_hurt_spazzes = False
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'body_scale': 0.9,
                'mesh': bs.getmesh('box'),
                'color_texture': bs.gettexture('white'),
                'position': position,
                'materials': [shared.object_material],
            }
        )
        self.area_node = bs.newnode(
            'locator',
            owner=self.node,
            attrs={
                'shape': 'circle',
                'opacity': 0.7,
                'additive': True,
                'draw_beauty': False,
                'size': [0],
            },
        )
        mnode = bs.newnode(
            'math',
            owner=self.node,
            attrs={'input1': (0, -0.7, 0), 'operation': 'add'},
        )
        self.node.connectattr('position', mnode, 'input2')
        self.region = bs.newnode(
            'region',
            delegate=self,
            owner=self.node,
            attrs={
                'scale': (self._area_scale, 5, self._area_scale),
                'type': 'box',
                'materials': [
                    shared.region_material_physical,
                ],
            },
        )
        mnode.connectattr('output', self.region, 'position')
        # connect area to us
        self.node.connectattr(
            'position', 
            self.area_node, 
            'position'
        )
        # animations
        bs.animate(
            self.node,
            'mesh_scale',
            {
                0: 0,
                0.3: 1.3,
                0.5: 0.7,
            }
        )
        bs.animate_array(
            self.area_node,
            'color', 3,
            {
                0: (0, 0.3, 0.9),
                0.1: (0.1, 0.5, 1.2),
                0.2: (0, 0.3, 0.9),
            },
            loop=True
        )
        # schedules
        self._update_timer = bs.Timer(0.11, self._update_hits, repeat=True)
        self._start_timer = bs.Timer(1.7, self._start_zap_area)
        self._death_timer = bs.Timer(
            7, 
            bs.WeakCall(self.handlemessage, bs.DieMessage())
        )
        self._connected_actors = []
    
    def _start_zap_area(self):
        if not self.node:
            return
        # let us hurt other people
        self._can_hurt_spazzes = True
        # animate in
        bs.animate_array(
            self.area_node,
            'size', 1,
            {
                0: [0,],
                0.05: [self._area_scale + 1.4,],
            }
        )
    
    def _update_hits(self):
        if not self.node:
            self._update_timer = None
            return
        # randomly emit sparks
        if (
            random.random() < 0.73
            and self._can_hurt_spazzes
        ):
            ourpos = self.node.position
            spread = self._area_scale
            pos = (
                ourpos[0] + random.uniform(-spread, spread),
                ourpos[1],
                ourpos[2] + random.uniform(-spread, spread),
            )
            bs.emitfx(
                position=pos,
                velocity=(0, 0, 0),
                count=5,
                scale=1.1,
                spread=0.7,
                chunk_type='spark',
            )
        if (
            random.random() < 0.67
            and self._can_hurt_spazzes
        ):
            ourpos = self.node.position
            spread = self._area_scale
            pos = (
                ourpos[0] + random.uniform(-spread, spread),
                ourpos[1],
                ourpos[2] + random.uniform(-spread, spread),
            )
            bs.emitfx(
                position=pos,
                velocity=(0, 0, 0),
                count=4,
                spread=0.2,
                scale=0.5,
                chunk_type='ice',
            )
        # if we shouldn't be hurting guys, then don't
        if not self._can_hurt_spazzes:
            return
        for actor in self._connected_actors:
            if (
                not actor 
                or not actor.node
                or not actor.is_alive()
            ):
                continue
            plpt = bs.Vec3(actor.node.position)
            ourpt = bs.Vec3(self.node.position)
            dist = (plpt - ourpt).length()
            if dist > self._area_scale - 0.4:
                self._connected_actors.remove(actor)
                continue
            # give em a hit
            actor.handlemessage(
                bs.HitMessage(
                    pos=self.node.position,
                    velocity=(0, 0, 0),
                    magnitude=20,
                    radius=0,
                    srcnode=self.node,
                )
            )
    
    @override
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            self._can_hurt_spazzes = False
            if msg.immediate:
                if self.node:
                    self.node.delete()
            else:
                if self.node:
                    bs.animate_array(
                        self.area_node,
                        'size', 1,
                        {
                            0: [self._area_scale + 1.4,],
                            0.2: [0,],
                        }
                    )
                    bs.animate(
                        self.node,
                        'mesh_scale',
                        {
                            0: 0.7,
                            0.2: 0,
                        }
                    )
                    bs.timer(0.2, self.node.delete)
        if isinstance(msg, TouchedMessage):
            if not self.node:
                return
            node = bs.getcollision().opposingnode
            actor = node.getdelegate(Spaz)
            if (
                not actor
                or not node
            ):
                return
            if actor not in self._connected_actors:
                self._connected_actors.append(actor)
        else:
            return super().handlemessage(msg)
        return None
    
    @override
    def exists(self) -> bool:
        return bool(self.node)

    