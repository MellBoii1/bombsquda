"""ONLINE SETTINGS"""
from typing import override

import bauiv1 as bui
from babase._logging import squdalog

class OnlineSettings(bui.Window):
    """ONLINE SETTINGS STUFF YEAH"""
    def __init__(
        self,
        first_time: bool = False,
    ):
        # pylint: disable=too-many-locals
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 450
        height = 290
        self._r = 'onlineWindow'

        uiscale = bui.app.ui_v1.uiscale
        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        safesize = bui.get_virtual_safe_area_size()

        # We're a generally widescreen shaped window, so bump our
        # overall scale up a bit when screen width is wider than safe
        # bounds to take advantage of the extra space.
        smallscale = min(2.0, 1.5 * screensize[0] / safesize[0])
        yoffs = height - 20
        scale = (
            smallscale
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        settings = self.get_settings()
        start_y = height - 140
        spacing = 2
        self._col_x = width * 0.2
        if uiscale is bui.UIScale.SMALL:
            self._col_x -= 40
        self.reset_clicks = 0
        self._first_time = first_time
        # look i cant be bothered to replace every 
        # mention of subcontainer
        self._subcontainer = root = bui.containerwidget(
            size=(width, height),
            toolbar_visibility='menu_minimal',
            scale=scale,
            transition='in_right',
        )
        super().__init__(
            root_widget=root,
        )
        self._back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(50, yoffs - 50.0),
            size=(70, 70),
            scale=0.8,
            text_scale=1.2,
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.close,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - 35),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,
        )
        row_height = 50
        # dicts containing options
        self._buttons = {}
        self._popup_labels = {}
        self._popup_menus = {}
        self._checkboxes = {}

        for row, setting in enumerate(settings):
            y = start_y - row * row_height
            if setting["type"] == "checkbox":
                self._build_checkbox(setting, y)
            elif setting["type"] == "popup":
                self._build_popup(setting, y)
            elif setting["type"] == "button":
                self._build_button(setting, y)
            else:
                squdalog.error(f"UNKNOWN SETTINGS SETTING TYPE: {setting['type']}")

    def _build_checkbox(self, setting: dict, y: float):
        key = setting.get('key')
        lkey = setting.get('label')
        sound = setting.get('sound')
        info = setting.get('info')
        x = self._col_x
        self._checkboxes[lkey] = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(x, y),
            size=(220, 40),
            autoselect=False,
            maxwidth=230,
            textcolor=(1.0, 1.0, 1.0),
            value=bui.app.config.get(key, False),
            text=bui.Lstr(resource=f"{self._r}.{lkey}"),
            on_value_change_call=bui.Call(
                self._set_config, key, 
                sound=sound
            ),
        )
        if info:
            bui.buttonwidget(
                parent=self._subcontainer,
                position=(x + 230, y + 5),
                size=(60, 45),
                scale=0.75,
                label='?',
                text_scale=1.5,
                on_activate_call=bui.Call(
                    bui.screenmessage,
                    bui.Lstr(r=f'{self._r}.{info}')
                ),
            )
    
    def _build_button(self, setting: dict, y: float):
        label = setting.get('label')
        callback = setting.get('callback')
        size = (350, 50)
        self._buttons[label] = bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._col_x, y),
            size=size,
            text_scale=1.0,
            label=bui.Lstr(resource=f'{self._r}.{label}'),
            on_activate_call=callback,
        )
    
    def _build_popup(self, setting: dict, y: float):
        xoffset = 70
        callback = setting.get('callback')
        cdisp = setting.get('display')
        c = setting.get('choices')
        cur = setting.get('current')
        label = setting.get('label')
        self._popup_labels[label] = bui.textwidget(
            parent=self._subcontainer,
            position=(self._col_x - xoffset, y + 25),
            text=bui.Lstr(resource=f"{self._r}.{label}"),
            size=(0, 0),
            scale=0.8,
            h_align='left',
            v_align='center',
        )
        self._popup_menus[label] = PopupMenu(
            parent=self._subcontainer,
            position=(self._col_x + 280 - xoffset, y),
            width=250,
            autoselect=False,
            on_value_change_call=bui.WeakCall(callback),
            choices=c,
            choices_display=cdisp,
            button_size=(200, 50),
            current_choice=cur,
        )
    
    def _set_config(self, 
        key: str, 
        val: bool, 
        sound: list | None = None
    ) -> None:
        cfg = bui.app.config
        cfg[key] = val
        cfg.apply_and_commit()
        squdalog.debug(f'{key} changed into {val}')
        if sound:
            if val:
                bui.getsound(sound[0]).play()
            else:
                bui.getsound(sound[1]).play()
        
    def get_settings(self):
        settings = [
            {
                'type': 'checkbox',
                'key': 'squda_disableping',
                'label': 'disablePinging',
                'info': 'pingingInfo',
            },
            {
                'type': 'checkbox',
                'key': "squda_disable_online_music", 
                'label': "disableOnlineMusic",
            },
            {
                'type': 'checkbox',
                'key': "squda_noonline",
                'label': "disableOnlineFeatures",
            },
        ]
        return settings
    
    def close(self):
        bui.containerwidget(
            edit=self._subcontainer, 
            transition='out_left'
        )