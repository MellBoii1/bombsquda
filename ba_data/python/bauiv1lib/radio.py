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
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 700
        self._height = 350
        scale = (
            1.55
            if uiscale is bui.UIScale.SMALL
            else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        stack_offset = (
            (15, -40) 
            if uiscale is bui.UIScale.SMALL else 
            (0, -30) 
            if uiscale is bui.UIScale.MEDIUM else 
            (0, -5)
        )
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
                scale=scale,
                stack_offset=stack_offset,
            ),
            # We exist in the overlay stack so main-windows being
            # recreated doesn't affect us.
            prevent_main_window_auto_recreate=False,
        )
        uiscale = bui.app.ui_v1.uiscale
        self._back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(self._width - 700, self._height - 80),
            size=(80, 80),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.3,
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.close,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        
        musics = [music_type for music_type in dir(bs.MusicType) if not music_type.startswith('__')]
        choices_display = []
        def format_music_val(music_val: str | dict):
            if isinstance(music_val, dict):
                return f'{music_val.get('title')} - {music_val.get('artist')}'
            else:
                return music_val
        choices_display.extend(
            bs.Lstr(
                value=format_music_val(
                    bs._music.get_music_value(music)
                )
            )
            for music in musics
        )
        self.popup = PopupMenu(
            parent=self._root_widget,
            position=(self._width - 500, self._height - 250),
            width=250,
            autoselect=True,
            on_value_change_call=bui.WeakCall(self._on_menu_choice),
            # You're welcome
            # - gummy
            choices=musics,
            choices_display=choices_display,
            button_size=(300, 70),
        )
        self.choice2 = musics[0]
        
        # i LOOVE lstrs!
        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 105),
            size=(0, 0),
            scale=1.0,
            text=bs.Lstr(resource='boomboxWindowText'),
            color=(1, 1, 1),
            h_align='center',
            v_align='center',
        )
        
        self.play_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(self._width - 440, self._height - 330),
            size=(80, 80),
            color=(0.3, 0.6, 0.3),
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
        
        if ba.app.config.get("squda_isplayingmusic", True):
            bui.imagewidget(edit=self.animboombox, opacity=1.0)
            bui.imagewidget(edit=self.normalboombox, opacity=0.0)
        else:
            bui.imagewidget(edit=self.normalboombox, opacity=1.0)
            bui.imagewidget(edit=self.animboombox, opacity=0.0)
            
        self.prefix = "boomboxon"
        self.frame_count = 2
        self.frame_delay = 0.3
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
        if ba.app.config.get("squda_isplayingmusic", True):
            bs.localsetmusic(getattr(bs.MusicType, self.choice2))
            
    def stopmusic(self):
        bui.imagewidget(edit=self.animboombox, opacity=0.0)
        bui.imagewidget(edit=self.normalboombox, opacity=1.0)
        bs.localsetmusic(None)
        bui.app.config['squda_isplayingmusic'] = False
        
    def playmusic(self):
        bui.imagewidget(edit=self.animboombox, opacity=1.0)
        bui.imagewidget(edit=self.normalboombox, opacity=0.0)
        bs.localsetmusic(getattr(bs.MusicType, self.choice2))
        bui.app.config['squda_isplayingmusic'] = True
