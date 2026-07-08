"""Parallax image class."""
from __future__ import annotations
from typing import override
import bascenev1 as bs

class ParallaxImage(bs.Actor):
    """Simple looping scrolling image."""
    def __init__(
        self,
        texture: bs.Texture,
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] = (100.0, 100.0),
        speed: tuple[float, float] = (-1.0, 0.0),
    ):
        super().__init__()
        self.position = position
        self.size = size
        self.speed = speed
        #  this is a tabbed indent
        # Main image.
        self.node1 = bs.newnode(
            'image',
            attrs={
                'texture': texture,
                'position': position,
                'scale': size,
            },
        )

        # Copy positioned right after it.
        self.node2 = bs.newnode(
            'image',
            attrs={
                'texture': texture,
                'position': (
                    position[0] + size[0],
                    position[1],
                ),
                'scale': size,
            },
        )
        self._update()
        self._timer = bs.Timer(
            0.016,
            bs.WeakCall(self._update),
            repeat=True,
        )

    def _update(self) -> None:
        if not self.node1 or not self.node2:
            self._timer = None
            return
        x_speed, y_speed = self.speed
        width, height = self.size

        for node in (self.node1, self.node2):
            x, y = node.position
            node.position = (x + x_speed, y + y_speed)

        # Horizontal wrap.
        if x_speed:
            if self.node1.position[0] <= self.node2.position[0]:
                left, right = self.node1, self.node2
            else:
                left, right = self.node2, self.node1

            if left.position[0] + width <= 0:
                left.position = (
                    right.position[0] + width,
                    left.position[1],
                )

        # Vertical wrap.
        if y_speed:
            if self.node1.position[1] <= self.node2.position[1]:
                bottom, top = self.node1, self.node2
            else:
                bottom, top = self.node2, self.node1

            if bottom.position[1] + height <= 0:
                bottom.position = (
                    bottom.position[0],
                    top.position[1] + height,
                )

    def delete(self) -> None:
        self.node1.delete()
        self.node2.delete()            

    @override
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            self.delete()
        else:
            return super().handlemessage(msg)
        return None
    
    @override
    def exists(self):
        return bool(self.node1)