"""Module for a intro activity and session"""
import bascenev1 as bs
import babase as ba
import bauiv1 as bui
import bascenev1lib.intros.main as main
from bascenev1lib.actor.text import Text
import random

from typing import override, Any
from bascenev1lib.intros.messages import (
    IntroStartedMessage, 
    IntroStoppedMessage
)

class IntroSession(bs.Session):
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.setactivity(bs.newactivity(IntroActivity))

class IntroActivity(bs.GameActivity[bs.Player, bs.Team]):
    """Simple activity for showing a random intro on boot-up."""
    name = ''
    description = ''
    suppress_zoomtext = True
    show_controls_guide = False
    allow_pausing = False
    
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Nothing']
    
    @override
    def __init__(self, settings: dict):
        super().__init__(settings)
        # make a bg so everything goes nice
        self.bg = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'fill_screen': True,
                'texture': bs.gettexture('black'),
            },
        )
        self.intro = None
        self.skip_button = None
        self.skip_info = None
        self.allow_emeralds = None
  
    def on_transition_in(self) -> None:
        super().on_transition_in()
        chosen = random.choice(main.intro_list)
        self.intro = chosen()
        with ba.ContextRef.empty():
            self.skip_button = bui.buttonwidget(
                autoselect=True,
                position=(-1000, -600),
                size=(2000, 1500),
                texture=bui.gettexture('empty'),
                label='',
                enable_sound=False,
                on_activate_call=bs.WeakCall(self.handle_button_clicked),
            )
        
    def handle_button_clicked(self):
        with self.context:
            if not self.skip_info:
                text = Text(
                    text=bs.Lstr(resource='pressAnythingToSkipIntro'),
                    transition=Text.Transition.IN_BOTTOM,
                    transition_out_delay=2.5,
                    h_attach=Text.HAttach.RIGHT,
                    v_attach=Text.VAttach.BOTTOM,
                    h_align=Text.HAlign.RIGHT,
                    position=(-20, 20),
                    scale=1.3,
                )
                text.autoretain()
                self.skip_info = text.node
            else:
                if not self.skip_info:
                    return
                bs.getsound('swish').play()
                self.go_to_menu()
    
    def go_to_menu(self):
        if self.intro.active:
            self.intro.stop(tell_activity=False)
        if self.skip_button:
            self.skip_button.delete()
        classic = bs.app.classic
        classic.return_to_main_menu_session_gracefully()
    
    @override
    def handlemessage(self, msg: Any):
        if isinstance(msg, IntroStartedMessage):
            pass
        elif isinstance(msg, IntroStoppedMessage):
            self.go_to_menu()
        else:
            super().handlemessage(msg)