"""doze"""
from __future__ import annotations
import bascenev1 as bs
import mellboii.mell_resources as mell
import random
from bascenev1lib.actor.image_looped import LoopingImageAnimation

ASSETS = {
    'normal': {
        'textures': {
            # prefix for path
            'path': 'entities/dozer/default/',
            # 'action': ('filename', frame count, frame delay, loop)
            'static': ('static', 3, 0.06, True),
            'wake': ('wake', 3, 0.06, True),
            'kill': ('kill', 3, 0.01, True),
        },
        'sounds': {
            # prefix for path
            'path': 'entities/dozer/default/',
            'kill': 'kill',
            'ticking': 'ticking',
        },
    },
}

class Dozer(bs.Actor):
    """spaz must stand still, or gets its head blown"""
    def __init__(self, actor: bs.Actor):
        super().__init__()
        self.actor = actor
        self.color = None
        self.high = None
        self.head = None
        self._x = 0
        self._y = 0
        self._scale = 0
        self.exists2 = False
        self.name_text = None
        self._slot = 0
        self._rotate_timer = None
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
        self.exists2 = True
        entities = self._activity().entities
        self._slot = _get_free_slot(entities)
        if len(self.getactivity().players) > 1:
            self.color = self.actor().node.color
            self.high = self.actor().node.highlight
        else:
            self.color = (1, 1, 0.2)
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
    
    def _rotate(self):
        if not self.head.node:
            self._rotate_timer = None
            return
        amount = 18
        if random.random() < 0.4:
            self.head.node.rotate += amount
        else:
            self.head.node.rotate -= amount
    
    def _check(self, chance: int = 0.1):
        # do some checks to prevent us from apearing in bad situations
        if (
            random.random() >= chance 
            or self.exists2
            or not self.actor().dozered
            or not self.actor()
            or not self.actor().node
            or not self.actor().is_alive()
        ):
            if not self.actor() or not self.actor().is_alive():
                self.stop()
                return
            if not self.actor().dozered:
                self.stop()
            return
        if not self.actor().node:
            self._delete()
            return
        self._get_free_space()
        scale = 200
        self._scale = scale
        self.recreate_head('static')
        self.create_name_text()
        time = random.uniform(0.8, 1.7)
        self.playsound('ticking')
        bs.timer(time, self._check_standing)
        mell.shake_node(
            self.head.node,
            duration=time,
            interval=0.01,
            intensity=4,
        )
        self._rotate_timer = bs.Timer(0.2, self._rotate, repeat=True)
    
    def _actor_moving(self) -> bool:
        return bool(abs(self.actor().last_x) >= 0.2 or abs(self.actor().last_y) >= 0.2)
    
    def _check_standing(self):
        self.recreate_head('wake')
        if not self.actor().node or not self.actor().is_alive():
            self.actor().dozered = False
            self._delete()
            return
        if self._actor_moving():
            bs.timer(0.1, self._death)
        else:
            # we don't do anything special, so just delete
            bs.timer(0.1, self._delete)
        return

    def _death(self):
        self.playsound('kill')
        self.recreate_head('kill')
        def die():
            # if parrying, DON'T die.
            if self.actor().parrying:
                self.actor().sugarcoat_overlay(sound='bellMed', image='sugarcoatparry')
                self.actor().mpa()
                self.actor().smashkill(sound='thunder', autodie=False)
                return
            self.actor().dozered = False
            self.actor().explode_head()
            self.actor().killed_by_entity('dozer')
        # schedules... yummy...
        bs.timer(0.2, self._delete)
        bs.timer(0.18, die)
        bs.timer(0.1, self.actor().dodge_warning)
    
    def _delete(self):
        # delete nodes
        if getattr(self.head, 'node', None):
            self.head.node.delete()
        if self.name_text:
            self.name_text.delete()
        if self._rotate_timer:
            self._rotate_timer = None
        self.exists2 = False
        if not hasattr(self._activity(), 'entities'):
            self._activity().entities = {}
        entities = self._activity().entities
        entities.pop(self._slot, None)  
    
    def start(self):
        self.check_timer = bs.Timer(1.2, self._check, repeat=True)
    
    def stop(self):
        self.check_timer = None
        self._delete()
    
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            # we'll check if the spaz still exists and has us, and if it doesn't we can stop
            if self.actor() and self.actor().node and not self.actor().dozered:
                self.stop()
            elif not self.actor() or not self.actor().node:
                self.stop()
            else:
                self._delete()
        else:
            super().handlemessage(msg) # Augment standard behavior.