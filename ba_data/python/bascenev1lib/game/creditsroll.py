""" Defines our Credits-Roll sequence. """
from __future__ import annotations
import bascenev1 as bs
import bauiv1 as bui
import babase as ba

from typing import TYPE_CHECKING, override


class Player(bs.Player['Team']):
    """Our player type for this game."""

class Team(bs.Team[Player]):
    """Our team type for this game."""

class CreditsActivity(bs.TeamGameActivity[bs.Player, bs.Team]):
    """Simple activity for rolling credits."""
    name = ''
    description = ''
    default_music = bs.MusicType.CREDITS
    suppress_zoomtext = True
    show_controls_guide = False
    allow_pausing = False
    
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        assert bs.app.classic is not None
        return bs.app.classic.getmaps('credits')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._text_node = None
  
    def on_transition_in(self) -> None:
        super().on_transition_in()
        
        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'
    
    def on_begin(self) -> None:
        super().on_begin()
        self._start_credits()
        bs.timer(193.0, self.dogoodbye)
        self.showlogo('logo2')
        bs.timer(27.0, lambda: self._start_character_scroll('spaz', leftside=True))
        bs.timer(37.0, lambda: self._start_character_scroll('susie',))
        bs.timer(47.0, lambda: self._start_character_scroll('kris', leftside=True))
        bs.timer(57.0, lambda: self._start_character_scroll('noobs'))
        bs.timer(67.0, lambda: self._start_character_scroll('mell', leftside=True)) # SIX SEVEEEEENNNNNNN
        bs.timer(77.0, lambda: self._start_character_scroll('ninja'))
        bs.timer(87.0, lambda: self._start_character_scroll('rayman', leftside=True))
        bs.timer(97.0, lambda: self._start_character_scroll('bowser'))
        bs.timer(107.0, lambda: self._start_character_scroll('noise', leftside=True))
        bs.timer(117.0, lambda: self._start_character_scroll('ralsei'))
        bs.timer(127.0, lambda: self._start_character_scroll('orangecap', leftside=True))
        bs.timer(137.0, lambda: self._start_character_scroll('knight'))
        
        
    def _start_character_scroll(self, tex: str | None = None, leftside: bool = False):
        """
        Shows character cards per request. See on_begin.
        """
        texture = bs.gettexture(tex)
        
        # Create image node
        self._char_node = bs.newnode('image', attrs={
            'texture': texture,
            'position': (0, 0), 
            'scale': (300, 300),
            'opacity': 1.0,
            'absolute_scale': True,
            'attach': 'center'
        })
        # If specified to go leftside, we will go to leftside.
        if leftside:
            bs.animate_array(self._char_node, 'position', 2, {
                0.5: (-500, -1000),
                55.0: (-500, 1000)  # scroll up slowly
            })
        else:
            bs.animate_array(self._char_node, 'position', 2, {
                0.5: (500, -1000),
                55.0: (500, 1000)  # scroll up slowly
            })
        bs.timer(60.0, self._char_node.delete)
    
    def showlogo(self, tex: str | None = None):
        """
        Shows LOGOOO per request. idk im just copy pastin atp
        """
        texture = bs.gettexture(tex)
        
        # Create image node
        self._logo_node = bs.newnode('image', attrs={
            'texture': texture,
            'position': (0, 0), 
            'scale': (900, 900),
            'opacity': 1.0,
            'absolute_scale': True,
            'attach': 'center'
        })
        bs.animate_array(self._logo_node, 'position', 2, {
            5.0: (0, 0),
            40.0: (0, 600) # scroll up slowly
        })
        bs.timer(45.0, self._logo_node.delete)
        
    def dogoodbye(self):
        """
        This is a long one. VEEERY long one.
        Imagine this is spaz talking to you. lel.
        """
        session = self.session
        ba.screenmessage('Uh... Hi there.', color=(0.5, 0.25, 1.0))
        bui.getsound('spazAttack02').play()
        ba.apptimer(2.0, lambda: ba.screenmessage('Name\'s Spaz. \nYa probably already met me.', color=(0.5, 0.25, 1.0)))
        ba.apptimer(2.0, lambda: bui.getsound('spazAttack04').play())
        ba.apptimer(4.5, lambda: ba.screenmessage('I just wanted to say...', color=(0.5, 0.25, 1.0)))
        ba.apptimer(4.5, lambda: bui.getsound('spazAttack01').play())
        ba.apptimer(5.5, lambda: ba.screenmessage('Um...', color=(0.5, 0.25, 1.0)))
        ba.apptimer(5.5, lambda: bui.getsound('spazImpact02').play())
        ba.apptimer(6.8, lambda: ba.screenmessage('Thanks for taking the time to play BombSquda, I guess.', color=(0.5, 0.25, 1.0)))
        ba.apptimer(6.8, lambda: bui.getsound('spazJump03').play())
        ba.apptimer(9.0, lambda: ba.screenmessage('Even tho this was Mell-', color=(0.5, 0.25, 1.0)))
        ba.apptimer(9.0, lambda: bui.getsound('spazAttack04').play())
        ba.apptimer(10.5, lambda: ba.screenmessage('Dare I say, Meliso... Heh.', color=(0.5, 0.25, 1.0)))
        ba.apptimer(10.5, lambda: bui.getsound('spazJump01').play())
        ba.apptimer(13.0, lambda: ba.screenmessage('Ahem. Mell\'s passion project for making stupid stuff...', color=(0.5, 0.25, 1.0)))
        ba.apptimer(13.0, lambda: bui.getsound('spazAttack02').play())
        ba.apptimer(16.5, lambda: ba.screenmessage('You still wasted your time, playing this modpack when you could play others.', color=(0.5, 0.25, 1.0)))
        ba.apptimer(16.5, lambda: bui.getsound('spazJump03').play())
        ba.apptimer(18.0, lambda: ba.screenmessage('So, even if you did or didn\'t support the project... \n..you still took a lot of part in it.', color=(0.5, 0.25, 1.0)))
        ba.apptimer(18.0, lambda: bui.getsound('spazJump04').play())
        ba.apptimer(22.0, lambda: ba.screenmessage('I just wanted to say...', color=(0.5, 0.25, 1.0)))
        ba.apptimer(22.0, lambda: bui.getsound('spazAttack03').play())
        ba.apptimer(24.0, lambda: ba.screenmessage('One way or another, We thank you for making this real.', color=(0.5, 0.25, 1.0)))
        ba.apptimer(24.0, lambda: bui.getsound('spazAttack01').play())
        ba.apptimer(27.0, lambda: ba.screenmessage('And of course, keep on Bombsquaddin\'!', color=(0.5, 0.25, 1.0)))
        ba.apptimer(27.0, lambda: bui.getsound('spazAttack02').play())
        ba.apptimer(30.0, lambda: ba.screenmessage(f'See ya, {self.you}.', color=(0.5, 0.25, 1.0)))
        ba.apptimer(30.0, lambda: bui.getsound('spazJump03').play())
        ba.apptimer(32.0, session.end)
        # there's the fuckin end!

    def _start_credits(self) -> None:
        """Create scrolling credits."""
        self.you = bui.app.plus.get_v1_account_display_string()

        # Create the text node off-screen at the bottom
        self._text_node = bs.newnode("text", attrs={
            "text": bs.Lstr(resource='creditsText', subs=[('${NAME}', self.you)]),
            "position": (0, 0),
            "scale": 1.5,
            "h_attach": "center",
            "v_attach": "center",
            "h_align": "center",
            "color": (1, 1, 1),
            "flatness": 0.5,
            "shadow": 0.5,
            "maxwidth": 800
        })

        bs.animate_array(
            self._text_node,
            "position", 2,  # 2 = number of components (x, y)
            {
                5.0: (0, -500),   # start position
                181.0: (0, 2600)    # end position
            }
        )

