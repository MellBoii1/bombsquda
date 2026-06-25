"""'UI' for modifier voting."""
from __future__ import annotations
from typing import Any, override

import bascenev1 as bs
import random
from bascenev1lib.modifiers.ingame import REGISTERED_MODS, Modifier
from bascenev1lib.actor.cursor_button import CursorButton

class ModifierVoteButton(bs.Actor):
    """A button for a modifier vote... button."""
    def __init__(
        self, 
        modifier: Modifier, 
        delegate: ModifierVoteDelegate,
        position: tuple[float, float],
    ):
        super().__init__()
        self._delegate = delegate
        self._modifier = modifier
        self._pos = position
        self._vote_img_nodes = []
        
        btn = self._button = CursorButton(
            position=(position[0] + 20, position[1]), 
            size=(500, 110),
        )
        btn.node.opacity = 0
        btn.on_activate = self._voted
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': bs.gettexture('modifierBtn1'),
                'scale': (160, 110),
                'position': (position[0] - 500, position[1]),
                'color': (0, 0, 0),
            }
        )
        intex = tuple(
            bs.gettexture('modifierBtn' + str(i + 1)) 
            for i in range(4)
        )
        texture_sequence = bs.newnode(
            'texture_sequence',
            owner=self.node,
            attrs={'rate': 130, 'input_textures': intex},
        )
        # Connect it's texture to us
        texture_sequence.connectattr('output_texture', self.node, 'texture')
        self.title = bs.newnode(
            'text',
            delegate=self,
            owner=self.node,
            attrs={
                'text': self._modifier.name,
                'position': (position[0] - 250, position[1] + 20),
                'maxwidth': 250,
                'shadow': 0.8,
                'front': True,
            }
        )
        self.description = bs.newnode(
            'text',
            delegate=self,
            owner=self.node,
            attrs={
                'text': self._modifier.description,
                'position': (position[0] - 400, position[1] + 5),
                'color': (0.9, 0.9, 0.9),
                'maxwidth': 400,
                'scale': 0.7,
                'flatness': 0.8,
                'front': True,
            }
        )
        self.oneliner = bs.newnode(
            'text',
            delegate=self,
            owner=self.node,
            attrs={
                'text': self._modifier.oneliner,
                'position': (position[0] - 400, position[1]),
                'color': (0.8, 0.8, 0.8),
                'maxwidth': 400,
                'scale': 0.7,
                'flatness': 0.8,
                'front': True,
            }
        )
        mathnode = bs.newnode(
            'math',
            owner=self.node,
            attrs={'input1': (50, 0), 'operation': 'add'},
        )
        self.node.connectattr('position', mathnode, 'input2')
        self.icon = bs.newnode(
            'image',
            delegate=self,
            owner=self.node,
            attrs={
                'texture': bs.gettexture(self._modifier.icon),
                'scale': (70, 70),
                'position': (position[0] - 500, position[1]),
                'front': True,
            }
        )
        mathnode.connectattr('output', self.icon, 'position')
        bs.animate_array(
            self.node, 
            'position', 
            2,
            {
                0: (position[0] - 400, position[1]),
                0.5: (position[0] - 140, position[1]),
            }
        )
        bs.animate_array(
            self.title, 
            'position', 
            2,
            {
                0: (position[0] - 700, position[1] + 20),
                0.5: (position[0] - 40, position[1] + 20),
            }
        )
        bs.animate_array(
            self.description, 
            'position', 
            2,
            {
                0: (position[0] - 700, position[1] + 3),
                0.5: (position[0] - 30, position[1] + 3),
            }
        )
        bs.animate_array(
            self.oneliner, 
            'position', 
            2,
            {
                0: (position[0] - 700, position[1] - 15),
                0.5: (position[0] - 30, position[1] - 15),
            }
        )
        self._emit_timer = bs.Timer(0.1, self._emit_bubbles, repeat=True)
    
    def _update_display(self):
        this_votes = self._delegate._modifier_votes.get(self._modifier)
        px, py = self._pos
        # this means the value is OVER 0.
        if this_votes:
            self.node.color = (1, 1, 0)
            self.node.position = (px - 130, py)
        else:
            self.node.color = (0, 0, 0)
            self.node.position = (px - 140, py)
        ix = px + 10
        iy = py - 30
        for node in self._vote_img_nodes:
            if node:
                node.delete()
        for player in this_votes:
            icon = player.get_icon() or {}
            node = bs.newnode(
                'image',
                delegate=self,
                owner=self.node,
                attrs={
                    'texture': icon.get('texture'),
                    'tint_texture': icon.get('tint_texture'),
                    'tint_color': icon.get('tint_color'),
                    'tint2_color': icon.get('tint2_color'),
                    'mask_texture': bs.gettexture('characterIconMask'),
                    'scale': (32, 32),
                    'position': (ix, iy),
                }
            )
            self._vote_img_nodes.append(node)
            ix += 35
    
    def _emit_bubbles(self):
        if not self.node:
            if self._emit_timer:
                self._emit_timer = None
            return
        # emit some nice lookin bubbles randomly...
        this_votes = self._delegate._modifier_votes.get(self._modifier)
        # Don't do anything if we have no votes
        # if not this_votes:
            # return
        # Don't do anything based on chance
        if random.random() > 0.9:
            return
        position = self._pos
        # node,,,
        node = bs.newnode(
            'image',
            delegate=self,
            owner=self.node,
            attrs={
                'texture': bs.gettexture('modifierBubble1'),
                'scale': (20, 20),
                'position': (position[0] - 500, position[1]),
                'color': self.node.color,
                'premultiplied': True,
            }
        )
        num = 36
        yoffs = random.uniform(-num, num)
        bs.animate_array(
            node, 
            'position', 
            2,
            {
                0: (position[0] - 90, position[1] + yoffs),
                4: (position[0] - 10, position[1] + yoffs),
            }
        )
        def out():
            if not node:
                return
            bs.animate_array(node, 'scale', 2, {
                0: (20, 20), 
                1: (0, 0),
            })
            bs.timer(1, node.delete)
        bs.timer(3, out)
        intex = tuple(
            bs.gettexture('modifierBubble' + str(i + 1)) 
            for i in range(4)
        )
        # Texture sequence,,,,
        texture_sequence = bs.newnode(
            'texture_sequence',
            owner=node,
            attrs={'rate': 80, 'input_textures': intex},
        )
        # Connect it's texture to us
        texture_sequence.connectattr('output_texture', node, 'texture')
    
    def _voted(
        self, 
        origin_cursor: bs.Actor, 
        state: int
    ):
        # Don't change if state is 'letting-go'.
        if not state:
            return
        player = origin_cursor._player
        this_votes = self._delegate._modifier_votes.get(self._modifier)
        # If player didn't vote for this modifier,
        # add them. Otherwise, remove them.
        if player not in this_votes:
            this_votes.append(player)
        else:
            this_votes.remove(player)
        # If player voted for something else,
        # remove that vote.  
        for key in self._delegate._modifier_votes.keys():
            other = self._delegate._modifier_votes[key]
            if player in other and other is not this_votes:
                other.remove(player)
        self._delegate.update_buttons()
    
    def on_expire(self):
        self.handlemessage(bs.DieMessage())
    
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
            # Let go of our delegate and
            # modifier, so we don't end up with
            # lingering strong refs.
            self._delegate = None
            self._modifier = None
            if self._button:
                self._button.on_activate = None
                self._button.handlemessage(bs.DieMessage())
            self._button = None
        else:
            return super().handlemessage(msg)
        return None
        

