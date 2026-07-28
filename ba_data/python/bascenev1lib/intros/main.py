"""Module for the Intro class"""
import bascenev1 as bs
from bascenev1lib.intros.messages import (
    IntroStartedMessage, 
    IntroStoppedMessage
)
from typing import override

intro_list = []

PATH = 'intro_assets/'
def register(cls):
    intro_list.append(cls)
    return cls

class Intro:
    def __init__(self):
        self.active: bool = False
        bs.timer(3.3, self.start)
    
    def start(self):
        """Called when the intro should
        start playing itself."""
        bs.getactivity().handlemessage(
            IntroStartedMessage()
        )
        self.active = True
    
    def stop(self, tell_activity: bool = True):
        """Called when the intro should
        stop everything, like timers, and stop."""
        if tell_activity:
            bs.getactivity().handlemessage(
                IntroStoppedMessage()
            )
        self.active = False

@register
class SegaIntro(Intro):
    @override
    def start(self):
        from bascenev1lib.actor.image_looped import LoopingImageAnimation
        from bascenev1lib.actor.nodejumper import ImageJumper
        self.bg = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'fill_screen': True,
                'texture': bs.gettexture('white2'),
            },
        )
        offX = 1000
        image = LoopingImageAnimation(
            prefix=f'{PATH}spaz_run',
            frame_count=4,
            frame_delay=0.01,
            scale=(200, 200),
            position=(offX, 0),
        )
        image2 = LoopingImageAnimation(
            prefix=f'{PATH}spaz_run_flipped',
            frame_count=4,
            frame_delay=0.01,
            scale=(200, 200),
            position=(offX, 0),
        )
        image3 = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture(f'{PATH}spaz_jump'),
                'position': (-offX, 0), 
                'scale': (200, 200),
                'opacity': 1.0,
            }
        )
        sc = 1.4
        logo_image = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('mell_logo'),
                'position': (offX, 0), 
                'scale': (512 * sc, 256 * sc),
                'opacity': 1.0,
            }
        )
        
        def animate1():
            bs.animate_array(
                image.node, 
                'position', 
                2,
                {
                    0: (offX, 0),
                    1: (-offX, 0),
                }
            )
            bs.getsound('spinzoom').play()
        def animate2():
            bs.animate_array(
                image2.node, 
                'position', 
                2,
                {
                    0: (-offX, 0),
                    1: (offX, 0),
                }
            )
            bs.getsound('spinzoom').play()
        
        def animate3():
            bs.animate_array(
                image.node, 
                'position', 
                2,
                {
                    0: (offX, 0),
                    1: (-offX, 0),
                }
            )
            bs.animate_array(
                logo_image, 
                'position', 
                2,
                {
                    0: (offX, 0),
                    0.6: (0, 0),
                }
            )
            bs.getsound('spinzoom').play()
        def animate4():
            ImageJumper.jump_to_position(
                image3, 
                target_pos=(-370, 0),
                time=1.0,
            )
            bs.getsound('smb1_jump').play()
        def animate5():
            image3.texture = bs.gettexture(f'{PATH}spaz_peace')
            bs.getsound('voicelines/spaz/jump01').play()
            bs.timer(4, self.stop)
        animate1()
        bs.timer(1, animate2)
        bs.timer(2, animate3)
        bs.timer(4, animate4)
        bs.timer(5, animate5)

