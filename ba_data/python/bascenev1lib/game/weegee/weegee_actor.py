"""WWEEEEGEEEEEHHHH"""
import bascenev1 as bs
import math
import random
from bascenev1lib.gameutils import SharedObjects

class Weegee(bs.Actor):
    """WWEEEEGEEEEEHHHH"""
    def __init__(self):
        super().__init__()
        self._can_tp = False
        seshplrs = self.getactivity().session.sessionplayers
        self.hitpoints = self.max_hitpoints = (
            5500 * len(seshplrs)
        )
        shared = SharedObjects.get()
        self._scale = scale = 13
        # this is our node, handles 
        # actual damage and stuff
        show_node = False
        self._dead = False
        self.node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'crate',
                'body_scale': scale,
                'mesh_scale': scale if show_node else 0,
                'mesh': bs.getmesh('tnt'),
                'color_texture': bs.gettexture('white'),
                'materials': [
                    shared.object_material, 
                    shared.no_object_footing_collide_mat, # don't collide with footing and objects
                    shared.disallow_pickup_material, # DONT FUCKIN ALLOW PICKUPs
                ], 
                'is_area_of_interest': True,
                'shadow_size': 0,
            }
        )
        # visual node.
        # just stays there and looks cool (no logic
        # except for animations)
        self.visual_node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'puck',
                'body_scale': 1,
                'mesh_scale': scale + 3,
                'mesh': bs.getmesh('weegee'),
                'color_texture': bs.gettexture('weegee'),
                'materials': [shared.object_material, shared.non_collide_mat],
                'shadow_size': 0,
            }
        )
        pos = (0, 5, -15)
        self._pos = pos
        # we rely on a combine to keep our position static.
        # by using connectattr, we don't rely on a timer to keep
        # resetting the position (game does it every sim-update)
        self.combine = bs.newnode(
            'combine', 
            owner=self.node, 
            attrs={
                'size': 3,
                'input0': pos[0],
                'input1': pos[1],
                'input2': pos[2],
            }
        )
        self.combine.connectattr('output', self.node, 'position')
        self.combine.connectattr('output', self.visual_node, 'position')
    
    def start_bouncy(self):
        bs.animate(
            self.visual_node,
            'mesh_scale',
            {
                0: self._scale,
                0.06: self._scale - 3.5,
                0.13: self._scale - 4,
                0.38: self._scale,
            },
            loop=True,
        )
        
    def random_tp(self):
        if not self._can_tp or not self.node:
            return
        pos = self._pos
        x_spread = 2
        self.combine.input0 = pos[0] + random.uniform(
            -x_spread, x_spread
        )
        
    def handlemessage(self, msg):
        if isinstance(msg, bs.HitMessage):
            self._can_tp = True
            damage = 0
            # punches hit us weaker
            iscale = 0.32 if msg.hit_type == 'punch' else 1
            if not msg.flat_damage:
                # "code from bombgeon
                # i already knew this method but i had a problem
                # still thanks to gummy for figuring this out"
                # yeah thanks efro for fucking hardcoding damage
                # --------------------------------------------
                # this is SO impractical dude.
                calculator = bs.newnode(
                    'spaz', 
                    attrs={
                        'style': 'ali', # .. so we dont see the eyes.
                        'is_area_of_interest': False, # Dont wanna take that chance
                    }
                )
                # calculate a good enough position based on distance
                center = self.node.position
                dx = abs(msg.pos[0] - center[0])
                dy = abs(msg.pos[1] - center[1])
                dz = abs(msg.pos[2] - center[2])
                dist = math.sqrt(dx + dy + dz)
                # bit of leeway so damage isnt too random
                leeway_scale = 0.2
                pos = (
                    msg.pos[0] + (dist * leeway_scale),
                    msg.pos[1] + (dist * leeway_scale),
                    msg.pos[2] + (dist * leeway_scale),
                )
                # bombs need a position i guess ???    
                calculator.handlemessage( 
                    'stand',
                    pos[0],
                    pos[1],
                    pos[2],
                    90,
                )
                
                # damage, yadda yadda
                calculator.handlemessage(
                    'impulse',
                    msg.pos[0],
                    msg.pos[1],
                    msg.pos[2],
                    msg.velocity[0],
                    msg.velocity[1],
                    msg.velocity[2],
                    msg.magnitude * iscale,
                    msg.velocity_magnitude * iscale,
                    msg.radius,
                    1,
                    msg.force_direction[0],
                    msg.force_direction[1],
                    msg.force_direction[2],
                )
                # Uh-uh give us the damage and ur done pally
                damage = 0.22 * calculator.damage
                calculator.delete()
            else:
                damage = msg.flat_damage
            # update hp
            self.hitpoints -= int(damage)
            if self.hitpoints < 0:
                self.hitpoints = 0
                if not self._dead:
                    self._dead = True
                    self.getactivity().weegee_beaten()
            # tell activitty to update the bar and such
            self.getactivity()._update_for_stats()
        else:
            return super().handlemessage(msg)
        return None