"""Class for an Ultrakill-style meter"""
# WELCOME TO ULTRA JANK HELL!
from __future__ import annotations
import bascenev1 as bs
import babase as ba
import fromgoverhaul.mell_resources as mell

# List of our ranks (a letter corresponding to a string and color).
SCORE_RANKS = {
    'D': (bs.Lstr(resource='ultrakillMeterRankD'), (1, 0.5, 0), 'player_unready'),
    'C': (bs.Lstr(resource='ultrakillMeterRankC'), (0, 0.8, 0.2), 'win'),
    'B': (bs.Lstr(resource='ultrakillMeterRankB'), (0.8, 0.8, 0), 'explosion01'),
    'A': (bs.Lstr(resource='ultrakillMeterRankA'), (1, 0.5, 0), mell.screams[0]),
    'S': (bs.Lstr(resource='ultrakillMeterRankS'), (1, 0.3, 0.3), 'supertrans'),
    'SS': (bs.Lstr(resource='ultrakillMeterRankSS'), (1, 0.1, 0.1), 'spazFall01'),
    'SSS': (bs.Lstr(resource='ultrakillMeterRankSSS'), (1, 0, 0), 'gooditem'),
    'U': (bs.Lstr(resource='ultrakillMeterRankU'), (1.2, 1.2, 0), 'srank'),
    None: (bs.Lstr(resource='ultrakillMeterRankN'), (0.5, 0.5, 0.5), None),
}
RANK_ORDER = [None, 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS', 'U']
FRESHNESS_ORDER = [0.0, 0.5, 1.0, 1.5]

def clamp(num, min_val, max_val):
    return max(min(num, max_val), min_val)


class UltrakillMeter(bs.Actor):
    """
    A style-meter based on Ultrakill's.
    It handles ranking and a bar that depletes over time.
    WARNING: The bar depends on the width of the window.
    So make sure it isn't too wide or too skinny.
    As for recommendation, I just recommend
    you leave the scale as the default.
    The compact bool allows for a smaller version
    without style text.
    """

    freshness: float = 1.5
    """The amount of freshness we have.
    This is controlled in bascenev1._coopgame,
    based on a SpazBot's last hit (simply, if the hit is equal to the last hit and
    sub-hit type, decrease freshness and vice versa. This should ONLY control how
    slow we add to the score. If you want more points, use multiplier."""

    multiplier: int = 1
    """Multiplier that multiplies how many points we get.
    Unused for now."""

    def __init__(
        self,
        position: tuple[float, float] | None = None,
        scale: tuple[float, float] | None = None,
        compact: bool = False,
    ):
        super().__init__()

        # Layout constants differ between compact and full modes.
        if compact:
            _default_position = (430, -300)
            _default_scale = (450, 110)
            self._bar_y_frac = 0.1
            self._freshbar_y_frac = -0.1
            self._rank_y_frac = 0.2
            self._freshbar_h_factor = 10
        else:
            _default_position = (430, 0)
            _default_scale = (450, 500)
            self._bar_y_frac = 0.35
            self._freshbar_y_frac = -0.35
            self._rank_y_frac = 0.4
            self._freshbar_h_factor = 40

        self._compact = compact
        position = position if position is not None else _default_position
        scale = scale if scale is not None else _default_scale

        self.texts = []
        self.bar_timer: bs.Timer | None = None
        self._bar: bs.Node | None = None
        self._rank_text: bs.Node | None = None
        self._rank: str | None = None
        self.node = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('softRect'),
                'position': position,
                'scale': scale,
                'color': (0.1, 0.1, 0.1),
                'opacity': 0.7,
                'absolute_scale': True,
            },
            delegate=self,
        )
        self.freshness_num = 50
        self.freshness_index = len(FRESHNESS_ORDER)
        width = scale[0] - 25
        barscale = 0.8
        self._width = width * barscale
        self._height = 15 * barscale
        self._bar_width = 1 * barscale
        self._freshbar_dwidth = width / 1.3 * barscale
        self._freshbar_height = self._freshbar_h_factor * barscale
        self._freshbar_width = width / 2 * barscale
        self._bar_tex = self._backing_tex = bs.gettexture('bar')
        self.score: int = 0
        self._rank_index = 0  # corresponds to None
        self.text_spacing = 30
        self.rainbow_bar = False
        self.create_bar()
        self._apply_rank()

    def create_bar(self):
        op = 0.3
        op2 = 0.6
        self._backing = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'scale': (self._width, self._height),
                    'opacity': op,
                    'color': (0.1, 0.1, 0.1),
                    'texture': self._backing_tex,
                },
            )
        )
        self._bar = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'opacity': op,
                    'color': (0.8, 0.8, 0.8),
                    'texture': self._bar_tex,
                },
            )
        )
        if self.rainbow_bar:
            bs.animate_array(
                self._bar.node, 'color', 3,
                {
                    0.0: (1.0, 0.0, 0.0),
                    0.1: (1.0, 0.5, 0.0),
                    0.2: (1.0, 1.0, 0.0),
                    0.3: (0.0, 1.0, 0.0),
                    0.4: (0.0, 0.0, 1.0),
                    0.5: (1.0, 0.0, 0.0),
                },
                loop=True
            )

        self._bar_scale = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': self._bar_width,
                'input1': self._height,
            },
        )
        assert self._bar.node
        self._bar_scale.connectattr('output', self._bar.node, 'scale')
        self._bar_position = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': self.node.position[0],
                'input1': self.node.position[1] + self.node.scale[1] * self._bar_y_frac,
            },
        )
        self._bar_position.connectattr('output', self._bar.node, 'position')
        self._bar_position.connectattr('output', self._backing.node, 'position')

        self._freshbacking = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'scale': (self._freshbar_dwidth, self._freshbar_height),
                    'opacity': op,
                    'color': (0.1, 0.1, 0.1),
                    'texture': self._backing_tex,
                },
            )
        )
        self._freshbar = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'opacity': op2,
                    'color': (0.9, 0.0, 0.0),
                    'texture': self._bar_tex,
                },
            )
        )
        self._freshbar_pos = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': self.node.position[0],
                'input1': self.node.position[1] + self.node.scale[1] * self._freshbar_y_frac,
            },
        )
        self._freshbar_text = bs.newnode(
            'text',
            attrs={
                'text': '',
                'color': (1, 0.9, 0.9),
                'h_align': 'center',
                'v_align': 'center',
                'scale': 1.0,
            },
        )
        self._freshbar_scale = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': self._freshbar_width,
                'input1': self._freshbar_height,
            },
        )
        assert self._freshbar.node
        self._freshbar_scale.connectattr('output', self._freshbar.node, 'scale')
        self._freshbar_pos.connectattr('output', self._freshbar.node, 'position')
        self._freshbar_pos.connectattr('output', self._freshbar_text, 'position')
        self._freshbar_pos.connectattr('output', self._freshbacking.node, 'position')
        self.add_freshness(0)

    def add_bar_length(self, length: int | float):
        if self._bar is None:
            self.create_bar()
        if self._bar_scale is not None:
            self._bar_scale.input0 += length
            self._bar_width += length

    def set_bar_length(self, length: int | float):
        if self._bar is None:
            self.create_bar()
        if self._bar_scale is not None:
            self._bar_scale.input0 = length
            self._bar_width = length

    def set_fbar_length(self, length: int | float, text: str | bs.Lstr = ''):
        if self._freshbar is None:
            self.create_bar()
        if self._freshbar_scale is not None:
            self._freshbar_scale.input0 = length
            self._freshbar_width = length
            self._freshbar_text.text = text

    def style_text(
        self,
        styletext: bs.Lstr | str,
        points: int = 30,
        color: tuple[float, float, float] = (1, 1, 1),
    ):
        """Show a floating style label and add points.
        In compact mode only the score callback fires (no text node)
        """
        if self._compact:
            self.on_score_callback(points)
            return

        y = self.node.scale[1] * 0.28
        for text in self.texts:
            y -= self.text_spacing
        ourpos = self.node.position
        textnode = bs.newnode(
            'text',
            attrs={
                'text': styletext,
                'position': (ourpos[0] - 180, ourpos[1] + y),
                'color': color,
                'h_align': 'left',
                'v_align': 'center',
                'scale': 1.0,
                'maxwidth': self.node.scale[0] - 180,
            },
        )
        self.texts.append(textnode)
        self.on_score_callback(points)
        bs.timer(3.5, lambda: self.delete_text(textnode))

    def delete_text(self, textnode):
        if textnode in self.texts:
            textnode.delete()
            self.texts.remove(textnode)
        for textnode in self.texts:
            textnode.position = (textnode.position[0], textnode.position[1] + self.text_spacing)

    def on_score_callback(self, newscore):
        finalscore = newscore * self.freshness * self.multiplier
        self.score += finalscore
        if self.bar_timer is None:
            self.bar_timer = bs.Timer(0.1, self.bar_tick, repeat=True)
        self.add_bar_length(finalscore)

    def _apply_rank(self):
        rank = RANK_ORDER[self._rank_index]
        self._rank = rank
        rank_lstr, color, sound = SCORE_RANKS[rank]
        self.set_rank(rank_lstr, color, sound)

    def bar_tick(self):
        """Slowly reduce the bar length over time."""
        # Rank up
        if self._bar_width >= self._width and self._rank_index < len(RANK_ORDER) - 1:
            self._rank_index += 1
            self._apply_rank()
            self.set_bar_length(50)
            bs.getsound('smb1r_rankup').play()

        # Decrease bar length RAPIDLY if over the limit
        if self._bar_width >= self._width:
            self.add_bar_length(-10)

        # Rank down
        if self._bar_width <= 1 and self._rank_index > 0:
            self._rank_index -= 1
            self._apply_rank()
            self.set_bar_length(self._width - 20)
            bs.getsound('smb1r_rankdown').play()
        # reduce the bar length
        self.add_bar_length(-2)

    def add_freshness(self, amount: int):
        """Add **A BIT** of freshness.
        Use this instead of setting the value."""
        self.freshness_num += amount
        if self.freshness > 50 and self.freshness_index < len(FRESHNESS_ORDER) - 1:
            self.freshness_num = 1
            self.freshness_index += 1
            self.freshness = FRESHNESS_ORDER[self.freshness_index]
        if self.freshness_num < 0 and self.freshness_index > 0:
            self.freshness_num = 50
            self.freshness_index -= 1
            self.freshness = FRESHNESS_ORDER[self.freshness_index]
        self.freshness_num = clamp(self.freshness_num, 0, 50)
        subs = [('${COUNT}', str(self.freshness))]
        freshness_dict = {
            1.5: 'ultrakillMeterFresh',
            1.0: 'ultrakillMeterUsed',
            0.5: 'ultrakillMeterStale',
            0.0: 'ultrakillMeterDull',
        }
        for threshold in freshness_dict:
            if self.freshness >= threshold:
                sub = bs.Lstr(
                    r=freshness_dict[threshold],
                    s=subs
                )
                break
        val = self.freshness_num
        mini = 0
        maxi = 50
        norm = (val - mini) / (maxi - mini)
        norm = clamp(norm, 0, 1)
        self.set_fbar_length(self._freshbar_dwidth * norm, sub)

    def set_rank(
        self,
        rank: str | bs.Lstr | None = None,
        color: tuple[float, float, float] = (1, 1, 1),
        sound: str | None = None,
    ):
        big = 1.7
        normal = 1.3
        animdict = {
            0: normal,
            0.05: big,
            0.1: big,
            0.5: normal,
        }
        if not self._rank_text:
            sc = self.node.scale
            ps = self.node.position
            self._rank_text = bs.newnode(
                'text',
                attrs={
                    'text': rank,
                    'position': (ps[0], ps[1] + sc[1] * self._rank_y_frac),
                    'color': color,
                    'h_align': 'center',
                    'v_align': 'center',
                    'scale': normal,
                    'maxwidth': 200,
                },
            )
            bs.animate(
                self._rank_text,
                'scale',
                animdict
            )
        else:
            self._rank_text.text = rank
            self._rank_text.color = color
            # Scale up our text briefly to show that
            # we've ranked up.
            bs.animate(
                self._rank_text,
                'scale',
                animdict
            )
        if sound:
            bs.getsound(sound).play()