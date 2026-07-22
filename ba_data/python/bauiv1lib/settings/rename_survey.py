"""Window for re-naming the characters after the intro."""
from __future__ import annotations

from typing import TYPE_CHECKING, Sequence, override, cast
import logging

import bauiv1 as bui
import bascenev1 as bs
import babase as ba

SURVEY_STEPS = [
    dict(
        texture="earthbound/spazbound",
        cfg="squda_ch1name",
    ),
    dict(
        texture="earthbound/krisbound",
        cfg="squda_ch2name",
    ),
    dict(
        texture="earthbound/snakebound",
        cfg="squda_ch3name",
    ),
    dict(
        texture="earthbound/noobbound",
        cfg="squda_ch4name",
    ),
]

class NameSurveyAllWindow(bui.MainWindow):
    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        self._r = 'renameWindow'
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 500
        screensize = bui.get_virtual_screen_size()
        safesize = bui.get_virtual_safe_area_size()
        smallscale = min(2.0, 1.5 * screensize[0] / safesize[0])
        scale = smallscale if uiscale is bui.UIScale.SMALL else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
        target_height = min(height - 70, screensize[1] / scale)
        self._yoffs = 0.5 * height + 0.5 * target_height + 30.0
        self._width = width
        self._height = height
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                scale=scale,
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
            refresh_on_screen_size_changes=True,
        )
        self.title = bui.textwidget(
            parent=self._root_widget,
            position=(15, self._yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        self._inputs: list[tuple[str, bui.Widget]] = []
        offset = 140
        start_y = self._height - offset
        spacing = 75
        x_center = self._width * 0.55
        self.should_continue = False

        for i, step in enumerate(SURVEY_STEPS):
            y = start_y - i * spacing

            # Image
            bui.imagewidget(
                parent=self._root_widget,
                position=(x_center - 300, y),
                size=(60, 60),
                texture=bui.gettexture(step["texture"]),
            )

            # Input field
            txt = bui.textwidget(
                parent=self._root_widget,
                position=(x_center - 200, y + 5),
                size=(400, 40),
                editable=True,
                autoselect=(i == 0),
                text=bui.app.config.get(step["cfg"], ""),
            )
            bui.textwidget(edit=txt, on_return_press_call=lambda: self._on_ok())

            self._inputs.append((step["cfg"], txt))

        # Save button
        y -= spacing
        position = (
            (self._width * 0.5 - 90, y)
        )
        self._save_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=position,
            size=(180, 60),
            label="Save",
            on_activate_call=self._on_save,
        )
        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(40, self._height - 60),
                size=(80, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

    def _on_save(self):
        if not self.main_window_has_control():
            return
            
        if not self.should_continue:
            glyph = ba.charstr(ba.SpecialChar.OUYA_BUTTON_Y)
            bui.screenmessage(f"WARNING: This will cost {glyph}800 to change.\nPress again to continue.", color=(1, 0.5, 0))
            bui.getsound('emerald_reject').play()
            self.should_continue = True
            return
            
        samenamenum = 0  
        for key, widget in self._inputs:
            val = cast(str, bui.textwidget(query=widget)).strip()

            if val == "":
                bui.screenmessage("All names must be filled.", color=(1, 0, 0))
                bui.getsound('error').play()
                return
            if val == bui.app.config.get(key):
                samenamenum += 1
                
            if samenamenum >= len(self._inputs):
                bui.screenmessage("Names are the exact same.", color=(1, 0, 0))
                bui.getsound('error').play()
                return

            bui.app.config[key] = val
            
        self.should_continue = False
        bui.app.config.apply_and_commit()
        bui.getsound('cashRegister').play()
        bui.screenmessage('Changes applied.', color=(0, 1, 0))
        amount = 800
        bui.app.config['squda_spaztix'] = ba.app.config.get('squda_spaztix', 0) - amount

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )