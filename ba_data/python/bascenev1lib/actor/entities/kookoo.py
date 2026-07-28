"""Script for Kookoo, where Spaz has to let go of anything when it's time."""
from __future__ import annotations
import bascenev1 as bs
import mellboii.mell_resources as mell
import random
from bascenev1lib.actor.image_looped import LoopingImageAnimation

class Kookoo(bs.Actor):
    """spaz must let go of all held 
    items or he faces a terrible faaatee...
    oh, and also memorizing. can't forget that!"""
    def __init__(self, actor: bs.Actor):
        super().__init__()
        self.actor = actor
        self.color = None
        self.high = None
        self.arm = None
        self.head = None
        self.tick_number = 0
        self._x = 0
        self._y = 0
        self._scale = 0
        self.tick_timer = None
        self.exists2 = False
        self.name_text = None
        self.time_text = None
        self._slot = 0

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
        if len(entities) > 0:
            self.color = self.actor().node.color
            self.high = self.actor().node.highlight
        else:
            self.color = (0, 0, 1)
            self.high = (0, 0, 0.7)
        entities[self._slot] = self
        max_per_column = 5
        col = self._slot // max_per_column
        row = self._slot % max_per_column
        spacing = 140
        x = -500 + (col * 200)
        y = 100 + (row * spacing)
        self._x = x
        self._y = y
    
    def _check(self, chance: int = 0.1, speed: int = 0.8):
        # do some checks to prevent us from appearing in bad situations
        if (
            random.random() >= chance 
            or self.exists2
            or not self.actor().kookood
            or not self.actor()
            or not self.actor().node
            or not self.actor().is_alive()
        ):
            if not self.actor() or not self.actor().is_alive() or not self.actor().node:
                self.stop()
                return
            if not self.actor().kookood:
                self.stop()
            return
        if not self.actor().node:
            self._delete()
            return
        self._get_free_space()
        scale = 200
        self._scale = scale
        # generate a random number we'll check at
        self.end_time = random.randint(4, 13)
        # create our arm (animation)
        def create_arm():
            self.arm = LoopingImageAnimation(
                'karm_appear',
                'karm_appearCM',
                frame_count=5, 
                frame_delay=0.07, 
                scale=(scale, scale), 
                position=(self._x, self._y),
                loop=False,
                attach="bottomCenter",
            )
            self.arm.node.tint_color = self.color
            self.arm.node.tint2_color = self.high
        # animate arm pointing
        def arm_point():
            self.arm.node.delete()
            self.arm = LoopingImageAnimation(
                'karm_point', 
                'karm_pointCM', 
                frame_count=3, 
                frame_delay=0.07, 
                scale=(scale, scale), 
                position=(self._x, self._y),
                loop=True,
                attach="bottomCenter",
            )
            self.arm.node.tint_color = self.color
            self.arm.node.tint2_color = self.high
            # create the text for the timer
            self.time_text = bs.newnode(
                'text',
                delegate=self,
                attrs={
                    'text': str(self.end_time),
                    'scale': 1.5,
                    'color': self.color,
                    'h_align': 'center',
                    'position': (self._x - 3, self._y - 28),
                    'v_attach': 'bottom',
                    'front': True,
                },
            )
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
            # animate opacity in
            bs.animate(self.time_text, 'opacity', {
                0.0: 0,
                0.5: 1,
            })
            bs.animate(self.name_text, 'opacity', {
                0.3: 0,
                0.6: 0.5,
            })
        # animate arm out
        def arm_out():
            self.arm.node.delete()
            self.arm = LoopingImageAnimation(
                'karm_out',
                'karm_outCM',
                frame_count=6,
                frame_delay=0.07,
                scale=(scale, scale),
                position=(self._x, self._y),
                loop=False,
                attach="bottomCenter",
            )
            self.arm.node.tint_color = self.color
            self.arm.node.tint2_color = self.high
        # play a sound
        def pointysound():
            bs.getsound('kwarnin').play()
        # animate in i guess
        self.recreate_head('ktrans', frames=5, delay=0.06, repeat=False)
        # schedule all those
        bs.timer(0.1, create_arm)
        bs.timer(0.2, pointysound)
        bs.timer(0.35, arm_point)
        bs.timer(1.5, arm_out)
        # then start tickin
        bs.timer(1.9, lambda: self._start_ticking(speed=speed))
    
    def recreate_head(
        self, 
        tex: str = 'ktransb',
        frames: int = 1, 
        delay: int = 0.05,
        repeat: bool = True,
    ):
        pos = (self._x, self._y)
        scale = (self._scale, self._scale)
        # delete ye olde head
        if self.head:
            self.head.node.delete()
        # transition in persay idk man
        self.head = LoopingImageAnimation(
            tex, 
            f'{tex}CM', 
            frame_count=frames, 
            frame_delay=delay, 
            scale=scale, 
            position=pos,
            loop=repeat,
            attach="bottomCenter",
        )
        self.head.node.tint_color = self.color
        self.head.node.tint2_color = self.high
    
    def _tick(self, speed: int):
        # if spaz not alive, we can just stop
        if not self.actor().node or not self.actor().is_alive():
            self.tick_timer = None
            self.actor().kookood = False
            self._delete()
            return
            
        # time has reached the end! time to check
        if self.tick_number >= self.end_time:
            if self.actor().shield:
                self._break_shield()
            elif self.actor().node.hold_node:
                self._death()
            else:
                self._survived()
            # stop ticking and reset our number
            self.tick_timer = None
            self.tick_number = 0
            return
            
        self.tick_number += 1
        bs.getsound(f'ktick{self.tick_number}').play()
        if self.time_text:
            self.time_text.text = str(self.tick_number)
        mell.shake_node(
            self.time_text,
            duration=speed - 0.3,
            interval=0.01,
            intensity=4,
        )
    
    def _death(self):
        self.recreate_head('ktransb', frames=5, delay=0.03, repeat=False)
        self.time_text.delete()
        # sound
        bs.getsound('kdie').play()
        def die():
            # if parrying, DON'T die.
            if self.actor().parrying:
                self.actor().sugarcoat_overlay(sound='bellMed', image='sugarcoatparry')
                self.actor().mpa()
                self.actor().smashkill(sound='thunder', autodie=False)
                return
            self.actor().kookood = False
            self.actor().kookoo_death()
            self.actor().killed_by_entity('kookoo')
        # reset ticking and check num
        self.tick_number = 0
        self.tick_timer = None
        # schedules... yummy...
        bs.timer(0.5, self._delete)
        bs.timer(0.4, die)
        bs.timer(0.25, self.actor().dodge_warning)
    
    def _start_ticking(self, speed: int = 0.8):
        self.recreate_head('ktick', frames=2, delay=0.06, repeat=True)
        # delete arm
        self.arm.node.delete()
        # actual ticker
        self._tick(speed)
        self.tick_timer = bs.Timer(speed, lambda: self._tick(speed=speed), repeat=True)
    
    def start(self):
        self.check_timer = bs.Timer(1.2, self._check, repeat=True)
    
    def stop(self):
        self.check_timer = None
        self._delete()
    
    def _survived(self):
        self.recreate_head('ktransb', frames=5, delay=0.03, repeat=False)
        # delete time
        self.time_text.delete()
        # play sound
        bs.getsound('klive').play(2)
        # ok reset everything and go away
        self.tick_timer = None
        bs.timer(0.2, self._delete)
    
    def _delete(self):
        # delete nodes
        if getattr(self.head, 'node', None):
            self.head.node.delete()
        if self.time_text:
            self.time_text.delete()
        if self.name_text:
            self.name_text.delete()
        self.exists2 = False
        # pop us from the "spacing" list
        if not hasattr(self._activity(), 'entities'):
            self._activity().entities = {}
        entities = self._activity().entities
        entities.pop(self._slot, None)  
        
    def _break_shield(self):
        self.recreate_head('ktransb', frames=5, delay=0.03, repeat=False)
        self.tick_timer = None
        self.time_text.delete()
        # get like WAY faster to kinda signify we're doin something
        def speedup():
            self.recreate_head('khead', frames=3, delay=0.01, repeat=True)
            mell.shake_node(
                self.head.node,
                duration=0.2,
                interval=0.0001,
                intensity=15,
            )
        # sound
        bs.getsound('kbreak').play()
        def breakem():
            if self.actor().shield:
                if self.actor().parrying:
                    self.actor().sugarcoat_overlay(sound='dingSmall', image='sugarcoatparry')
                    return
                # yeah so we hate their shield
                # we're gonna delete it
                self.actor().shield.delete()
                self.actor().shield = None
                # Emit some cool looking sparks when the shield dies.
                npos = self.actor().node.position
                bs.emitfx(
                    position=(npos[0], npos[1] + 0.9, npos[2]),
                    velocity=self.actor().node.velocity,
                    count=random.randrange(20, 30),
                    scale=1.0,
                    spread=0.6,
                    chunk_type='spark',
                )
                # say something just because we want to
                self.actor().scary_text(
                    bs.Lstr(resource=f'kookooBreaksShield{random.randint(1, 4)}').evaluate(),
                    color=(0, 0, 1),
                    xpos=0,
                    endtime=4,
                    spacing_x=0.29,
                    shakiness=0.075,
                )
            # knockout and impulse! yeah!
            self.actor().node.handlemessage('knockout', 750)
            self.actor().impulse(x=-500, y=70)
        # start ticking way faster than normal
        def retick():
            self._check(chance=1, speed=0.55)
        # schedules
        bs.timer(0.1, speedup)
        bs.timer(0.4, self._delete)
        bs.timer(0.3, breakem)
        bs.timer(0.41, retick)
    
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            # we'll check if the spaz still exists and has us, and if it doesn't we can stop
            if self.actor() and self.actor().node and not self.actor().kookood:
                self.stop()
            elif not self.actor() or not self.actor().node:
                self.stop()
            else:
                self._delete()
        else:
            super().handlemessage(msg) # Augment standard behavior.
    