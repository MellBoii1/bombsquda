"""Script for Ire, the entity that forces a spaz to jump (at correct timing) or die."""
from __future__ import annotations
from typing import override
import bascenev1 as bs
import mellboii.mell_resources as mell
import random
from bascenev1lib.actor.image_looped import LoopingImageAnimation

# define paths to assets like textures and sounds.
# useful for things like skins
ASSETS = {
    'normal': {
        'textures': {
            # prefix for path
            'path': 'entities/ire/default/',
            # 'action': ('filename', frame count, frame delay, loop)
            'appear': ('appear', 3, 0.08, True),
            'ready': ('ready', 3, 0.06, True),
            'kill': ('kill', 4, 0.05, True),
            'frown': ('frown', 3, 0.05, True),
            'angry': ('angry', 3, 0.05, True),
            'attack': ('attack', 4, 0.05, False),
        },
        'sounds': {
            # prefix for path
            'path': 'entities/ire/default/',
            'kill': 'kill',
            'appear': 'appear',
            'ready': 'ready',
            'attack': 'attack',
            'player_die': 'shatter_worse',
        },
    },
    'kitty': {
        'textures': {
            # prefix for path
            'path': 'entities/ire/kitty/',
            # 'action': ('filename', frame count, frame delay, loop)
            'appear': ('appear', 3, 0.08, True),
            'ready': ('ready', 3, 0.06, True),
            'kill': ('kill', 4, 0.05, True),
            'frown': ('frown', 3, 0.05, True),
            'angry': ('angry', 3, 0.05, True),
            'attack': ('attack', 4, 0.05, False),
        },
        'sounds': {
            # prefix for path
            'path': 'entities/ire/default/',
            'kill': 'kill',
            'appear': 'appear',
            'ready': 'ready',
            'attack': 'attack',
            'player_die': 'shatter_worse',
        },
    },
}

