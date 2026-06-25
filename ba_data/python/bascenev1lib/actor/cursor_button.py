"""Module for a button cursors can interact with."""
from __future__ import annotations
from typing import Any, override

import bascenev1 as bs
from bascenev1lib.actor.cursor import (
    CursorClickedMessage, 
    CursorMovedMessage,
    Cursor,
)

class CursorButton(bs.Actor):
    """A button a cursor can click, on which
    then it'll callback its' on_activate method."""
    texture = 'buttonSquare'
    color = (0.5, 0.8, 0.5)
    
    def __init__(
        self, 
        position: tuple[float, float],
        size: tuple[float, float],
    ):
        super().__init__()
        self._size = size
        self._position = position
        self._connected_cursors: set[Cursor] = set()
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': bs.gettexture(self.texture),
                'scale': size,
                'position': position,
                'color': self.color,
            }
        )
        # Add us to the buttons.
        self.getactivity().cur_buttons.append(self)
    
    def _is_touching(self, origin_pos, target_pos, target_scale):
        ox, oy = origin_pos
        tx, ty = target_pos
        width, height = target_scale

        left = tx - width / 2
        right = tx + width / 2
        bottom = ty - height / 2
        top = ty + height / 2

        return left <= ox <= right and bottom <= oy <= top
    
    def on_activate(self, origin_cursor: Cursor, state: int):
        """Called when the button gets pressed 
        (and after it does its' visual logic).
        Override with your code."""
    
    def click_effect(self, position: tuple[float, float]):
        # Make a simple image node.
        node = bs.newnode(
            'image',
            delegate=self,
            owner=self.node,
            attrs={
                'texture': bs.gettexture('clickAnim1'),
                'scale': (30, 30),
                'position': position,
            }
        )
        # Make a texture sequence...
        intex = tuple(
            bs.gettexture('clickAnim' + str(i + 1)) 
            for i in range(6)
        )
        texture_sequence = bs.newnode(
            'texture_sequence',
            owner=node,
            attrs={'rate': 40, 'input_textures': intex},
        )
        # Connect it's texture to us
        texture_sequence.connectattr('output_texture', node, 'texture')
        bs.timer(0.24, node.delete)
    
    def get_hover_color(self):
        c0, c1, c2 = self.color
        extra = 0.2
        color = (
            c0 + extra, 
            c1 + extra, 
            c2 + extra
        )
        return color
    
    def _update_hover(self):
        # Visually make us brighter (or normal) so they know
        # we're currently being hovered (or not) by someone.
        if self._connected_cursors:
            self.node.color = self.get_hover_color()
        else:
            self.node.color = self.color
    
    def _on_press(self, msg: Any):
        self.on_activate(
            origin_cursor=msg.cursor,
            state=msg.state
        )
        # If state was to 'let go', don't play anything and just activate.
        # This should let us be able to handle holding presses.
        if msg.state == 0:
            return
        # Play sound.
        bs.getsound('deek2').play()
        self.click_effect(msg.position)
    
    @override
    def exists(self) -> bool:
        return bool(self.node)
    
    def handlemessage(self, msg: Any):
        if isinstance(msg, CursorMovedMessage):
            # Check whether contact is being done.
            contact = self._is_touching(
                origin_pos=msg.position, 
                target_pos=self._position, 
                target_scale=self._size,
            )
            # If contact was done and they're not connected to us,
            # connect them to us.
            if contact:
                if msg.cursor not in self._connected_cursors:
                    self._connected_cursors.add(msg.cursor)
            # Otherwise, and if they already were,
            # disconnect them from us.
            else:
                if msg.cursor in self._connected_cursors:
                    self._connected_cursors.discard(msg.cursor)
            self._update_hover()
            
        elif isinstance(msg, CursorClickedMessage):
            # Don't activate if they're not in us.
            if msg.cursor not in self._connected_cursors:
                return
            self._on_press(msg)
        elif isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
            # Clean up everything.
            self._connected_cursors.clear()
            if self in self.getactivity().cur_buttons:
                self.getactivity().cur_buttons.remove(self)
        else:
            return super().handlemessage(msg)
        return None
            
        