"""blood rain"""
from __future__ import annotations
from bascenev1lib.actor.particles import BloodRaindrop
import bascenev1 as bs
import mellboii.mell_resources as mell
import random

class Sorrow(bs.Actor):
    """spaz must hold something above his head when it strikes, or he dies
    if another spaz is in the spaz's hands, kill it instead"""
    def __init__(self, actor: bs.Actor):
        super().__init__()
        # surprisingly short!
        self.actor = actor
        self.exists2 = False
        self.check_timer = None
        self.light = None
        self.blood_raindrops = []
        self.rain_timer = None
        self.shake_timer = None
        self.rain_sfx = None
        self.volume = 1.8
    
    def _check(self):
        if (
            random.random() >= 0.1
            or self.exists2
            or not self.actor().sorrowful
            or not self.actor()
            or not self.actor().node
            or not self.actor().is_alive()
            or (self.actor().kookoo and self.actor().kookoo.exists2)
        ):
            if not self.actor() or not self.actor().is_alive() or not self.actor().node:
                self.stop()
                return
            if not self.actor().sorrowful:
                self.stop()
                return
            return
        self.exists2 = True
        self.rain_sfx = bs.newnode(
            'sound',
            delegate=self,
            attrs={
                'sound': bs.getsound('srain'),
                'volume': self.volume,
            }
        )
        self.light = bs.newnode(
            'light',
            attrs={
                'radius': 0.5,
                'height_attenuated': False,
                'color': (0.4, 0, 0),
            },
        )
        bs.animate(self.light, 'intensity', 
            {
                0.0: 0, 
                1.0: 1.5, 
                2.5: 0.5,
                4.5: 5,
            }
        )
        bs.timer(3.5, self._shake)
        self.actor().node.connectattr('torso_position', self.light, 'position')
        self.rain_timer = bs.Timer(0.008, self._spawn_particle, repeat=True)
    
    def _resolve(self):
        if not self.actor().sorrowful:
            return
        self._delete()
        hnode = self.actor().node.hold_node
        # player not holding something
        if not hnode:
            if self.actor().parrying:
                self.actor().sugarcoat_overlay(sound='bellMed', image='sugarcoatparry')
                self.actor().mpa()
                return
            self.actor().shatter(True)
            self.actor().killed_by_entity('sorrow')
        # player is holding something
        elif self.actor().node.hold_node:
            sactor = hnode.getdelegate(bs.Actor)
            # if it's a spaz, kill it 
            if sactor and hnode.getnodetype() == 'spaz':
                sactor.shatter(True)
        bs.getsound('safter').play(1.5)
    
    def _shake(self):
        bs.getsound('swindy').play(1.5)
        self.shake_timer = bs.Timer(0.040, lambda: bs.camerashake(intensity=0.2), repeat=True)
        bs.timer(0.8, self._resolve)
        bs.timer(0.7, self.actor().dodge_warning)
    
    def _spawn_particle(self):
        # stop if we should
        if (
            not self.actor()
            or not self.actor().node
            or not self.actor().sorrowful
            or not self.actor().is_alive()
        ):
            self.stop()
            return
        if random.random() < 0.3:
            return
        # AGGH I HATE YOU MATERIALS
        if bs.app.config.get('squda_noparticles'):
            node = self.actor().node.hold_node
            if not node:
                return
            sactor = node.getdelegate(bs.Actor)
            if sactor and node.getnodetype() == 'bomb':
                sactor.defuse()
            return
        # we can assume where we wanna go is the actor's position
        ppos = self.actor().node.position
        # nice symmetric random 
        offs_x = (random.random() - 0.5) * 2
        offs_z = (random.random() - 0.5) * 2
        spread = 1.7  # controls how far it spreads
        pos = (
            ppos[0] + offs_x * spread,
            ppos[1] + 4.6,
            ppos[2] + offs_z * spread
        )
        blooddrop = BloodRaindrop(pos)
        blooddrop.autoretain()
        self.blood_raindrops.append(blooddrop)
    
    def _delete(self):
        # cleanup
        self.exists2 = False
        for rainy in self.blood_raindrops:
            rainy.handlemessage(bs.DieMessage(immediate=True))
        if self.light:
            self.light.delete()
            self.light = None
        if self.rain_sfx:
            self.rain_sfx.volume = 0
            self.rain_sfx.delete()
        if self.shake_timer:
            self.shake_timer = None
        if self.rain_timer:
            self.rain_timer = None
    
    def start(self):
        self.check_timer = bs.Timer(1.2, self._check, repeat=True)
    
    def stop(self):
        self.check_timer = None
        self._delete()
    
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            # we'll check if the spaz still exists and has us, and if it doesn't we can stop
            if self.actor() and self.actor().node and not self.actor().sorrowful:
                self.stop()
            elif not self.actor() or not self.actor().node:
                self.stop()
            else:
                self._delete()
        else:
            super().handlemessage(msg) # Augment standard behavior.