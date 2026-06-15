"""Module for a :class:bascenev1lib.actor.PlayerSpaz:class:'s HP meter."""
from typing import override, Any
import bascenev1 as bs
import random
import math

class EarthboundMeter(bs.Actor):
    """Handles the full EarthBound-style meter UI for a spaz."""
    @override
    def exists(self) -> bool:
        return bool(self.meter)
    
    @override
    def on_expire(self):
        super().on_expire()
        self.spaz = None
        
    def __init__(
        self,
        spaz: Any,
        portrait_texture: bs.Texture,
        lose_texture: bs.Texture,
        scale: float = 1.0,
    ):
        super().__init__()

        self.spaz = spaz
        self.scale = scale
        self.portrait_texture = portrait_texture
        self.lose_texture = lose_texture
        
        self.x = -9999
        self.y = -9999
        self.did_death_anim = False

        self._create_nodes()
        self.refresh()

    def _get_position(self) -> tuple[float, float]:
        source_player = self.spaz.source_player

        if not source_player:
            return (-9999, -9999)

        players = bs.getplayers()

        if source_player not in players:
            return (-9999, -9999)

        index = players.index(source_player)

        normal_x = -670
        spacing = 150 * self.scale
        default_y = -270

        return (
            normal_x + spacing * (index + 1),
            default_y,
        )

    def refresh_position(self) -> None:
        self.x, self.y = self._get_position()

        positions = {
            self.char: (self.x, self.y),
            self.meter: (self.x, self.y),

            self.name_text: (
                self.x,
                self.y + (50 * self.scale),
            ),

            self.hp_text: (
                self.x + (18 * self.scale),
                self.y - (16 * self.scale),
            ),

            self.sp_text: (
                self.x + (18 * self.scale),
                self.y - (53 * self.scale),
            ),
        }

        for node, pos in positions.items():
            if node and node.exists():
                node.position = pos

    def _create_nodes(self) -> None:
        self.x, self.y = self._get_position()

        self.char = bs.newnode(
            'image',
            attrs={
                'texture': self.portrait_texture,
                'absolute_scale': True,
                'position': (self.x, self.y),
                'attach': 'center',
                'opacity': 1.0,
                'scale': (
                    100 * self.scale,
                    100 * self.scale,
                ),
                'color': (1, 1, 1),
            },
        )

        self.meter = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('earthmeter'),
                'tint_texture': bs.gettexture('earthmeterCM'),
                'absolute_scale': True,
                'position': (self.x, self.y),
                'attach': 'center',
                'opacity': 1.0,
                'scale': (
                    150 * self.scale,
                    150 * self.scale,
                ),
                'color': (1, 1, 1),
            },
        )

        self.name_text = bs.newnode(
            'text',
            attrs={
                'text': self.spaz.node.name,
                'h_align': 'center',
                'v_align': 'top',
                'position': (
                    self.x,
                    self.y + (50 * self.scale),
                ),
                'scale': 0.9 * self.scale,
                'maxwidth': 100 * self.scale,
                'color': (1, 1, 1),
                'shadow': 0.7,
                'flatness': 0.6,
            },
        )

        self.hp_text = bs.newnode(
            'text',
            attrs={
                'text': '',
                'h_align': 'center',
                'position': (
                    self.x + (18 * self.scale),
                    self.y - (16 * self.scale),
                ),
                'scale': 0.9 * self.scale,
                'color': (1, 1, 1),
                'shadow': 0.7,
                'flatness': 0.6,
            },
        )

        self.sp_text = bs.newnode(
            'text',
            attrs={
                'text': '',
                'h_align': 'center',
                'position': (
                    self.x + (18 * self.scale),
                    self.y - (53 * self.scale),
                ),
                'scale': 0.9 * self.scale,
                'color': (1, 1, 1),
                'shadow': 0.7,
                'flatness': 0.6,
            },
        )

    def refresh(self) -> None:
        spaz = self.spaz

        if not self.meter or not self.meter.exists():
            return

        self.refresh_position()

        # HP
        if self.hp_text and self.hp_text.exists():
            self.hp_text.text = str(int(spaz.hitpoints / 10))

        # Shield
        if self.sp_text and self.sp_text.exists():

            if spaz.shield:
                self.sp_text.opacity = 1.0
                self.sp_text.text = str(
                    int(spaz.shield_hitpoints / 10)
                )
            else:
                self.sp_text.opacity = 0.0

        # Determine colors
        low_hp = spaz.hitpoints <= 250
        is_super = spaz.issuper

        if low_hp:
            tint1 = (0.8, 0.2, 0.3)
            tint2 = (0.9, 0.5, 0.5)
            text_color = tint2

        elif is_super:
            tint1 = (0.8, 0.7, 0.2)
            tint2 = (1.0, 0.9, 0.4)
            text_color = tint2

        else:
            tint1 = spaz._saved_color
            tint2 = spaz._saved_highlight
            text_color = tint1

        # Meter colors
        if self.meter.exists():
            self.meter.tint_color = bs.safecolor(tint1)
            self.meter.tint2_color = bs.safecolor(tint2)

        # Text colors
        for node in (self.hp_text, self.sp_text):
            if node and node.exists():
                node.color = bs.safecolor(text_color)

    def play_death_animation(self) -> None:
        from bascenev1lib.actor.nodejumper import ImageJumper

        if self.did_death_anim:
            return

        self.did_death_anim = True
        
        # for every node, make them jump
        for node in (
            self.char,
            self.meter,
            self.name_text,
            self.sp_text,
        ):
            if node and node.exists():
                ImageJumper.jump_image(
                    node,
                    220,
                    230,
                    -1500,
                )

        if self.char and self.char.exists():
            self.char.texture = self.lose_texture

        if self.hp_text and self.hp_text.exists():
            self.hp_text.delete()

    def delete(self) -> None:
        for node in (
            self.char,
            self.meter,
            self.name_text,
            self.hp_text,
            self.sp_text,
        ):
            if node and node.exists():
                node.delete()
    
    def popup_char(self):
        if not self.char or self.did_death_anim:
            return
        bs.animate_array(
            self.char,
            "position",
            2,
            {
                0.0: (self.x, self.y),
                0.5: (self.x, self.y + 90),
                1.5: (self.x, self.y + 90),
                2.5: (self.x, self.y),
            },
        )
    
    @override
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            self.delete()
        else:
            super().handlemessage(msg)