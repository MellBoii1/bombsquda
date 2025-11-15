""" i dunno """

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib.popup import PopupMenu
import babase as ba

if TYPE_CHECKING:
    from typing import Any, Callable

class RadioWindow(bui.Window):
    """
    Window for using the UI for
    setting player-chosen MusicTypes
    to play locally. For use with online and such.
    """

    def __init__(self, origin: Sequence[float] = (0, 0)):
        bui.set_party_window_open(True)
        self._width = 700
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._height= 350
        self.choice2 = 'MENU'
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
            ),
            # We exist in the overlay stack so main-windows being
            # recreated doesn't affect us.
            prevent_main_window_auto_recreate=False,
        )
        uiscale = bui.app.ui_v1.uiscale
        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.close
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=False,
                position=(self._width - 700, self._height - 80),
                size=(80, 80),
                color=(0.7, 0.3, 0.3),
                textcolor=(1, 1, 1),
                scale=0.8,
                text_scale=1.3,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.close,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        self.popup = PopupMenu(
            parent=self._root_widget,
            position=(self._width - 500, self._height - 250),
            width=250,
            autoselect=True,
            on_value_change_call=bui.WeakCall(self._on_menu_choice),
            choices= [
                'MENU',
                'MENU2',
                'MENU3',
                'MENU6',
                'MENU7',
                'MENU8',
                'MENU9',
                'MENU10',
                'MENU11',
                'MENU12',
                'MENU67',
                'Victory',
                'VictoryFinal',
                'Char_Select',
                'Char_Select2',
                'Tutorial',
                'Run_Away',
                'ModulatingTime',
                'Onslaught2',
                'Onslaught3',
                'Keep_Away',
                'Race',
                'Gambling',
                'Epic_Race',
                'Scores',
                'Grand_Romp',
                'MetalCapTime',
                'Rage',
                'NoiseSuper',
                'Reprieve',
                'Business',
                'To_The_Death',
                'To_The_DeathFast',
                'To_The_Death2Fast',
                'To_The_Death2',
                'To_The_Death3Fast',
                'To_The_Death3',
                'Keep_Away2',
                'Chosen_One',
                'Forward_March',
                'Flag_Catcher',
                'Survival',
                'Epic',
                'Online',
                'Pause',
                'D_RUNNIN', 
                'EpicFast',
                'Sports',
                'Hockey',
                'Football',
                'Flying',
                'Flying2',
                'Scary',
                'Cookin',
                'Marching',
                'Defeat',
                'Credits',
                'TheFinale',
                'RunaroundFinal',
                'War',
                'Lap0',
                'Lap1',
                'Lap2',
                'Lap3',
                'Lap4',
                'Lap5',
                'Lap6',
                'Lap7',
                'Lap8',
                'Lap9',
                'SNESCourse',
                'SNESCourse2',
                'DS1',
                'DS2',
                'DS3',
                'StrongOne',
                'SURVEY',
                'Opening',
            ],
            button_size=(300, 70),
        )
        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 105),
            size=(0, 0),
            scale=0.75 if uiscale is bui.UIScale.SMALL else 1.0,
            text='Welcome to the Boombox.\nThis allows you to play any of the game\'s music\nINCLUDING whenever in a online party. \nSelect a MusicType and press play to start.',
            color=(1, 1, 1),
            h_align='center',
            v_align='center',
        )
        self.play_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(self._width - 440, self._height - 330),
            size=(80, 80),
            color=(0.6, 0.3, 0.3),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.3,
            label=bui.charstr(bui.SpecialChar.PLAY_BUTTON),
            on_activate_call=self.playmusic,
        )
        self.stop_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(self._width - 340, self._height - 330),
            size=(80, 80),
            color=(0.6, 0.3, 0.3),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.3,
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_SQUARE_BUTTON),
            on_activate_call=self.stopmusic,
        )
        self.normalboombox = bui.imagewidget(
            parent=self._root_widget,
            position=(self._width * 0.28, self._height - 100),
            size=(300, 300),
            texture=bui.gettexture('boomboxoff'),
            opacity=1.0,
        )
        self.animboombox = bui.imagewidget(
            parent=self._root_widget,
            position=(self._width * 0.28 + 5, self._height - 100),
            size=(300, 300),
            texture=bui.gettexture('boomboxon1'),
            opacity=0.0,
        )
        
        if ba.app.config.get("isplayingmusic", True):
            bui.imagewidget(edit=self.animboombox, opacity=1.0)
            bui.imagewidget(edit=self.normalboombox, opacity=0.0)
        else:
            bui.imagewidget(edit=self.normalboombox, opacity=1.0)
            bui.imagewidget(edit=self.animboombox, opacity=0.0)
            
        self.prefix = "boomboxon"
        self.frame_count = 2
        self.frame_delay = 0.5
        self._current_frame = 1
        # Start the animation timer.
        self._timer = ba.AppTimer(self.frame_delay, self._next_frame, repeat=True)

    def _next_frame(self):
        """Advance to the next frame."""
        self._current_frame += 1

        # Wrap around if looping.
        if self._current_frame > self.frame_count:
            self._current_frame = 1

        tex_name = f"{self.prefix}{self._current_frame}"
        try:
            bui.imagewidget(edit=self.animboombox, texture=bui.gettexture(tex_name))
        except:
            self._timer = None
    def close(self) -> None:
        """Close the window."""
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
        self._timer = None
    def _on_menu_choice(self, choice: str) -> None:
        self.choice2 = choice.upper()
        if ba.app.config.get("isplayingmusic", True):
            bs.localsetmusic(getattr(bs.MusicType, self.choice2))
    def stopmusic(self):
        bui.imagewidget(edit=self.animboombox, opacity=0.0)
        bui.imagewidget(edit=self.normalboombox, opacity=1.0)
        bs.localsetmusic(None)
        bui.app.config['isplayingmusic'] = False
    def playmusic(self):
        bui.imagewidget(edit=self.animboombox, opacity=1.0)
        bui.imagewidget(edit=self.normalboombox, opacity=0.0)
        bs.localsetmusic(getattr(bs.MusicType, self.choice2))
        bui.app.config['isplayingmusic'] = True
