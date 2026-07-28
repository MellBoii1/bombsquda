"""We are so back"""
from __future__ import annotations
from typing import Any, override
from dataclasses import dataclass

import bascenev1 as bs
import mellboii.mell_resources as mell
import bauiv1 as bui

@dataclass
class CursorClickedMessage:
    """A message that tells a cursor
    has clicked a certain position."""
    #: The cursor that clicked.
    cursor: Cursor
    #: The position the cursor clicked.
    position: tuple[float, float]
    #: The click state (0-1).
    state: int

@dataclass
class CursorMovedMessage:
    """A message that tells a cursor
    has moved to positions."""
    #: The cursor that clicked.
    cursor: Cursor
    #: The position the cursor clicked.
    position: tuple[float, float]

class Cursor(bs.Actor):
    """A on-screen cursor that a player
    can control. Sends messages when moving and clicking."""
    def __init__(self, source_player: bs.Player):
        super().__init__()
        self._player: bs.Player = source_player
        self._connected_to_player: bs.Player | None = None
        self._up_down_timer: bs.Timer | None = None
        self._left_right_timer: bs.Timer | None = None
        self._default_move_multiplier = self._move_multiplier = 3
        self._default_timer_speed = self._timer_speed = 0.01
        self._last_stick_x: int = 0
        self._last_stick_y: int = 0
        icon = self._player.get_icon() or {}
        scale = self._scale = 0.9
        pos = (0, 0)
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': bs.gettexture('pcursor'),
                'tint_texture': bs.gettexture('pcursorCM'),
                'tint_color': icon.get('tint_color'),
                'tint2_color': icon.get('tint2_color'),
                'scale': (64 * scale, 64 * scale),
                'position': pos,
                'front': True,
            }
        )
        mathnode = bs.newnode(
            'math',
            owner=self.node,
            attrs={'input1': (4 * scale, -4 * scale), 'operation': 'add'},
        )
        self.node.connectattr('position', mathnode, 'input2')
        self.plr_icon = bs.newnode(
            'image',
            delegate=self,
            owner=self.node,
            attrs={
                'texture': icon.get('texture'),
                'tint_texture': icon.get('tint_texture'),
                'tint_color': icon.get('tint_color'),
                'tint2_color': icon.get('tint2_color'),
                'mask_texture': bs.gettexture('circleMask'),
                'scale': (36 * scale, 36 * scale),
                'position': pos,
                'front': True,
            }
        )
        mathnode.connectattr('output', self.plr_icon, 'position')
    
    def get_point_pos(self):
        """Gets the position of the tip of our pointer."""
        px, py = self.node.position
        result = (
            px + (-25 * self._scale), 
            py + (25 * self._scale)
        )
        return result
    
    def _move(self, x: float, y: float):
        if not self.node:
            return
        px, py = self.node.position
        screen_size = bui.get_virtual_safe_area_size()
        screen_size = (
            screen_size[0] * 0.5, 
            screen_size[1] * 0.5,
        )
        tx = mell.clamp(px + x, -screen_size[0], screen_size[0])
        ty = mell.clamp(py + y, -screen_size[1], screen_size[1])
        self.node.position = (tx, ty)
        self.getactivity().handlemessage(
            CursorMovedMessage(self, self.get_point_pos())
        )
        
    def run(self, value: int):
        """Speeds up (or defaults) the cursor."""
        if value == 1:
            self._move_multiplier = self._default_move_multiplier * 2
        else:
            self._move_multiplier = self._default_move_multiplier
        # Just in case, re-call left-right-up-down
        # with last x-y values so we don't need to press em again
        self.left_right(self._last_stick_x)
        self.up_down(self._last_stick_y)
    
    def left_right(self, value: int):
        """Moves the cursor in a left-right direction."""
        self._last_stick_x = value
        value *= self._move_multiplier
        
        self._left_right_timer = bs.Timer(
            self._timer_speed,
            bs.Call(self._move, value, 0),
            repeat=True,
        )

    def up_down(self, value: int):
        """Moves the cursor in a up-down direction."""
        self._last_stick_y = value
        value *= self._move_multiplier
        self._up_down_timer = bs.Timer(
            self._timer_speed,
            bs.Call(self._move, 0, value),
            repeat=True,
        )
    
    def click(self, value: int):
        if not self.node:
            return
        self.getactivity().handlemessage(
            CursorClickedMessage(self, self.get_point_pos(), value)
        )
    
    def connect_controls(self):
        """Connects the Cursor's player's input."""
        player = self._player
        if self._connected_to_player:
            if player != self._connected_to_player:
                player.resetinput()
            self.disconnect_controls()
        else:
            player.resetinput()
        player.assigninput(bs.InputType.UP_DOWN, self.up_down)
        player.assigninput(bs.InputType.LEFT_RIGHT, self.left_right)
        player.assigninput(bs.InputType.RUN, self.run)
        player.assigninput(bs.InputType.JUMP_PRESS, bs.WeakCall(self.click, 1))
        player.assigninput(bs.InputType.JUMP_RELEASE, bs.WeakCall(self.click, 0))
        self._connected_to_player = player
    
    def disconnect_controls(self) -> None:
        """Completely sever any previously connected
        bascenev1.Player from control of the cursor."""
        if self._connected_to_player:
            self._connected_to_player.resetinput()
            self._connected_to_player = None

            # Send releases for anything in case its held.
            self.run(0)
            self.up_down(0)
            self.left_right(0)
            self.click(0)
        else:
            print(
                'WARNING: disconnect_controls() called for'
                ' non-connected player'
            )
    
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
            self.disconnect_controls()
        else:
            return super().handlemessage(msg)
        return None