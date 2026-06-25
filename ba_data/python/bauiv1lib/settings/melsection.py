# Released under the MIT License. See LICENSE for details.
#
"""UI for setting... settings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence, override
import logging

import bauiv1 as bui
import bascenev1 as bs
import os
import babase
import random
from bauiv1lib.popup import PopupMenu
from bauiv1lib.characterpicker import CharacterPickerDelegate, CharacterPicker
from bauiv1lib.settings.online import OnlineSettings
from bascenev1lib.mainmenu import MENU_MUSIC_AMOUNT
from babase._logging import squdalog

if TYPE_CHECKING:
    from typing import Callable

def _format_chance(c: float) -> str:
    text = f"{c:.1f}".rstrip('0').rstrip('.')
    newtext = text.replace('.', '')
    return newtext
        

class MelWindow(bui.MainWindow, CharacterPickerDelegate):
    """Window for selecting BombSquda settings."""
    
    @staticmethod
    def _create(t, o, ft):
        return MelWindow(
            transition=t,
            origin_widget=o,
            first_time=ft,
        )
    
    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        first_time: bool = False,
    ):
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('BombSquda Settings')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 750
        self._r = 'melWindow'

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
        scale = (
            smallscale
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        target_height = min(height - 70, screensize[1] / scale)
        target_width = min(width - 80, screensize[0] / scale)
        yoffs = 0.5 * height + 0.5 * target_height + 30.0
        self._scroll_width = target_width - 30
        self._scroll_height = target_height - 45
        self._sub_width = min(500, self._scroll_width * 0.95)
        self._sub_height = 50
        settings = self.get_settings(first_time=first_time)
        # for every setting here, we add 50 to the
        # height of the sub widget
        for setting in settings:
            self._sub_height += 50
        start_y = self._sub_height - 60
        spacing = 2
        scroll_bottom = yoffs - 56 - self._scroll_height
        self._col_x = width * 0.12
        if uiscale is bui.UIScale.SMALL:
            self._col_x -= 40
        self.is_small = bui.app.ui_v1.uiscale is bui.UIScale.SMALL
        self.reset_clicks = 0
        self._first_time = first_time
        
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL or first_time
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )
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
        bui.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            selection_loops_to_parent=True,
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
                position=(50, yoffs - 50.0),
                size=(70, 70),
                scale=0.8,
                text_scale=1.2,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        if first_time:
            position = (width - 30, yoffs - 80.0)
            scale = 0.8
            if uiscale is bui.UIScale.SMALL:
                position = (width - 140, yoffs - 130.0)
                scale = 1.0
            contbtn = bui.buttonwidget(
                parent=self._root_widget,
                position=position,
                size=(70, 70),
                label='->',
                scale=scale,
                autoselect=True,
                on_activate_call=self._continue,
            )

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
        row_height = 50
        # dicts containing options
        self._buttons = {}
        self._multi_buttons_label = {}
        self._multi_buttons_buttons = {}
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

            elif setting["type"] == "multi_button":
                self._build_multi_button(setting, y)
            
            else:
                squdalog.error(f"UNKNOWN SETTINGS SETTING TYPE: {setting['type']}")

    def _build_checkbox(self, setting: dict, y: float):
        key = setting.get('key')
        lkey = setting.get('label')
        sound = setting.get('sound')
        info = setting.get('info')
        sub_option = setting.get('sub_option')
        x = self._col_x
        if sub_option:
            bui.imagewidget(
                parent=self._subcontainer,
                position=(x - 5, y - 3),
                size=(40, 45),
                texture=bui.gettexture('subOption'),
                color=(0.49, 0.45, 0.61),
            )
            x += 50
        self._checkboxes[lkey] = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(x, y),
            size=(220, 40),
            autoselect=False,
            maxwidth=300,
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
                position=(x + 360, y + 5),
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
    
    def _build_multi_button(self, setting: dict, y: float):
        xoffset = 70
        label = setting.get('label')

        self._multi_buttons_label[label] = bui.textwidget(
            parent=self._subcontainer,
            position=(self._col_x - xoffset, y + 25),
            text=bui.Lstr(resource=f"{self._r}.{label}"),
            size=(0, 0),
            scale=0.8,
            h_align='left',
            v_align='center',
        )

        buttons = setting["buttons"]

        for i, btn in enumerate(buttons):
            label = btn["label"]
            key = btn["key"]

            self._multi_buttons_buttons[key] = bui.buttonwidget(
                parent=self._subcontainer,
                position=(self._col_x + 160 + (i * 160), y),
                size=(150, 50),
                label=label,
                on_activate_call=btn.get("callback"),
            )
    
    def _build_popup(self, setting: dict, y: float):
        xoffset = 70
        x = self._col_x
        callback = setting.get('callback')
        cdisp = setting.get('display')
        c = setting.get('choices')
        cur = setting.get('current')
        label = setting.get('label')
        sub_option = setting.get('sub_option')
        x_extra = 280
        if sub_option:
            bui.imagewidget(
                parent=self._subcontainer,
                position=(x - 5, y - 3),
                size=(40, 45),
                texture=bui.gettexture('subOption'),
                color=(0.49, 0.45, 0.61),
            )
            x += 120
            x_extra = 140
            y -= 5
        self._popup_labels[label] = bui.textwidget(
            parent=self._subcontainer,
            position=(x - xoffset, y + 25),
            text=bui.Lstr(resource=f"{self._r}.{label}"),
            size=(0, 0),
            scale=0.9,
            h_align='left',
            v_align='center',
            maxwidth=x_extra - 30,
        )
        self._popup_menus[label] = PopupMenu(
            parent=self._subcontainer,
            position=(x + x_extra - xoffset, y),
            width=250,
            autoselect=False,
            on_value_change_call=bui.WeakCall(callback),
            choices=c,
            choices_display=cdisp,
            button_size=(200, 50),
            current_choice=cur,
        )
    
    def _changefont(self) -> None:
        # THE FOLLOWING CODE BELOW
        # SHOULD **NEVER** BE REPLICATED IN
        # AN ACTUAL WELL DEVELOPED MODPACK!!
        # NOT ONLY ARE THEY ARBITRARY AND RENAME
        # FILES (WHICH ALSO MEANS THEY REVERT
        # EVERY UPDATE), BUT THEY COULD JUST SCREW UP
        # SOMETHING AND I DON'T EVEN KNOW THAT!!
        def rename(name: str, output: str):
            platform = app.classic.platform
            app = babase.app
            suffix = '.dds' if platform not in ['android'] else '.ktx'
            path = os.path.join(
                app.env.data_directory,
                'ba_data',
                'textures',
                name + suffix,
            )
            out = os.path.join(
                app.env.data_directory,
                'ba_data',
                'textures',
                output + suffix,
            )
            os.rename(path, out)
        rename('fontSmall0', 'oldefont')
        rename('fontBig', 'oldefont2')
        rename('fontALT0', 'fontSmall0')
        rename('fontBigALT', 'fontBig')
        rename('oldefont', 'fontALT0')
        rename('oldefont2', 'fontBigALT')
        bs.screenmessage('doing media reload to apply change...')
        bui.app.classic.run_media_reload_benchmark()
    
    def open_characters(self):
        btn = self._multi_buttons_buttons['favChar']
        CharacterPicker(
            parent=self._root_widget,
            position=btn.get_screen_space_center(),
            delegate=self,
        )
    
    @override
    def on_character_picker_pick(self, character: str) -> None:
        """A character has been selected by the picker."""
        if not self._root_widget:
            return
        bui.getsound(
            random.choice(
                bui.app.classic.spaz_appearances[character].victory_sounds
            )
        ).play()
        bui.app.config['squda_favchar'] = character
        bui.app.config.commit()
        btn = self._multi_buttons_buttons['favChar']
        bui.buttonwidget(
            edit=btn, 
            label=character
        )
    
    def reset_character(self):
        character = bui.app.config.get('squda_favchar', None)
        btn = self._multi_buttons_buttons['favChar']
        if character:
            bui.getsound(
                random.choice(
                    bui.app.classic.spaz_appearances[character].death_sounds
                )
            ).play()
        bui.app.config['squda_favchar'] = None
        bui.app.config.commit()
        bui.buttonwidget(
            edit=btn, 
            label=bui.Lstr(resource=f"{self._r}.pickChar")
        )
        
    def _meter_choice(self, choice):
        key = "squda_ultrameter"
        cfg = bui.app.config
        cfg[key] = choice
        cfg.apply_and_commit()
        squdalog.debug(f'{key} changed into {choice}')
        
    def _chance_choice(self, choice):
        key = "squda_entitychance"
        cfg = bui.app.config
        cfg[key] = choice
        cfg.apply_and_commit()
        squdalog.debug(f'{key} changed into {choice}')
    
    def _music_choice(self, choice):
        from bascenev1lib.mainmenu import MainMenuActivity
        key = "squda_menumusic"
        cfg = bui.app.config
        cfg[key] = choice
        cfg.apply_and_commit()
        squdalog.debug(f'{key} changed into {choice}')
        activity = bs.get_foreground_host_activity()
        if isinstance(activity, MainMenuActivity):
            activity.menu_music()

    def _set_config(self, 
        key: str, 
        val: bool, 
        sound: list | None = None
    ) -> None:
        cfg = bui.app.config
        cfg[key] = val
        cfg.apply_and_commit()
        squdalog.debug(f'{key} changed into {val}')
        if key == 'squda_customfont':
            self._changefont()
        if sound:
            if val:
                bui.getsound(sound[0]).play()
            else:
                bui.getsound(sound[1]).play()

    def _continue(self) -> None:
        from bascenev1lib.game.surveyprogram import SurveyIntroWindow
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
            
        self.main_window_replace(
            SurveyIntroWindow(
                transition='in_right',
                origin_widget=self._root_widget,
                step=1,
            )
        )
        
    def _open_name_setup(self):
        from bauiv1lib.settings.rename_survey import NameSurveyAllWindow
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
            
        self.main_window_replace(
            NameSurveyAllWindow(
                origin_widget=self._root_widget
            )
        )
    
    def _open_powerup_setup(self):
        from bauiv1lib.settings.powerups import PowerupSetupWindow
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
            
        self.main_window_replace(
            PowerupSetupWindow(
                origin_widget=self._root_widget
            )
        )
    
    def _reset_achievements(self):
        if self.reset_clicks < 2:
            bui.getsound('error').play()
            bui.screenmessage(
                bs.Lstr(resource=f'{self._r}.confirmReset'),
                color=(1, 0.5, 0)
            )
            self.reset_clicks += 1
        else:
            bui.getsound('baditem').play()
            bui.app.config['squda_achievements'] = {}
            bui.screenmessage(
                bs.Lstr(resource=f'{self._r}.achResetDone'),
                color=(1, 0.1, 0.1)
            )
            self.reset_clicks = 0
            
    @override
    def get_main_window_state(self):
        return bui.BasicMainWindowState(
            create_call=lambda t, o, ft=self._first_time:
                MelWindow._create(t, o, ft)
        )
    
    def get_settings(self, first_time: bool = False):
        meter_choices = [
            'disabled',
            'basic',
            'normal',
        ]
        def ls(text: str): return bui.Lstr(r=f'{self._r}.{text}')
        meter_cdisp = [
            ls(f'meter{text}Text')
            for text in meter_choices
        ]
        music_choices = [str(None)]
        music_choices.extend('MENU' + str(i + 1) for i in range(MENU_MUSIC_AMOUNT))
        music_cdisp = [bs.Lstr(v=str(None))]
        def format_music_val(music_val: str | dict):
            if isinstance(music_val, dict):
                return f'{music_val.get('title')} - {music_val.get('artist')}'
            else:
                return music_val
        music_cdisp.extend(
            bs.Lstr(
                value=format_music_val(
                    bs._music.get_music_value(music)
                )
            )
            for music in music_choices if music != 'None'
        )
        settings = [
            {
                'type': 'checkbox',
                'key': "Disable Camera Shake", 
                'label': "camShakeText", 
            },
            {
                'type': 'checkbox',
                'key': "squda_disablewindowshake", 
                'label': "windowShakeText", 
                'sub_option': True,
            },
            {
                'type': 'checkbox',
                'key': "squda_noisepolution", 
                'label': "noisePollutionText", 
            },
            {
                'type': 'checkbox',
                'key': "squda_skipintro", 
                'label': "skipIntroText"
            },
            {
                'type': 'checkbox',
                'key': "squda_foxyjumpscare", 
                'label': "foxyJumpscareText",
            },
            {
                'type': 'checkbox',
                'key': "squda_spazhardmode", 
                'label': "spazHardModeText", 
                'sound': ['hardmode', 'okitem'],
                'info': 'infoHardMode',
            },
            {
                'type': 'checkbox',
                'key': "squda_randomtext", 
                'label': "randomizeAllText",
                'info': 'infoRandomizeText',
            },
            {
                'type': 'checkbox',
                'key': "squda_chaosemeralds", 
                'label': "enableEmeraldsText",
            },
            {
                'type': 'checkbox',
                'key': "squda_disablemortal", 
                'label': "disableMortalDamageText",
            },
            {
                'type': 'checkbox',
                'key': "squda_parryalways", 
                'label': "parryAlwaysText", 
                'sound': [
                    'attempt_parry', 
                    'voicelines/kris/pickup'
                ],
            },
            {
                'type': 'checkbox',
                'key': "squda_dontshutdown", 
                'label': "dontShutdownText", 
                'sound': ['gooditem', 'baditem'],
                'info': 'infoNoShutdown',
            },
            {
                'type': 'checkbox',
                'key': "squda_nowiggledance", 
                'label': "noWiggleText",
                'info': 'infoNoWiggle',
            },
            {
                'type': 'checkbox',
                'key': "squda_dontdomarioman", 
                'label': "noMarioDelayText", 
                'sound': ['blip', 'quit'],
                'info': 'infoMarioDelay',
            },
            {
                'type': 'checkbox',
                'key': "squda_richpresence", 
                'label': "discordRpcText",
            },
            {
                'type': 'checkbox',
                'key': "squda_enablemeter", 
                'label': "enableMeterText", 
                'sound': ['shield2', 'shieldReflect'],
            },
            {
                'type': 'checkbox',
                'key': "squda_nosugarcoats", 
                'label': "noSugarcoatingText", 
                'sound': ['bellLow', 'bellMed'],
                'info': 'infoNoSugarcoating',
            },
            {
                'type': 'checkbox',
                'key': "squda_specialmusic", 
                'label': "specialMusicText",
                'info': 'infoSpecialMusic',
            },
            {
                'type': 'checkbox',
                'key': "squda_customfont", 
                'label': "customFontText",
                'info': 'infoCustomFont',
            },
            {
                'type': 'checkbox',
                'key': "squda_blood", 
                'label': "enableBloodText", 
                'sound': ['gibbed', 'party_blower'],
            },
            {
                'type': 'checkbox',
                'key': "squda_noparticles", 
                'label': "noParticlesText"
            },
            {
                'type': 'checkbox',
                'key': "squda_coopnames", 
                'label': "coopNamesText",
                'info': 'infoCoopNames',
            },
            {
                'type': 'checkbox',
                'key': "squda_pausemusic", 
                'label': "pauseMusicText",
            },
            {
                'type': 'checkbox',
                'key': "squda_showerrors", 
                'label': "showErrorsText", 
                'sound': ['dev_epicfail', 'spawn'],
                'info': 'infoShowErrors',
            },
            {
                'type': 'checkbox',
                'key': "squda_botnames", 
                'label': "botNamesText",
            },
            {
                'type': 'checkbox',
                'key': "squda_randomgrace",
                'label': "randomEntitiesText", 
                'sound': ['mikiwhatthefuck', 'mikiwhatthefuck2'],
            },
            {
                "type": "popup",
                "label": "entityChance",
                "choices": [0.1, 0.3, 0.5, 0.8, 1.0],
                "display": [
                    bui.Lstr(resource=f"{self._r}.chance{_format_chance(c)}")
                    for c in [0.1, 0.3, 0.5, 0.8, 1.0]
                ],
                "current": bui.app.config.get("squda_entitychance"),
                "callback": self._chance_choice,
                "sub_option": True,
            },
            {
                "type": "popup",
                "label": "menuMusic",
                "choices": music_choices,
                "display": music_cdisp,
                "current": bui.app.config.get("squda_menumusic"),
                "callback": self._music_choice,
            },
            {
                "type": "popup",
                "label": "ultraMeter",
                "choices": meter_choices,
                "display": meter_cdisp,
                "current": bui.app.config.get("squda_ultrameter"),
                "callback": self._meter_choice,
            },
            {
                "type": "multi_button",
                "label": "favChar",
                "buttons": [
                    {
                        "label": (
                            bui.app.config.get('squda_favchar')
                            or bui.Lstr(resource=f"{self._r}.pickChar")
                        ),
                        'key': 'favChar',
                        "callback": self.open_characters,
                    },
                    {
                        "label": bui.Lstr(resource=f"{self._r}.resetText"),
                        'key': 'favCharReset',
                        "callback": self.reset_character,
                    },
                ],
            },
            {
                'type': 'button',
                'label': 'powerupSetup',
                'callback': self._open_powerup_setup,
            },
        ]
        # add rename and reset button if not in survey
        if not first_time:
            settings.append({
                'type': 'button',
                'label': 'nameSetup',
                'callback': self._open_name_setup,
            })
            settings.append({
                'type': 'button',
                'label': 'resetAchievements',
                'callback': self._reset_achievements,
            })
        settings.append({
            'type': 'button',
            'label': 'openOnlineWindow',
            'callback': OnlineSettings,
        })
        return settings