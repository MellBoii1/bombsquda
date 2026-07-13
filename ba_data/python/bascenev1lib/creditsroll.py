""" Defines our Credits-Roll sequence. """
from __future__ import annotations
import bascenev1 as bs
import bauiv1 as bui
import babase as ba

from typing import TYPE_CHECKING, override

LENGTH = 77
TEXT_START = 5.0
TEXT_END = LENGTH - 4.0
        
class CreditsActivity(bs.GameActivity[bs.Player, bs.Team]):
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
        return ['CREDITS']
    
    @override
    def __init__(self, settings: dict):
        super().__init__(settings)
        self._text_node = None
        self.allow_emeralds = False
        self.length = LENGTH
  
    def on_transition_in(self) -> None:
        super().on_transition_in()
        
        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'
    
    def on_begin(self) -> None:
        super().on_begin()

        self._start_credits()
        bs.timer(self.length + 5, self.leave)
        self.showlogo()
        bs.timer(self.length - 16, self.showlogo2)
    
    def showlogo(self):
        # Create image node
        node = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('title_hd'),
                'scale': (800, 200),
                'absolute_scale': True,
            }
        )
        bs.animate_array(node, 'position', 2, {
            TEXT_START: (0, 0),
            TEXT_START + 8: (0, 600) # scroll up slowly
        })
        bs.timer(45.0, node.delete)
        
    def showlogo2(self):
        # Create image node
        node = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('title_hd'),
                'position': (0, -500), 
                'scale': (800, 200),
                'absolute_scale': True,
            }
        )
        # create text
        node2 = bs.newnode("text", 
            attrs={
                "text": bs.Lstr(resource='thanksForPlaying'),
                "position": (0, -800),
                "scale": 1.7,
                "h_attach": "center",
                "v_attach": "center",
                "h_align": "center",
                "color": (1, 1, 1),
            }
        )
        
        # create a math node
        # (used to add a bit y offset)
        mathnode = bs.newnode(
            'math',
            owner=node,
            attrs={'input1': (0, 100), 'operation': 'add'},
        )
        node.connectattr('position', mathnode, 'input2')
        mathnode.connectattr('output', node2, 'position')
        bs.animate_array(node, 'position', 2, {
            0.0: (0, -800),
            9.0: (0, 0) # scroll up slowly
        })
        
    def leave(self):
        session = self.session
        bui.getsound('thankforplay').play()
        bs.timer(4.5, session.end)

    def _start_credits(self) -> None:
        """Create scrolling credits."""

        # Create the text node off-screen at the bottom
        self._text_node = bs.newnode("text", 
            attrs={
                "text": bs.Lstr(resource='creditsWindow.text'),
                "position": (0, -500),
                "scale": 1.5,
                "h_align": "center",
                "maxwidth": 800
            }
        )
        bs.animate_array(
            self._text_node,
            "position", 2,  # 2 = number of components (x, y)
            {
                TEXT_START: (0, -500),   # start position
                TEXT_END: (0, 4500)    # end position
            }
        )
    
    @override
    def spawn_player_spaz(
        self,
        player: PlayerT,
        position: Sequence[float] = (0, 0, 0),
        angle: float | None = None,
    ) -> PlayerSpaz:
        return super().spawn_player_spaz(player=player,position=(0, 5, -2))
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(bs.Player)
            self.respawn_player(player)
        else:
            return super().handlemessage(msg)
        return None

