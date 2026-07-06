"""Proceed"""
from typing import override, Any
from bascenev1lib.actor.bomb import Blast
import bascenev1 as bs
import random

class Snowgrave(bs.Actor):
    def __init__(
        self, 
        position: tuple[float, float, float]
    ):
        super().__init__()
        self._grave_sound = bs.getsound('snowgrave')
        self.node = bs.newnode(
            'light',
            attrs={
                'position': position,
                'color': (0, 0.6, 0.9),
                'intensity': 0,
            },
        )
        self.sound = bs.newnode(
            'sound',
            owner=self.node,
            attrs={
                'sound': bs.getsound('snow_loop'),
                'volume': 0.3,
                'position': self.node.position,
            }
        )
        bs.animate(
            self.sound, 
            'volume',
            {
                0: 0.3,
                3: 1.1,
            }
        )
        bs.animate(
            self.node, 
            'radius',
            {
                0: 0,
                4.5: 0.6,
            }
        )
        bs.animate_array(
            self.node,
            'color',
            3,
            {
                0: (0, 0, 0),
                4.9: (0, 0.6, 0.9),
            }
        )
        bs.animate(
            self.node, 
            'intensity',
            {
                0: 0.0,
                4.8: 1.2,
            },
        )
        bs.timer(5, self._start)
    
    
    def _start(self):
        bs.animate(
            self.node, 
            'intensity',
            {
                0: 1.3,
                0.1: 0,
            },
        )
        bs.animate_array(
            self.node,
            'color', 3,
            {
                0: (0, 0.6, 0.9),
                0.05: (0.8, 0.9, 1),
            }
        )
        self._grave_sound.play(
            position=self.node.position
        )
        self.sound.volume = 0
        self.sound.delete()

        def start():
            for step in range(540):
                pos = self.node.position
                spread = 0.5

                bpos = (
                    pos[0] + random.uniform(-spread, spread),
                    pos[1] + random.uniform(-2, 7),
                    pos[2] + random.uniform(-spread, spread),
                )

                def spawn(pos=bpos):
                    Blast(
                        position=pos,
                        velocity=(0, 0.1, 0),
                        blast_type='ice',
                        hit_subtype='snowgrave',
                        blast_radius=1.7,
                        nosound=True,
                    ).autoretain()
                bs.timer(step * 0.004, spawn)
        bs.timer(0.1, start)
    
    @override
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
        else:
            return super().handlemessage(msg)
        return None
    
    @override
    def exists(self):
        return bool(self.node)
	