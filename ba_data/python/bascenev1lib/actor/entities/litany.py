"""yup"""
from __future__ import annotations
from typing import override
import bascenev1 as bs
import mellboii.mell_resources as mell
import random
import math
from bascenev1lib.actor.image_looped import LoopingImageAnimation
# define paths to assets like textures and sounds.
# useful for things like skins
ASSETS = {
    'normal': {
        'textures': {
            # prefix for path
            'path': 'entities/litany/default/',
            # 'action': ('filename', frame count, frame delay, loop)
            'head': ('base', 3, 0.06, True),
            'eye_open': ('eye_open', 3, 0.06, True),
            'eye_closed': ('eye_closed', 3, 0.06, True),
            'eye_opening': ('eye_opening', 3, 0.03, False),
        },
        'sounds': {
            # prefix for path
            'path': 'entities/litany/default/',
            'eye_opened': 'eye_opened',
            'last_eye_opened': 'last_eye_opened',
            'parried': 'parried',
            'ticking': 'ticking',
            'ticking_opened': 'ticking_opened',
            'warning': 'warning',
            'kill': 'kill',
        },
    },
}
INTERVAL = 3

class Eye(bs.Actor):
    """a class for one of litany's eyes.
    made to handle logic by itself (and with most 
    control from litany itself)
    (also ire reference :3)"""
    @override
    def on_expire(self) -> None:
        super().on_expire()
        self.source = None
        
    def __init__(self, source: Litany):
        super().__init__()
        self.source = source
        self.active = False
        self.x = 0
        self.y = 0
        self._scale = 50
        self.dead = False
        self.image = None
        self.rotate = 0
        self.last_eye = False
    
    def recreate(self, name: str):
        skin_assets = ASSETS[self.source.skin]['textures']
        tex, frames, delay, repeat = skin_assets[name]
        path = skin_assets['path']
        pos = (self.x, self.y)
        scale = (self._scale, self._scale)
        if self.image:
            self.image.die()
            self.image = None
        self.image = LoopingImageAnimation(
            f'{path}{tex}',
            frame_count=frames,
            frame_delay=delay,
            scale=scale,
            position=pos,
            loop=repeat,
            attach="bottomCenter",
        )
        self.image.node.rotate = self.rotate
    
    def playsound(self, name: str):
        """Given a action name, plays a sound
        using assets from its' skin."""
        skin_assets = ASSETS[self.source.skin]['sounds']
        path = skin_assets['path']
        sound = skin_assets[name]
        volume = 1.0
        bs.getsound(f'{path}{sound}').play(volume=volume)

    def set_pos_and_rotation(self, pos, angle):
        self.x, self.y = (
            self.source._x + pos[0],
            self.source._y + pos[1],
        )
        self.rotate = angle
        self.recreate('eye_closed')
    
    def schedule_open(self):
        if self.dead:
            return
        values = self.source.my_many_eyes.values()
        index = list(values).index(self)
        delay = INTERVAL * (index + 1)
        bs.timer(delay, self.warning)
    
    def delete(self):
        self.dead = True
        if self.image:
            self.image.die()
            self.image = None
    
    def warning(self):
        if self.dead:
            return
        self.source.flash_red()
        bs.timer(0.6, self.open)
    
    def open(self):
        if self.dead:
            return
        if self.last_eye:
            self.playsound('last_eye_opened')
        else:
            self.playsound('eye_opened')
        self.source.activate_alt_ticking()
        self.recreate('eye_opening')
        bs.timer(0.15, self.source.check_for_death)
        bs.timer(0.3, self.close)
    
    def close(self):
        if self.dead:
            return
        if self.last_eye:
            self.source._delete()
            return
        self.recreate('eye_closed')