class ModifierVoteDelegate(bs.Actor):
    """Handles the 'UI' for voting for modifiers.
    Why's it called a delegate?
     Haha... ha...
      ..I HAVE NO IDEA!!!"""
    def __init__(self):
        super().__init__()
        maximum = 3
        x = -500
        y = 100
        # This is mostly a 'dummy' node, just so
        # we know whether we exist.
        self.node = bs.newnode(
            'math',
            delegate=self,
        )
        self._modifier_votes = {}
        self._buttons = []
        
        for i in range(maximum):
            # get a random modifier that
            # already wasn't added
            try:
                modifier = random.choice(
                    list(
                        mod for mod in REGISTERED_MODS 
                        if mod not in self._modifier_votes
                    )
                )
            # index error means list was empty; we just stop.
            except IndexError:
                modifier = None
            if not modifier:
                return
            self._modifier_votes[modifier] = []
            btn = ModifierVoteButton(
                modifier=modifier,
                delegate=self,
                position=(x, y),
            )
            self._buttons.append(btn)
            y -= 100
        bs.timer(10, self.end_votes)
    
    def update_buttons(self):
        for btn in self._buttons:
            btn._update_display()
    
    def end_votes(self):
        # Get the modifier with the most votes
        winner_mod = max(
            self._modifier_votes,
            key=lambda m: len(self._modifier_votes[m])
        )
        # Delete all the buttons that 
        # aren't our winner modifer
        for btn in self._buttons[:]:
            if btn._modifier is not winner_mod:
                btn.handlemessage(bs.DieMessage())
                self._buttons.remove(btn)
            else:
                bs.timer(1.5, bs.Call(btn.handlemessage, bs.DieMessage()))
        # Then, apply the modifier's effects!!
        winner_mod.apply()
    
    def exists(self):
        return bool(self.node)
    
    def on_expire(self):
        self.handlemessage(bs.DieMessage())
    
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            self._buttons.clear()
            self._modifier_votes.clear()
        else:
            return super().handlemessage(msg)
        return None