class Ire(bs.Actor):
    """spaz must jump when it strikes, or he dies
    'it's pronounced eye-r-uh!', was what this docstring originally said
    (and yes, that's how it's pronounced and i'm standing by that)"""
    def __init__(self, actor: bs.Actor):
        """weakref actor otherwise the game 
        cries about it not dying"""
        super().__init__()
        self.actor = actor
        self.color = None
        self.high = None
        self.head = None
        self._x = 0
        self._y = 0
        self._scale = 200
        self.tick_timer = None
        self.exists2 = False
        self.name_text = None
        self.check_timer = None
        self._slot = 0
        self.times_avoided = 0
        self.skin = 'normal'

    def _get_free_space(self):
        # ok... get a free space based on how many of us
        # there are
        if not hasattr(self._activity(), 'entities'):
            self._activity().entities = {}
        def _get_free_slot(entities: dict) -> int:
            slot = 0
            while slot in entities:
                slot += 1
            return slot
        entities = self._activity().entities
        self._slot = _get_free_slot(entities)
        if len(self.getactivity().players) > 0:
            self.color = self.actor().node.color
            self.high = self.actor().node.highlight
        else:
            self.color = (1, 1, 1)
            self.high = (0, 0, 0)
        entities[self._slot] = self
        max_per_column = 5
        col = self._slot // max_per_column
        row = self._slot % max_per_column
        spacing = 140
        x = -500 + (col * 200)
        y = 100 + (row * spacing)
        self._x = x
        self._y = y
    
    def _delete(self):
        # delete nodes
        if self.head:
            self.head.die()
            self.head = None
        if self.name_text:
            self.name_text.delete()
        self.exists2 = False
        if not hasattr(self._activity(), 'entities'):
            self._activity().entities = {}
        entities = self._activity().entities
        entities.pop(self._slot, None)  
    
    def recreate_head(self, name: str):
        """Given a action name, recreates the
        entity's head at its' position using assets from
        its' skin and the action name."""
        
        # wow this is very unsafe.. should do checks
        # get assets (textures) from our skin
        skin_assets = ASSETS.get(self.skin, {}).get('textures', {})
        # hash data from the action name
        tex, frames, delay, repeat = skin_assets.get(name)
        # get a path for all the actual assets
        path = skin_assets.get('path')
        pos = (self._x, self._y)
        scale = (self._scale, self._scale)
        if self.head:
            self.head.die()
            self.head = None
        self.head = LoopingImageAnimation(
            f'{path}{tex}', 
            f'{path}{tex}CM', 
            frame_count=frames, 
            frame_delay=delay, 
            scale=scale, 
            position=pos,
            loop=repeat,
            attach="bottomCenter",
        )
        self.head.node.tint_color = self.color
        self.head.node.tint2_color = self.high
    
    def playsound(self, name: str):
        """Given a action name, plays a sound
        using assets from its' skin."""
        skin_assets = ASSETS.get(self.skin, {}).get('sounds', {})
        path = skin_assets.get('path', '')
        sound = skin_assets.get(name, 'trublank')
        volume = 1.3
        bs.getsound(f'{path}{sound}').play(volume=volume)
    
    def create_name_text(self):
        self.name_text =  bs.newnode(
            'text',
            delegate=self,
            attrs={
                'text': f'({self.actor().node.name})',
                'scale': 1.0,
                'color': self.actor().node.color,
                'h_align': 'center',
                'position': (self._x - 3, self._y - 90),
                'v_attach': 'bottom',
                'front': True,
            },
        )
        bs.animate(self.name_text, 'opacity', {
            0.0: 0,
            0.5: 0.5,
        })
    
    def _check(self, chance = 0.12):
        # fuck you
        if (
            random.random() >= chance 
            or self.exists2
            or not self.actor().ired
            or not self.actor()
            or not self.actor().node
            or not self.actor().is_alive()
            or (self.actor().sorrow and self.actor().sorrow.exists2)
        ):
            if not self.actor() or not self.actor().is_alive() or not self.actor().node:
                self.stop()
                return
            if not self.actor().ired:
                self.stop()
            return
        if not self.actor().node:
            self._delete()
            return
        self._get_free_space()
        self.exists2 = True
        self.recreate_head('appear')
        self.create_name_text()
        self.playsound('appear')
        bs.timer(1.7, self._ready)
    
    def _check_ungrounded(self):
        # aw dang it, they're already dead :<
        if not self.actor().node or not self.actor().is_alive():
            self.actor().ired = False
            self._delete()
            return
        # standing determines whether 
        # spaz is on ground
        if self.actor().standing == True:
            self._death()
        else:
            self._animate_out()
        self.tick_timer = None
        return
    
    def _animate_out(self):
        self.times_avoided += 1
        # if we got avoided too many times, 
        # start doing another expression
        if self.times_avoided >= 6:
            expression = 'angry'
        else:
            expression = 'frown'
        self.recreate_head(expression)
        bs.timer(0.5, self._delete)
    
    def _death(self):
        self.playsound('kill')
        self.recreate_head('kill')
        mell.shake_node(
            self.head.node,
            duration=0.6,
            interval=0.0001,
            intensity=2,
        )
        bs.timer(0.6, lambda: mell.shake_node(
                self.head.node,
                duration=0.6,
                interval=0.0001,
                intensity=7,
            )
        )
        def die():
            # dont die if the player is parrying
            if self.actor().parrying:
                self.actor().sugarcoat_overlay(sound='bellMed', image='sugarcoatparry')
                self.actor().mpa()
                self.actor().smashkill(sound='thunder', autodie=False)
                self._delete()
                return
            self.actor().ired = False
            # we reuse hardmode's death because it's similar
            self.actor().hardmode_death()
            self.actor().die()
            self.actor().impulse(y=500)
            self.actor().killed_by_entity('ire')
            self._delete()
            self.playsound('player_die')
        bs.timer(1.2, die)
        bs.timer(1.1, self.actor().dodge_warning)
    
    def _anim_attack(self):
        # wow they're still dead!
        if not self.actor().node or not self.actor().is_alive():
            self.actor().ired = False
            self._delete()
            return
        self.recreate_head('attack')
        self.playsound('attack')
        bs.timer(0.4, self._check_ungrounded)
    
    def _ready(self):
        # wow why are they dead!
        if not self.actor().node or not self.actor().is_alive():
            self.actor().ired = False
            self._delete()
            return
        # show a warning that we're about to attack
        self.recreate_head('ready')
        self.playsound('ready')
        dict1 = {
            0: self.color,
            0.1: (5, 0, 0),
            0.3: self.color,
        }
        dict2 = {
            0: self.high,
            0.1: (12, 0, 0), # higher here cuz our 'tint2' color is dark
            0.3: self.high,
        }
        bs.animate_array(self.head.node, 'tint_color', 3, dict1)
        bs.animate_array(self.head.node, 'tint2_color', 3, dict2)
        bs.timer(1.1, self._anim_attack)
    
    def start(self):
        self.check_timer = bs.Timer(1.2, self._check, repeat=True)
    
    def stop(self):
        self.check_timer = None
        self._delete()
    
    @override
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            # we'll check if the spaz still exists and has us, and if it doesn't we can stop
            if self.actor() and self.actor().node and not self.actor().ired:
                self.stop()
            elif not self.actor() or not self.actor().node:
                self.stop()
            else:
                self._delete()
        else:
            super().handlemessage(msg) # Augment standard behavior.