# Released under the MIT License. See LICENSE for details.
#
"""Profile editing window."""

from __future__ import annotations

from threading import Thread
from typing import cast, override, Sequence

import bauiv1 as bui
import bascenev1 as bs
import os

import mellboii.mell_resources as mell

from bauiv1lib.texturepicker import TexturePicker
from bauiv1lib.colorpicker import ColorPicker
from pathlib import Path

class SqudaProfileEditWindow(bui.MainWindow):
    """Window for editing profile data."""
    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):      
        uiscale = bui.app.ui_v1.uiscale
        self._r = 'friendsTab'
        self._loading = False
        self._closed = False

        # Default placeholder values while loading.
        self._profile = {}

        self._texture = 'null'
        self._cmtexture = 'white'

        self._color = (1, 1, 1)
        self._highlight = (1, 1, 1)

        self._username = ''
        self._status = ''

        # Profile load state.
        self._profile_loaded = False

        self._width = 1000 if uiscale is bui.UIScale.SMALL else 760
        self._height = 600

        self._sub_width = 700
        self._sub_height = 670

        assert bui.app.classic is not None

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=(
                    1.3
                    if uiscale is bui.UIScale.SMALL
                    else 1.1
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
                stack_offset=(
                    (0, -20)
                    if uiscale is bui.UIScale.SMALL
                    else (0, 0)
                ),
                transition=transition,
                scale_origin_stack_offset=(
                    origin_widget.get_screen_space_center()
                    if origin_widget
                    else None
                ),
            ),
            origin_widget=origin_widget,
            transition=transition,
        )
        self._build_loading_ui()

        Thread(
            target=self._load_profile_thread,
            daemon=True,
        ).start()

    def _build_ui(self):
        root = self._root_widget
        # normal ui
        self._back_button = bui.buttonwidget(
            parent=root,
            position=(45, self._height - 70),
            size=(55, 55),
            scale=0.8,
            autoselect=True,
            label=bui.charstr(
                bui.SpecialChar.BACK
            ),
            button_type='backSmall',
            on_activate_call=self.main_window_back,
        )
        bui.containerwidget(
            edit=root,
            cancel_button=self._back_button,
        )
        # title
        bui.textwidget(
            parent=root,
            position=(
                self._width * 0.5,
                self._height - 45,
            ),
            size=(0, 0),
            text=bui.Lstr(
                resource=f'{self._r}.profileEditTitle'
            ),
            color=bui.app.ui_v1.title_color,
            scale=1.3,
            h_align='center',
            v_align='center',
        )
        self._scrollwidget = bui.scrollwidget(
            parent=root,
            position=(35, 40),
            size=(
                self._width - 70,
                self._height - 120,
            ),
            simple_culling_v=20.0,
            border_opacity=0.4,
        )
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(
                self._sub_width,
                self._sub_height,
            ),
            background=False,
        )
        y = self._sub_height - 50
        # profile section
        self._section_title(
            'Profile',
            y,
        )
        y -= 50
        self._username_field = self._text_setting(
            label='Username',
            text=self._username,
            y=y,
        )
        y -= 50
        self._status_field = self._text_setting(
            label='Status',
            text=self._status,
            y=y,
        )
        y -= 70
        # avatar section
        self._section_title(
            'Appearance',
            y,
        )
        y -= 130
        self._build_avatar_section(y)

        y -= 60
        # colors section
        self._section_title(
            'Colors',
            y,
        )
        y -= 100
        self._build_color_buttons(y)
        y -= 120
        self._build_save_button(y)

    def _section_title(
        self,
        text: str | bui.Lstr,
        y: float,
    ):

        return bui.textwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.08,
                y,
            ),
            text=text,
            h_align='left',
            v_align='center',
            scale=1.0,
            color=(0.75, 0.75, 0.75),
            maxwidth=self._sub_width * 0.8,
        )

    def _text_setting(
        self,
        *,
        label: str,
        text: str,
        y: float,
        max_chars: int = 64,
    ):

        label_x = self._sub_width * 0.08
        field_x = self._sub_width * 0.33

        bui.textwidget(
            parent=self._subcontainer,
            position=(label_x, y + 5),
            text=label,
            h_align='left',
            v_align='center',
            scale=0.9,
            color=(0.8, 0.8, 0.8),
        )

        return bui.textwidget(
            parent=self._subcontainer,
            position=(field_x, y),
            size=(420, 50),
            text=text,
            editable=True,
            max_chars=max_chars,
            v_align='center',
            corner_scale=0.7,
            autoselect=True,
        )
    def _build_avatar_section(
        self,
        y: float,
    ):

        center_x = self._sub_width * 0.5

        # Preview.

        self._icon_preview = bui.imagewidget(
            parent=self._subcontainer,
            position=(center_x - 64, y),
            texture=bui.gettexture(self._texture),
            tint_texture=bui.gettexture(self._cmtexture),
            mask_texture=bui.gettexture('characterIconMask'),
            tint_color=self._color,
            tint2_color=self._highlight,
            size=(128, 128),
        )

        # Avatar button.
        self._texture_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(center_x - 210, y + 18),
            size=(90, 90),
            label='',
            texture=bui.gettexture(self._texture),
            on_activate_call=bui.Call(
                self.open_texture_picker,
                'tex',
                (center_x - 210, y + 18),
            ),
            color=(1, 1, 1),
        )

        # Mask button.
        self._cm_texture_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(center_x + 120, y + 18),
            size=(90, 90),
            label='',
            texture=bui.gettexture(
                self._cmtexture
            ),
            on_activate_call=bui.Call(
                self.open_texture_picker,
                'cmtex',
                (center_x + 120, y + 18),
            ),
            color=(1, 1, 1),
        )
        x = 20
        bui.textwidget(
            parent=self._subcontainer,
            position=(center_x - 210 + x, y - 20),
            text='Avatar',
            scale=0.75,
            color=(0.7, 0.7, 0.7),
            h_align='center',
        )

        bui.textwidget(
            parent=self._subcontainer,
            position=(center_x + 120 + x, y - 20),
            text='Overlay',
            scale=0.75,
            color=(0.7, 0.7, 0.7),
            h_align='center',
        )

    def _build_color_buttons(
        self,
        y: float,
    ):

        spacing = 120
        start_x = (
            self._sub_width * 0.3
        )

        self._color_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(start_x, y),
            size=(100, 100),
            color=self._color,
            label='',
            button_type='square',
            on_activate_call=bui.WeakCall(
                self._make_picker,
                'color',
                (start_x, y),
            ),
        )

        self._highlight_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(
                start_x + spacing,
                y,
            ),
            size=(100, 100),
            color=self._highlight,
            label='',
            button_type='square',
            on_activate_call=bui.WeakCall(
                self._make_picker,
                'highlight',
                (
                    start_x + spacing,
                    y,
                ),
            ),
        )

        bui.textwidget(
            parent=self._subcontainer,
            position=(start_x + 50, y - 40),
            text='Color',
            scale=0.8,
            color=(0.75, 0.75, 0.75),
            h_align='center',
        )

        bui.textwidget(
            parent=self._subcontainer,
            position=(
                start_x + spacing + 50,
                y - 40,
            ),
            text='Highlight',
            scale=0.8,
            color=(0.75, 0.75, 0.75),
            h_align='center',
        )

    def _build_save_button(
        self,
        y: float,
    ):
        self._spinner = bui.spinnerwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.5,
                y + 38,
            ),
            visible=False,
        )

        self._save_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.2,
                y,
            ),
            size=(
                self._sub_width * 0.6,
                70,
            ),
            label=bui.Lstr(
                resource=f'{self._r}.saveToServerText'
            ),
            on_activate_call=bui.WeakCall(
                self._save_data,
            ),
        )

    def _save_data(self):
        if self._loading:
            return
        if not self._profile_loaded:
            return
        self._loading = True
        bui.spinnerwidget(
            edit=self._spinner,
            visible=True,
        )
        bui.buttonwidget(
            edit=self._save_button,
            label='',
        )
        Thread(
            target=self._save_thread,
            daemon=True,
        ).start()

    def _save_thread(self):

        data = {
            'avatar': self._texture,
            'cm_avatar': self._cmtexture,
            'color': list(self._color),
            'highlight': list(
                self._highlight
            ),
            'username': cast(
                str,
                bui.textwidget(
                    query=self._username_field
                ),
            ).strip(),
            'status': cast(
                str,
                bui.textwidget(
                    query=self._status_field
                ),
            ).strip(),
        }

        result = mell.set_profile_data(data)

        bs.pushcall(
            bui.Call(
                self._finish_save,
                result,
            ),
            from_other_thread=True,
        )

    def _finish_save(
        self,
        result: dict,
    ):

        self._loading = False
        if self._closed:
            return
        bui.spinnerwidget(
            edit=self._spinner,
            visible=False,
        )
        bui.buttonwidget(
            edit=self._save_button,
            label=bui.Lstr(
                resource=f'{self._r}.saveToServerText'
            ),
        )
        if (
            result.get('status')
            in ['error', 'fail']
            or result.get('error')
        ):
            bui.screenmessage(
                str(
                    result.get(
                        'error',
                        result.get(
                            'message',
                            bui.Lstr(r=f'{self._r}.unknownError'),
                        ),
                    )
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        bui.screenmessage(
            bui.Lstr(resource=f'{self._r}.savedText'),
            color=(0, 1, 0),
        )
        bui.getsound('ding').play()
        self.main_window_back()

    def open_texture_picker(
        self,
        picker_type: str,
        origin: tuple[float, float],
    ):
        # it's a little unsafe to be allowing everyone to
        # just access the textures and use them... but,
        # i do kinda want them to get creative and mesh together
        # textures to make a neat looking avatar!
        # ...or just make a character's icon manually. eh.
        path = os.path.join(
            bui.app.env.data_directory,
            'ba_data',
            'textures',
        )
        # get the stem so we only get filename
        textures = [f.stem for f in Path(path).iterdir() if f.is_file()]
        TexturePicker(
            delegate=self,
            tag=picker_type,
            position=origin,
            parent=self._root_widget,
            textures=textures,
        )

    def _make_picker(
        self,
        picker_type: str,
        origin: tuple[float, float],
    ):

        ColorPicker(
            parent=self._root_widget,
            position=origin,
            initial_color=(
                self._color
                if picker_type == 'color'
                else self._highlight
            ),
            delegate=self,
            tag=picker_type,
        )

    def color_picker_selected_color(
        self,
        picker: ColorPicker,
        color: tuple[float, float, float],
    ):

        tag = picker.get_tag()

        if tag == 'color':
            self._color = color
            bui.buttonwidget(
                edit=self._color_button,
                color=color,
            )

        elif tag == 'highlight':
            self._highlight = color
            bui.buttonwidget(
                edit=self._highlight_button,
                color=color,
            )

        self._update_preview()

    def texture_picker_selected(
        self,
        picker: TexturePicker,
        texture: str,
    ):
        picker_type = picker.get_tag()

        if picker_type == 'tex':
            self._texture = texture
            bui.buttonwidget(
                edit=self._texture_button,
                texture=bui.gettexture(texture),
            )

        elif picker_type == 'cmtex':
            self._cmtexture = texture
            bui.buttonwidget(
                edit=self._cm_texture_button,
                texture=bui.gettexture(texture),
            )

        self._update_preview()

    def _update_preview(self):
        bui.imagewidget(
            edit=self._icon_preview,
            texture=bui.gettexture(
                self._texture
            ),
            tint_texture=bui.gettexture(
                self._cmtexture
            ),
            tint_color=self._color,
            tint2_color=self._highlight,
        )

    def on_main_window_close(self):
        self._closed = True
    
    def texture_picker_closing(self, yeah):
        pass
    
    def color_picker_closing(self, yeah):
        pass
    
    def _build_loading_ui(self):
        root = self._root_widget
        self._back_button = bui.buttonwidget(
            parent=root,
            position=(45, self._height - 70),
            size=(55, 55),
            scale=0.8,
            autoselect=True,
            label=bui.charstr(
                bui.SpecialChar.BACK
            ),
            button_type='backSmall',
            on_activate_call=self.main_window_back,
        )
        bui.containerwidget(
            edit=root,
            cancel_button=self._back_button,
        )
        bui.textwidget(
            parent=root,
            position=(
                self._width * 0.5,
                self._height - 45,
            ),
            size=(0, 0),
            text=bui.Lstr(
                resource=f'{self._r}.profileEditTitle'
            ),
            color=bui.app.ui_v1.title_color,
            scale=1.3,
            h_align='center',
            v_align='center',
        )
        self._loading_spinner = bui.spinnerwidget(
            parent=root,
            position=(
                self._width * 0.5,
                self._height * 0.5,
            ),
            visible=True,
        )
    
    def _load_profile_thread(self):
        """Load profile in background."""

        try:
            result = mell.get_info_from_id(
                mell.get_unique_bs_id()
            )
            bs.pushcall(
                bui.Call(
                    self._finish_loading_profile,
                    result,
                ),
                from_other_thread=True,
            )
        except Exception as exc:
            bs.pushcall(
                bui.Call(
                    self._finish_loading_profile,
                    {
                        'error': str(exc),
                    },
                ),
                from_other_thread=True,
            )
    
    def _finish_loading_profile(
        self,
        result: dict,
    ):
        """Finish profile loading."""

        if self._closed:
            return
        # Hide spinner.
        bui.spinnerwidget(
            edit=self._loading_spinner,
            visible=False,
        )
        # Handle errors.
        if (
            result.get('status')
            in ['error', 'fail']
            or result.get('error')
        ):
            bui.screenmessage(
                str(
                    result.get(
                        'error',
                        result.get(
                            'message',
                            bui.Lstr(
                                r=f'{self._r}.unknownError'
                            ),
                        ),
                    )
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            bui.apptimer(
                0,
                self.main_window_back,
            )
            return
        # Save loaded profile.
        self._profile = result
        self._texture = result.get(
            'avatar',
            'null',
        )
        self._cmtexture = result.get(
            'cm_avatar',
            'white',
        )
        self._color = tuple(
            result.get(
                'color',
                (1, 1, 1),
            )
        )
        self._highlight = tuple(
            result.get(
                'highlight',
                (1, 1, 1),
            )
        )
        self._username = result.get(
            'username',
            '',
        )
        self._status = result.get(
            'status',
            '',
        )
        self._profile_loaded = True
        # Build actual UI.
        self._build_ui()
            
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
            )
        )