"""gooner"""
from __future__ import annotations
from bascenev1lib.gameutils import SharedObjects, TouchedMessage
import bascenev1 as bs
import mellboii.mell_resources as mell
import random
import math

class Mime(bs.Actor):
    """spaz has to BEAT THIS FUCKER TO DEATH 
    (which won't happen since hes inv), 
    otherwise he'll touch him eventually and kill spaz!"""
    def __init__(self, actor: bs.Actor):
        super().__init__()
        self.actor = actor
        self.exists2 = False
        self._current_frame = 1
        self.frame_count = 3
        self.frame_delay = 0.1
        self.node: bs.Node | None = None
        shared = SharedObjects.get()
        self.material = shared.touch_material
        self.volume = 0.9
    
    def move_tick(self):
        if not self.node or not self.actor().node:
            return
        # check distance between us and spaz.
        our_pos = self.node.position
        spaz_pos = self.actor().node.position
        dx = spaz_pos[0] - our_pos[0]
        dy = spaz_pos[1] - our_pos[1]
        dz = spaz_pos[2] - our_pos[2]

        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        # our strength is based on distance, 
        # so we get stronger far away.
        strength = dist / 5
        # if we're within reasonable distance, 
        # we reel ourself towards spaz menagincly
        if dist > 3:
            self.node.handlemessage(
                'impulse',
                our_pos[0],
                our_pos[1],
                our_pos[2],
                0, 0, 0,
                80, 80, 0,
                0,
                dx * strength,
                dy * strength,
                dz * strength,
            )
        # too close, and we start moving away 
        # (assuming they're walking into us)
        elif dist <= 1.8:
            # reset the strength to be stronger IF we're closer.
            strength = dist * 0.4
            self.node.handlemessage(
                'impulse',
                our_pos[0],
                our_pos[1],
                our_pos[2],
                0, 0, 0,
                80, 80, 0,
                0,
                -dx * strength,
                -dy * strength,
                -dz * strength,
            )
    
    def _check(self):
        chance = 0.25
        if (
            random.random() >= chance 
            or self.exists2
            or not self.actor().mimed
            or not self.actor()
            or not self.actor().node
            or not self.actor().is_alive()
        ):
            if not self.actor() or not self.actor().is_alive():
                self.stop()
                return
            if not self.actor().mimed:
                self.stop()
            if self.exists2:
                self._check_sound()
            return
        if not self.actor().node:
            self._delete()
            return
        # assuming from this point forward everything is ok
        self.exists2 = True
        shared = SharedObjects.get()
        pos = self.actor().node.position
        offset_x = random.uniform(-2, 2)
        offset_z = random.uniform(-2, 2)
        offset_y = 1.5
        position = (pos[0] + offset_x, pos[1] + offset_y, pos[2] + offset_z)
        self.scale = 0.8
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'body_scale': self.scale,
                'position': position,
                'mesh': bs.getmesh('mime1'),
                'mesh_scale': 0,
                'light_mesh': bs.getmesh('mime1'),
                'shadow_size': 0.5,
                'color_texture': bs.gettexture('white'),
                'reflection': 'powerup',
                'reflection_scale': [0.7],
                'materials': (self.material, shared.object_material),
            },
        )
        bs.animate(self.node, 'mesh_scale', 
            {
                0: 0, 
                0.6: self.scale,
            }
        )
        self._anim_timer = bs.Timer(self.frame_delay, self.animate, repeat=True)
        self._move_timer = bs.Timer(0.01, self.move_tick, repeat=True)
    
    def _check_sound(self):
        if random.random () > 0.1:
            return
        list = ['mvoice' + str(i + 1) + '' for i in range(7)]
        choice = random.choice(list)
        if self.node:
            bs.getsound(choice).play(
                volume=self.volume,
                position=self.node.position,
            )
    
    def _delete(self):
        if self.node:
            self.node.delete()
            self.node = None
        self.exists2 = False
    
    def animate(self):
        """Advance to the next frame."""
        if not self.node:
            if self._anim_timer:
                self._anim_timer = None
            return

        self._current_frame += 1

        # Wrap around if looping.
        loop = True
        if self._current_frame > self.frame_count:
            if loop:
                self._current_frame = 1
            else:
                # Stop animation if not looping.
                self._anim_timer = None
                return

        tex_name = f"mime{self._current_frame}"
        try:
            self.node.mesh = bs.getmesh(tex_name)
        except Exception as e:
            print(f'[Mime] Got error {e} while changing mesh to {tex_name}')
            if self._anim_timer:
                self._anim_timer = None
        
    def start(self):
        self.check_timer = bs.Timer(0.8, self._check, repeat=True)
    
    def stop(self):
        self.check_timer = None
        self._delete()
    
    def handlemessage(self, msg):
        # ouch. we just got hit.
        if isinstance(msg, bs.HitMessage):
            # we only accept hits from our actor's player
            if msg.get_source_player(bs.Player) is self.actor().source_player:
                if msg.hit_type == 'punch':
                    bs.app.classic.ach.award_local_achievement(
                        'MimePunch'
                    )
                bs.getsound('mhurt').play(
                    volume=self.volume, 
                    position=self.node.position
                )
                self._delete()
        # aha! came into contact with something
        elif isinstance(msg, TouchedMessage):
            from bascenev1lib.actor.spaz import Spaz
            toucher = bs.getcollision().opposingnode
            actor = None
            if toucher:
                actor = toucher.getdelegate(Spaz)
            # we don't check if it's our actor here, 
            # so irregardless of whoever we touch we kill
            if actor:
                actor.impulse(x=-50, y=190)
                actor.shatter()
                actor.killed_by_entity('mime')
        # ow. we fell out of bounds
        elif isinstance(msg, bs.OutOfBoundsMessage):
            bs.getsound('mhurt').play(
                volume=self.volume, 
                position=self.node.position
            )
            self._delete()
        else:
            return super().handlemessage(msg) # Augment the very standard behavior.
        return None