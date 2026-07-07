"""ui for turning on and off powerups"""

from __future__ import annotations

from typing import override

import bascenev1 as bs
import bauiv1 as bui
import fromgoverhaul.mell_resources as mell


class PowerupSetupWindow(bui.MainWindow):
    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        bui.set_analytics_screen('Powerup Setup')

        self._r = 'powerupsWindow'
        uiscale = bui.app.ui_v1.uiscale

        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 700

        screensize = bui.get_virtual_screen_size()
        safesize = bui.get_virtual_safe_area_size()

        smallscale = min(2.0, 1.5 * screensize[0] / safesize[0])

        scale = (
            smallscale
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
        )

        target_height = min(height - 70, screensize[1] / scale)
        target_width = min(width - 80, screensize[0] / scale)

        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        self._scroll_width = target_width - 30
        self._scroll_height = target_height - 140
        self._sub_width = min(700, self._scroll_width * 0.95)

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget,
                on_cancel_call=self.main_window_back,
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(50, yoffs - 50.0),
                size=(70, 70),
                scale=0.8,
                text_scale=1.2,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )

            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (55 if uiscale is bui.UIScale.SMALL else 35)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,
        )

        self._powerups = dict(bs._powerup.get_powerup_dist2())

        cfg = bui.app.config
        custom = cfg.get('squda_powerup_dist', {})

        for ptype in self._powerups:
            if ptype in custom:
                self._powerups[ptype] = custom[ptype]

        self._checkboxes: dict[str, bui.Widget] = {}

        self._all_enabled = all(
            thisvalue == True
            for thisvalue in cfg.get('squda_powerup_dist').values()
        )

        button_y = yoffs - 120

        self._toggle_all_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.5 - 120, button_y),
            size=(240, 55),
            autoselect=True,
            label=self._get_toggle_all_label(),
            on_activate_call=self._toggle_all_powerups,
        )

        scroll_bottom = button_y - self._scroll_height - 15

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(self._scroll_width, self._scroll_height),
            position=(
                width * 0.5 - self._scroll_width * 0.5,
                scroll_bottom,
            ),
            simple_culling_v=20.0,
            highlight=False,
            center_small_content_horizontally=True,
            selection_loops_to_parent=True,
            border_opacity=0.4,
        )

        bui.widget(
            edit=self._scrollwidget,
            right_widget=self._scrollwidget,
        )

        row_height = 70
        self._sub_height = max(
            100,
            len(self._powerups) * row_height + 30
        )

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            selection_loops_to_parent=True,
        )

        start_y = self._sub_height - 70

        for i, (ptype, weight) in enumerate(self._powerups.items()):
            y = start_y - i * row_height
            x = 130

            cfg = bui.app.config.get('squda_powerup_dist', {})
            enabled = cfg.get(ptype, False)

            tex = mell.get_texture_for_powerup(ptype, ui=True)

            bui.imagewidget(
                parent=self._subcontainer,
                position=(x + 50, y - 10),
                size=(55, 55),
                color=(1.5, 1.5, 1.5),
                texture=tex,
            )

            self._checkboxes[ptype] = bui.checkboxwidget(
                parent=self._subcontainer,
                position=(x + 120, y),
                size=(400, 40),
                maxwidth=450,
                autoselect=False,
                textcolor=(1.0, 1.0, 1.0),
                text=bui.Lstr(resource=f'{self._r}.{ptype}'),
                value=enabled,
                on_value_change_call=bui.Call(
                    self._toggle_powerup,
                    ptype,
                ),
            )

    def _get_toggle_all_label(self) -> str:
        return (
            bui.Lstr(r=f'{self._r}.disableAllText')
            if self._all_enabled
            else bui.Lstr(r=f'{self._r}.enableAllText')
        )

    def _toggle_all_powerups(self) -> None:
        new_value = not self._all_enabled

        cfg = bui.app.config
        custom = cfg.get('squda_powerup_dist', {})

        for ptype, checkbox in self._checkboxes.items():
            custom[ptype] = True if new_value else False

            bui.checkboxwidget(
                edit=checkbox,
                value=new_value,
            )

        cfg['squda_powerup_dist'] = custom
        cfg.apply_and_commit()

        self._all_enabled = new_value

        bui.buttonwidget(
            edit=self._toggle_all_button,
            label=self._get_toggle_all_label(),
        )

        bui.getsound(
            'shieldUp' if new_value else 'shieldDown'
        ).play()

    def _toggle_powerup(self, ptype: str, value: bool):
        cfg = bui.app.config

        custom = cfg.get('squda_powerup_dist', {})

        custom[ptype] = True if value else False

        cfg['squda_powerup_dist'] = custom
        cfg.apply_and_commit()

        self._all_enabled = all(
            thisvalue == True
            for thisvalue in cfg.get('squda_powerup_dist').values()
        )

        bui.buttonwidget(
            edit=self._toggle_all_button,
            label=self._get_toggle_all_label(),
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        cls = type(self)

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
            )
        )