@register
class MarioMakerIntro(Intro):
    def __init__(self):
        import mellboii.mell_resources as mell
        import random
        super().__init__()
        bs.getsound('slideWhistleReverse')
        bs.getsound('slideWhistle')
        bs.getsound('mortal_damage')
        bs.getsound('ring_spill')
        bs.getsound('cheer2')
        bs.getsound('smashDied')
        self.scream = bs.getsound(random.choice(mell.screams))
    @override
    def start(self):
        from bascenev1lib.actor.nodejumper import ImageJumper
        import mellboii.mell_resources as mell
        self.bg = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'fill_screen': True,
                'texture': bs.gettexture('white2'),
            },
        )
        sc = 1.4
        logo_image = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('mell_logo'),
                'position': (0, 0), 
                'scale': (512 * sc, 256 * sc),
                'opacity': 1.0,
            }
        )
        hsc = 1.4
        hand = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture(f'{PATH}spaz_mm_hand'),
                'position': (5000, 0), 
                'scale': (256 * hsc, 512 * hsc),
                'opacity': 1.0,
            }
        )
        def end_it():
            bs.getsound('smashDied').play()
            bs.getsound('cheer2').play()
            bs.timer(3, self.stop)
        def jump_logo():
            ImageJumper.jump_to_position(
                logo_image,
                target_pos=(4000, 0),
                time=3,
            )
            bs.getsound('mortal_damage').play()
            bs.getsound('ring_spill').play()
            self.scream.play()
            bs.timer(1, end_it)
        def animatehand():
            xoffs = 500
            yoffs = 500
            animate_array = {
                0: (579 - xoffs, -260 - yoffs),
                0.71: (579 - xoffs, 121 - yoffs),
                0.85: (607 - xoffs, 247 - yoffs),
                0.92: (527 - xoffs, 254 - yoffs),
                1.02: (445 - xoffs, 260 - yoffs),
                1.13: (368 - xoffs, 251 - yoffs),
                1.23: (320 - xoffs, 245 - yoffs),
                1.34: (288 - xoffs, 236 - yoffs),
                1.59: (282 - xoffs, 233 - yoffs),
                1.7: (289 - xoffs, 229 - yoffs),
                1.81: (315 - xoffs, 223 - yoffs),
                1.91: (402 - xoffs, 214 - yoffs),
                2.02: (454 - xoffs, 209 - yoffs),
                2.12: (477 - xoffs, 201 - yoffs),
                2.31: (477 - xoffs, 201 - yoffs),
                2.42: (419 - xoffs, 177 - yoffs),
                2.54: (400 - xoffs, 168 - yoffs),
                2.72: (399 - xoffs, 168 - yoffs),
                3.28: (520 - xoffs, 166 - yoffs),
                3.35: (800 - xoffs, 300 - yoffs),
                4: (800 - xoffs, 300 - yoffs),
                5: (800 - xoffs, -500 - yoffs),
            }
            bs.getsound('slideWhistle').play()
            bs.timer(4, bs.getsound('slideWhistleReverse').play)
            bs.animate_array(
                hand, 
                'position', 
                2, 
                animate_array
            )
            bs.timer(3.3, jump_logo)
        bs.timer(3, animatehand)

@register
class MarioKartIntro(Intro):
    def __init__(self):
        import mellboii.mell_resources as mell
        super().__init__()
        self.logos = []
        bs.getsound('mk64_logo')
        
    @override
    def start(self):
        from bascenev1lib.actor.image_looped import LoopingImageAnimation
        global this_op
        global delay
        hsc = 1.5
        this_op = 0.7
        delay = 0.3
        logo = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture(f'{PATH}logo3d_frame1'),
                'position': (0, 0), 
                'scale': (512 * hsc, 256 * hsc),
            }
        )
        def part2():
            global delay
            bs.timer(0.3, logo.delete)
            bs.getsound('mk64_logo').play()
            def make():
                logo = LoopingImageAnimation(
                    prefix=f'{PATH}logo3d_frame',
                    frame_count=8,
                    frame_delay=0.2,
                    scale=(512 * hsc, 256 * hsc),
                )
                if len(self.logos) == 0:
                    opacity = 1
                else:
                    opacity = 0
                logo.node.opacity = opacity
                self.logos.append(logo)
            for _ in range(15):
                bs.timer(delay, make)
                delay += 0.01
            def speedup():
                for logo in self.logos:
                    logo.frame_delay -= 0.02
            def fade_in_others():
                global this_op
                for logo in self.logos:
                    if logo.node.opacity != 1:
                        bs.animate(
                            logo.node, 
                            'opacity',
                            {
                                0.0: 0,
                                1.0: this_op,
                            },
                        )
                        this_op -= 0.1
            def fadeout():
                white_fadeout = bs.newnode('image', 
                    attrs={
                        'texture': bs.gettexture('white2'), 
                        'fill_screen': True,
                        'opacity': 0,
                    }
                )
                bs.animate(
                    white_fadeout, 
                    'opacity',
                    {
                        0.0: 0,
                        1.5: 1,
                    },
                )
                bs.timer(1.9, self.stop)
            bs.timer(1.3, speedup)
            bs.timer(2.3, speedup)
            bs.timer(3.3, speedup)
            bs.timer(3.5, speedup)
            bs.timer(3.8, speedup)
            bs.timer(4.1, speedup)
            bs.timer(4.5, speedup)
            bs.timer(5.0, speedup)
            bs.timer(4, fade_in_others)
            bs.timer(7, fadeout)
        bs.timer(1.5, part2)
        
