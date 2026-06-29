"""UI class for selecting specific textures."""
from __future__ import annotations

from typing import TYPE_CHECKING, cast, override, Any
from bauiv1lib.popup import PopupWindow
import bauiv1 as bui


class TexturePicker(PopupWindow):
    """Popup UI to select a texture."""

    def __init__(
        self,
        parent: bui.Widget,
        position: tuple[float, float],
        *,
        textures: list[str],
        delegate: Any = None,
        scale: float | None = None,
        offset: tuple[float, float] = (0.0, 0.0),
        tag: Any = '',
    ):
        assert bui.app.classic is not None

        self._textures = sorted(textures)
        self._filtered_textures = list(self._textures)

        self._delegate = delegate
        self._parent = parent
        self._position = position
        self._offset = offset
        self._tag = tag
        self._transitioning_out = False

        uiscale = bui.app.ui_v1.uiscale
        if scale is None:
            scale = (
                2.3
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            )
        self._scale = scale

        self._cols = 4
        self._button_size = 40
        self._spacing = 45

        # Window sizing.
        width = 30 + self._cols * self._spacing
        visible_rows = 5
        height = 30 + visible_rows * self._spacing

        super().__init__(
            position=position,
            size=(width, height),
            scale=scale,
            bg_color=(0.5, 0.5, 0.5),
            offset=offset,
        )

        # Scroll area.
        self._scrollwidget = bui.scrollwidget(
            parent=self.root_widget,
            position=(15, 15),
            size=(width - 25, height - 70),
            simple_culling_v=20.0,
        )
        
        # Search bar.
        self._search_bar = bui.textwidget(
            parent=self.root_widget,
            position=(width * 0.18, height - 45),
            size=(width, 30),
            text='',
            editable=True,
            maxwidth=width - 30,
            description='Search Textures',
            v_align='center',
            corner_scale=0.7,
            autoselect=False,
            selectable=False,
            on_return_press_call=bui.Call(self._update_filter),
        )

        self._buttons: list[bui.Widget] = []

        # Initial populate.
        self._rebuild_grid()

        # Continuously check for text changes.
        self._last_query = ''
        self._update_timer = bui.AppTimer(
            0.15,
            bui.WeakCall(self._check_search),
            repeat=True,
        )

    def _check_search(self) -> None:
        query = cast(str, bui.textwidget(query=self._search_bar))

        if query != self._last_query:
            self._last_query = query
            self._update_filter()

    def _update_filter(self) -> None:
        query = cast(str, bui.textwidget(query=self._search_bar)).lower()

        if not query:
            self._filtered_textures = list(self._textures)
        else:
            self._filtered_textures = [
                tex for tex in self._textures
                if query in tex.lower()
            ]

        self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        rows = max(
            1,
            (len(self._filtered_textures) + self._cols - 1)
            // self._cols,
        )

        sub_height = max(265, 40 + rows * self._spacing)

        # Delete old subcontainer.
        try:
            self._subcontainer.delete()
        except Exception:
            pass

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(170, sub_height),
            background=False,
        )

        self._buttons.clear()

        for i, tex_name in enumerate(self._filtered_textures):
            x = i % self._cols
            y = i // self._cols

            tex = bui.gettexture(tex_name)

            btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=(
                    self._spacing * x,
                    sub_height - 50 - self._spacing * y,
                ),
                size=(self._button_size, self._button_size),
                label='',
                button_type='square',
                texture=tex,
                on_activate_call=bui.WeakCall(
                    self._select,
                    tex_name,
                ),
                autoselect=True,
                color=(1, 1, 1),
            )

            self._buttons.append(btn)

    def _select(self, texture: str) -> None:
        if self._delegate:
            self._delegate.texture_picker_selected(self, texture)

        bui.apptimer(0.05, self._transition_out)

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True

            if self._delegate:
                self._delegate.texture_picker_closing(self)

            bui.containerwidget(
                edit=self.root_widget,
                transition='out_scale',
            )

    def get_tag(self) -> Any:
        """Return this popup's tag value."""
        return self._tag

    @override
    def on_popup_cancel(self) -> None:
        if not self._transitioning_out:
            bui.getsound('swish').play()
        self._transition_out()