"""Health bar."""
from typing import override, Any
import bascenev1 as bs

class HealthBar(bs.Actor):
    """An animated HP bar with name, icon, and percentage/HP text.
    Call :meth:`update_hitpoints` whenever
    its hp value changes; the bar will 
    animate to the new length and
    update its text automatically.
    """

    def __init__(
        self,
        hitpoints: int,
        max_hitpoints: int,
        name: str = '',
        icon_texture: str = 'weegee_icon1',
        position: tuple[float, float] = (0, -290),
        width: float = 500,
        height: float = 45,
    ):
        super().__init__()

        self._width = width
        self._height = height
        self._pos = position
        self._hitpoints = hitpoints
        self._max_hitpoints = max_hitpoints

        self._backing_tex = bs.gettexture('bar')
        self._bar_tex = bs.gettexture('bar')

        self._backing: bs.NodeActor | None = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'scale': (self._width, self._height),
                    'color': (0.1, 0.1, 0.1),
                    'texture': self._backing_tex,
                    'position': position,
                },
            )
        )
        self._bar: bs.NodeActor | None = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'color': (0.1, 0.9, 0.25),
                    'texture': self._bar_tex,
                    'position': position,
                },
            )
        )

        hp_percent = (hitpoints / max_hitpoints) * 100

        self._bar_hp_text = bs.newnode(
            'text',
            owner=self._bar.node,
            attrs={
                'scale': 1.4,
                'color': (0.65, 1, 0.7),
                'opacity': 0.8,
                'text': f'{hp_percent:.0f}%',
                'h_align': 'center',
                'v_align': 'center',
                'position': position,
            },
        )
        self._bar_accurate_hp_text = bs.newnode(
            'text',
            owner=self._bar.node,
            attrs={
                'scale': 0.9,
                'color': (0.4, 0.9, 0.5),
                'opacity': 0.5,
                'text': f'{hitpoints}/{max_hitpoints}',
                'h_align': 'center',
                'v_align': 'center',
                'position': (
                    position[0],
                    position[1] - self._height + 5,
                ),
            },
        )
        self._bar_name_text = bs.newnode(
            'text',
            owner=self._bar.node,
            attrs={
                'scale': 1.1,
                'color': (0.4, 1.1, 0.65),
                'opacity': 1.0,
                'text': name,
                'h_align': 'center',
                'v_align': 'center',
                'position': (
                    position[0] - (self._width * 0.5) + 90,
                    position[1] + self._height - 3,
                ),
            },
        )
        self._bar_icon = bs.newnode(
            'image',
            owner=self._bar.node,
            attrs={
                'texture': bs.gettexture(icon_texture),
                'scale': (80, 80),
                'position': (
                    position[0] - (self._width * 0.5) + 10,
                    position[1],
                ),
            },
        )
        self._bar_scale = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': 0,
                'input1': self._height,
            },
        )
        self._bar_scale.connectattr('output', self._bar.node, 'scale')

        self._bar_position = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': -self._width / 2,
                'input1': position[1],
            },
        )
        self._bar_position.connectattr('output', self._bar.node, 'position')

        self._bar_width = self._width * (hitpoints / max_hitpoints)

        self._animate_in()
        self.set_length(self._bar_width, time=1)

    def _animate_in(self) -> None:
        assert self._backing is not None and self._bar is not None
        bs.animate(self._backing.node, 'opacity', {0: 0, 0.5: 1})
        bs.animate(self._bar_hp_text, 'opacity', {0: 0, 1: 1})
        bs.animate_array(
            self._bar_name_text,
            'position',
            2,
            {
                0: (-1200, self._bar_name_text.position[1]),
                0.8: self._bar_name_text.position,
            },
        )
        bs.animate_array(
            self._bar_icon,
            'position',
            2,
            {
                0: (-1200, self._bar_icon.position[1]),
                1: self._bar_icon.position,
            },
        )
        bs.animate(
            self._bar_accurate_hp_text,
            'opacity',
            {0: 0, 0.8: 0, 1.7: 1},
        )
        bs.animate(self._bar.node, 'opacity', {0: 0, 0.7: 1})

    def set_length(self, length: float, time: float = 0.2) -> None:
        """Animate the bar's fill."""
        if self._bar is None or self._bar_scale is None:
            return
        self._bar_width = length
        cur_x = self._bar_position.input0
        bs.animate(
            self._bar_position,
            'input0',
            {0: cur_x, time: -self._width / 2 + self._bar_width / 2},
        )
        bs.animate(
            self._bar_scale,
            'input0',
            {0: self._bar_scale.input0, time: length},
        )

    def update_hitpoints(self, hitpoints: int, max_hitpoints: int) -> None:
        """Update the displayed HP values."""
        self._hitpoints = hitpoints
        self._max_hitpoints = max_hitpoints
        self.set_length(self._width * (hitpoints / max_hitpoints))
        if self._bar_accurate_hp_text:
            self._bar_accurate_hp_text.text = (
                f'{hitpoints}/{max_hitpoints}'
            )
        if self._bar_hp_text:
            self._bar_hp_text.text = (
                f'{int((hitpoints / max_hitpoints) * 100)}%'
            )

    @override
    def exists(self) -> bool:
        return self._bar is not None

    @override
    def handlemessage(self, msg) -> None:
        if isinstance(msg, bs.DieMessage):
            self._backing = None
            self._bar = None
        else:
            super().handlemessage(msg)