class Litany(bs.Actor):
    """why did you listen"""
    def __init__(self, actor: bs.Actor):
        super().__init__()
        self.actor = actor
        self.color = None
        self.high = None
        self.head = None
        self.skin = 'normal'
        self.my_many_eyes: dict = {}
        self.how_many_should_we_like_actually_have_tho_when_we_spawn_or_something = 3
        self._x = 0
        self._y = 0
        self._scale = 200
        self.exists2 = False
        self.name_text = None
        self.alt_ticking = False
        self.at_sound = None
        self.t_sound = None
        self._slot = 0
    
    def _actor_moving(self) -> bool:
        return bool(abs(self.actor().last_x) >= 0.2 or abs(self.actor().last_y) >= 0.2)
    
    def flash_red(self):
        dict1 = {
            0: self.color,
            0.05: (5, 0, 0),
            0.2: self.color,
        }
        bs.animate_array(self.head.node, 'color', 3, dict1)
        self.playsound('warning')
    
    def activate_alt_ticking(self):
        if self.alt_ticking:
            return False
        self.alt_ticking = True
        name = 'ticking_opened'
        skin_assets = ASSETS[self.skin]['sounds']
        path = skin_assets['path']
        sound = skin_assets[name]
        self.at_sound = bs.newnode(
            'sound',
            attrs={
                'sound': bs.getsound(f'{path}{sound}'),
                'volume': 1.0,
                'positional': False,
            }
        )
    
    def check_for_death(self):
        if not self.actor().node or not self.actor().is_alive():
            self.actor().litanyd = False
            self._delete()
            return
        if self._actor_moving():
            if self.actor().parrying:
                return
            self._death()
    
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
        for eye in self.my_many_eyes.values():
            if eye:
                eye.delete()
                eye = None
        self.my_many_eyes.clear()
        if self.at_sound:
            self.at_sound.volume = 0
            self.at_sound.delete()
        if self.t_sound:
            self.t_sound.volume = 0
            self.t_sound.delete()
    
    def playsound(self, name: str):
        """Given a action name, plays a sound
        using assets from its' skin."""
        skin_assets = ASSETS[self.skin]['sounds']
        path = skin_assets['path']
        sound = skin_assets[name]
        volume = 1.0
        bs.getsound(f'{path}{sound}').play(volume=volume)
    
    def _death(self):
        self.head.node.color = (0, 0, 0)
        self.playsound('kill')
        def die():
            self.actor().litanyd = False
            self.actor().explode_head()
            self.actor().killed_by_entity('litany')
        # schedules... yummy...
        bs.timer(1.0, self._delete)
        bs.timer(0.7, die)
    
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
    
    def _check(self):
        chance = 0.1
        if (
            random.random() >= chance 
            or self.exists2
            or not self.actor().litanyd
            or not self.actor()
            or not self.actor().node
            or not self.actor().is_alive()
        ):
            if not self.actor() or not self.actor().is_alive() or not self.actor().node:
                self.stop()
                return
            if not self.actor().litanyd:
                self.stop()
            return
        if not self.actor().node:
            self._delete()
            return
        self._get_free_space()
        self.recreate_head('head')
        self.create_name_text()
        self.exists2 = True
        name = 'ticking'
        skin_assets = ASSETS[self.skin]['sounds']
        path = skin_assets['path']
        sound = skin_assets[name]
        self.t_sound = bs.newnode(
            'sound',
            attrs={
                'sound': bs.getsound(f'{path}{sound}'),
                'volume': 1.0,
                'positional': False,
            }
        )
        # create all the eyes
        for _ in range(self.how_many_should_we_like_actually_have_tho_when_we_spawn_or_something):
            # get a free slot
            def _get_free_slot(thedict: dict) -> int:
                slot = 0
                while slot in thedict:
                    slot += 1
                return slot
            # create each eye and add them to the dict
            this_slot = _get_free_slot(self.my_many_eyes)
            eye = Eye(source=self)
            eye.x = self._x
            eye.y = self._y
            if (
                (this_slot + 1)
                >= self.how_many_should_we_like_actually_have_tho_when_we_spawn_or_something
            ):
                eye.last_eye = True
            self.my_many_eyes[this_slot] = eye
            
        rotation_dict = {
            0: 0,   # bottom
            1: -140,   # top left
            2: -40,     # top right
        }
        centerx = 20
        cornery = 30
        pos_dict = {
            0: (0, -15),   # bottom
            1: (-centerx, cornery),   # top left
            2: (centerx, cornery),     # top right
            3: (-centerx, -cornery),     # bottom left
            4: (centerx, -cornery),     # bottom right
        }
        for index, eye in enumerate(self.my_many_eyes.values()):
            angle = rotation_dict.get(index)
            pos = pos_dict.get(index)

            if angle is None:
                # fallback to circle
                angle = (360 / len(self.my_many_eyes)) * index
            if pos is None:
                pos = random.choice(list(pos_dict.values()))
            eye.set_pos_and_rotation(pos, angle)
            eye.schedule_open()
    
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
    
    def recreate_head(self, name: str):
        """Given a action name, recreates the
        entity's head at its' position using assets from
        its' skin and the action name."""
        
        # wow this is very unsafe.. should do checks
        # get assets (textures) from our skin
        skin_assets = ASSETS[self.skin]['textures']
        # hash data from the action name
        tex, frames, delay, repeat = skin_assets[name]
        # get a path for all the actual assets
        path = skin_assets['path']
        pos = (self._x, self._y)
        scale = (self._scale, self._scale)
        if self.head:
            self.head.die()
            self.head = None
        self.head = LoopingImageAnimation(
            f'{path}{tex}', 
            frame_count=frames, 
            frame_delay=delay, 
            scale=scale, 
            position=pos,
            loop=repeat,
            attach='bottomCenter',
        )
        self.head.node.color = self.color
    
    def start(self):
        self.check_timer = bs.Timer(1.2, self._check, repeat=True)
    
    def stop(self):
        self.check_timer = None
        self._delete()
    
    @override
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            # we'll check if the spaz still exists and has us, and if it doesn't we can stop
            if self.actor() and self.actor().node and not self.actor().litanyd:
                self.stop()
            elif not self.actor() or not self.actor().node:
                self.stop()
            else:
                self._delete()
        else:
            super().handlemessage(msg) # Augment standard behavior.