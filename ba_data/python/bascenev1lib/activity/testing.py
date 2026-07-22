"""Yeah. I'm doing it buddie."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING, override, Callable
from bascenev1lib.dialog import DialogueManager
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.image_looped import LoopingImageAnimation
from bascenev1lib.actor.portalradio import PortalRadio
from bascenev1lib.actor.nodejumper import ImageJumper
from bascenev1lib import eb_engine
import bascenev1 as bs
import random
import time

if TYPE_CHECKING:
    from typing import Any, Sequence

# session..
class TestSession(bs.Session):
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.lobby_autojoin = True
        self.setactivity(bs.newactivity(TestActivity))
    
class TestActivity(bs.GameActivity[bs.Player, bs.Team]):
    name = ''
    description = ''
    announce_player_deaths = True
    suppress_zoomtext = True
    default_music = bs.MusicType.SURVEY
    
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Nothing']
        
    def __init__(self, settings: dict):
        super().__init__(settings)
        self.text_timer = None
        self.waiting_on_join = False
        
    @override
    def on_begin(self):
        super().on_begin()
        node = bs.newnode(
            'image',
            attrs={
                'fill_screen': True,
                'texture': bs.gettexture('white'),
                'color': (0, 0, 0),
            },
        )
        spaz = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('spaz_comad'),
                'color': (1, 1, 1),
                'scale': (100, 100),
            },
        )
        bs.animate(spaz, 'opacity', {0.1: 0, 2: 1})
        def text2():
            self.make_floaty_text('You must wake up, SPAZ...', callback=self.ask_to_join)
        bs.timer(3.0, lambda: self.make_floaty_text('SPAZ...', callback=text2))
    
    def next_activity(self):
        node = bs.newnode(
            'image',
            attrs={
                'fill_screen': True,
                'texture': bs.gettexture('white2'),
                'color': (1, 1, 1),
            },
        )
        bs.animate(node, 'opacity', {0: 0, 2: 1})
        bs.timer(2, lambda: self.session.setactivity(bs.newactivity(TestActivity2)))
    
    def text3(self):
        self.make_floaty_text('Meliso has returned, and is coming\nback stronger than ever...', callback=self.text4)
    def text4(self):
        self.make_floaty_text('You must gather your friends...', callback=self.text5)
    def text5(self):
        self.make_floaty_text('..and together, with your strength...', callback=self.text6)
    def text6(self):
        self.make_floaty_text('...stop Meliso from causing total destruction.', callback=self.text7)
    def text7(self):
        self.make_floaty_text('The SQUDA\'s fate lies on you, SPAZ...', callback=self.text8)
    def text8(self):
        self.make_floaty_text('SPAZ... wake up...', callback=self.text9)
    def text9(self):
        self.make_floaty_text('...SPAZ..!', callback=self.next_activity)
    
    def ask_to_join(self):
        self.waiting_on_join = True
        if len(self.players) > 0:
            #self.text3()
            self.next_activity()
            return
        textnode = self.textnode_pressbtn = bs.newnode(
            'text',
            attrs={
                'text': bs.Lstr(resource='pressToContinueActivity'),
                'h_align': 'center',
                'position': (0, 150),
                'scale': 1.3,
                'opacity': 0,
            }
        )
        bs.animate(textnode, 'opacity', {0: 0, 0.5: 0.5})
    
    def on_player_join(self, player: bs.Player):
        if not self.waiting_on_join:
            return
        bs.animate(self.textnode_pressbtn, 'opacity', {0: 0.5, 1: 0})
        self.text3()
        
    def make_floaty_text(
        self, 
        text: str, 
        callback: Callable | None = None
    ):
        full_text = text
        self.current_text = ''
        self.text_index = 0
        textnode = bs.newnode(
            'text',
            attrs={
                'text': self.current_text,
                'h_align': 'center',
                'position': (0, 190),
                'scale': 1.3
            }
        )
        pos = textnode.position
        num1 = -0.2
        num2 = 0.2
        def fade_out():
            def deleteit():
                textnode.delete()
                if callback:
                    callback()
            bs.animate(textnode, 'opacity', {0: 1, 1: 0})
            bs.timer(1, deleteit)
        def _type_tick():
            if self.text_index >= len(full_text):
                self.text_timer = None
                bs.timer(1.7, fade_out)
                return
            char = full_text[self.text_index]
            self.text_index += 1
            self.current_text += char
            textnode.text = self.current_text
        self.text_timer = bs.Timer(0.05, _type_tick, repeat=True)

class TestActivity2(bs.GameActivity[bs.Player, bs.Team]):
    name = ''
    description = ''
    announce_player_deaths = True
    suppress_zoomtext = True
    
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Nothing']
        
    def __init__(self, settings: dict):
        super().__init__(settings)
        self.text_timer = None
    
    def on_begin(self):
        bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white'),
                'color': (0.2, 0.2, 0.6),
                'fill_screen': True,
            },
        )
        self.scene = eb_engine.Scene(position=(600, 340), texture='special', scale=1.0)
        spaz = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('spaz_comad'),
                'color': (1, 1, 1),
                'scale': (100, 100),
            },
        )
        self.spaz_anim_image = spaz
        DialogueManager(
            [
                {
                    "text": "WAKE UP DUMBASS!!!!!",
                    "sound": "tap",
                },
                {
                    "text": "...jeez, does this guy not hear me?!",
                    "sound": "tap",
                },
                {
                    "text": "..oh wait, I have an idea.",
                    "sound": "tap",
                },
                {
                    "text": "{eval=bs.getactivity().spaz_gets_bricked()}",
                    "interrupt": True,
                },
            ],
        )
    
    def spaz_gets_bricked(self):
        bs.getsound('hook_throw').play()
        brick = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('windowHSmallVSmall'),
                'color': (0.9, 0.2, 0.2),
                'scale': (300, 300),
                'position': (0, 0),
                'absolute_scale': True,
            },
        )
        time = 1.5
        bs.animate_array(
            brick, 
            'scale', 
            2,
            {
                0.0: (500, 500),
                time * 0.5: (300, 300),
                time: (30, 30),
            }
        )
        bs.animate(brick, 'rotate',
            {
                0: 0,
                time: 180,
            }
        )
        ImageJumper.jump_to_position(
            brick, 
            target_pos=self.spaz_anim_image.position,
            time=time,
            height=500,
        )
        def gets_hit():
            bs.getsound('bigImpact2').play()
            ImageJumper.jump_image(brick, fall_speed=-700, jump_force=600)
            self.spaz_anim_image.delete()
            LoopingImageAnimation(
                scale=(100, 100), 
                prefix='spaz_wakeup', 
                frame_count=7, 
                loop=False,
                frame_delay=0.05,
            )
            self.scene._move(y=-15)
            
        bs.timer(time, gets_hit)
    
    @override
    def spawn_player(self, player: bs.Player):
        return
        
        

    
