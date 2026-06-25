"""Notification for currently playing music."""
from typing import override, Any

import bascenev1 as bs
import bauiv1 as bui
import babase as ba

RAINBOW_SPEED = 0.6  # determine speed
RAINBOW_COLORS = [
    (1.0, 0.0, 0.0),  # red
    (1.0, 0.5, 0.0),  # orange
    (1.0, 1.0, 0.0),  # yellow
    (0.0, 1.0, 0.0),  # green
    (0.0, 1.0, 1.0),  # cyan
]

def build_rainbow(speed: float):
    colors = RAINBOW_COLORS + [RAINBOW_COLORS[0]]
    step = speed / (len(colors) - 1)
    return {
        i * step: color
        for i, color in enumerate(colors)
    }

RAINBOW = build_rainbow(RAINBOW_SPEED)

class MusicNotifier:
    """A simple NOT ACTOR because actors suck lol for a notification 
    of currently playing music. NOT recommended for use,
    as it already gets used in :meth:bascenev1._music.setmusic:meth:."""
    _STORENAME = bs.storagename()
    
    def __init__(
        self, 
        music_type: bs.MusicType, 
        scale: float = 1.5, 
        position: tuple[float, float] = (-500, 200),
    ):
        super().__init__()
        self.node: bs.Node | None = None
        music_data = bs._music.get_music_value(music_type)
        # Time to stay onscreen.
        time = 4
        # If the music data is a regular string (so let's say,
        # just the name and artist, our legacy type) let's convert to a dict
        if isinstance(music_data, str):
            tlist = music_data.split('-')
            music_data = {
                'title': tlist[0].strip(),
                'artist': tlist[1].strip(),
                'artist_keyword': 'by', # Assume it's from a artist.
            }
        # If a notifier already exists, we just use that.
        session = bs.getsession()
        notifier = session.customdata.get(self._STORENAME)
        if notifier:
            if notifier.exists():
                notifier.set_data(music_data)
                notifier.delay_transition(time)
                return
        # Otherwise, save us, then continue.
        session.customdata[self._STORENAME] = self
        # UI scale. Used to determine 
        # whether to use a bigger scale overall.
        uiscale = bui.app.ui_v1.uiscale
        # Position values.
        ypos = 0
        xpos = 635
        offscrX = 1500
        # Whether we'll stay on the front (like a
        # ui widget) or not (regular images).
        front = True

        # Scale.
        tscale = (
            1.3 if uiscale is bui.UIScale.SMALL
            else 0.8
        )
        i_scale = (
            1.3 if uiscale is bui.UIScale.SMALL
            else 0.6
        )
        # music title node
        self.node = bs.newnode(
            'text',
            attrs={
                'position': (offscrX, ypos + 15),
                'scale': tscale,
                'shadow': 0.5,
                'flatness': 0.5,
                'h_align': 'right',
                'v_attach': 'bottom',
                'front': front,
            }
        )
        bs.animate_array(
            self.node, 'color', 
            3, RAINBOW, loop=True
        )
        # artist name  node
        self.subnode = bs.newnode(
            'text',
            delegate=self,
            owner=self.node,
            attrs={
                'position': (offscrX, ypos),
                'scale': tscale - 0.2,
                'flatness': 0.9,
                'opacity': 0.5,
                'h_align': 'right',
                'v_attach': 'bottom',
                'front': front,
            }
        )
        # disc that spins round
        self.imgnode = bs.newnode(
            'image',
            delegate=self,
            owner=self.node,
            attrs={
                'texture': bs.gettexture('coverDisc'),
                'attach': 'bottomCenter',
                'scale': (300 * i_scale, 300 * i_scale),
                'opacity': 0.5,
            }
        )
        self.set_data(music_data)
        # animations
        def posi(node):
            bs.animate_array(
                node,
                "position",
                2,
                {
                    0.0: (offscrX, node.position[1]),
                    0.5: (xpos, node.position[1]),
                }
            )
        self._node_opacities = {}
        def opac(node):
            bs.animate(
                node,
                "opacity",
                {
                    0.0: 0.0,
                    0.5: node.opacity,
                }
            )
        # for every node, fade in and move in
        for node in [
            self.node, 
            self.subnode, 
            self.imgnode,
        ]:
            self._node_opacities[node] = node.opacity
            opac(node)
            posi(node)
        def add_one():
            if not self.imgnode:
                self.rotatetimer = None
                return
            self.imgnode.rotate += 5
        # timers
        self.rotatetimer = bs.BaseTimer(0.01, add_one, repeat=True)
        self.transition_timer = bs.Timer(time, self._trans_out)
        
    
    def set_data(self, data: dict):
        keyw = bs.Lstr(
            t=(
                'artistKeywords', 
                data.get('artist_keyword')
            )
        )
        artist_text = bs.Lstr(
            value='${A} ${B}',
            subs=[
                ('${A}', keyw),
                ('${B}', data.get('artist')),
            ]
        )
        text = bs.Lstr(
            value='${A} ~ ${B}',
            subs=[
                ('${A}', ba.charstr(ba.SpecialChar.DICE_BUTTON3)),
                ('${B}', data.get('title')),
            ]
        )
        self.node.text = text
        self.subnode.text = artist_text
    
    def _trans_out(self):
        def opac(node):
            bs.animate(
                node,
                "opacity",
                {
                    0.0: node.opacity,
                    1: 0,
                }
            )
        # for every node, fade in and move in
        for node in [
            self.node, 
            self.subnode, 
            self.imgnode,
        ]:
            if node:
                opac(node)
        self.death_timer = bs.Timer(1, self.delete)
    
    def delay_transition(self, time: float):
        for node in [
            self.node, 
            self.subnode, 
            self.imgnode,
        ]:
            if node:
                node.opacity = self._node_opacities[node]
        self.transition_timer = bs.Timer(time, self._trans_out)
        self.death_timer = None
    
    def delete(self):
        if self.node:
            self.node.delete()
        
    def exists(self):
        return bool(self.node)