"""Script that contains a setup for first time players."""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence, override, cast
import logging

import bauiv1 as bui
import bascenev1 as bs
import babase as ba

if TYPE_CHECKING:
    from typing import Callable
    
SURVEY_STEPS = [
    dict(
        prompt=ba.Lstr(resource='surveyPrompt1'),
        texture="earthbound/spazbound",
        cfg="squda_ch1name",
    ),
    dict(
        prompt=ba.Lstr(resource='surveyPrompt2'),
        texture="earthbound/krisbound",
        cfg="squda_ch2name",
    ),
    dict(
        prompt=ba.Lstr(resource='surveyPrompt3'),
        texture="earthbound/snakebound",
        cfg="squda_ch3name",
    ),
    dict(
        prompt=ba.Lstr(resource='surveyPrompt4'),
        texture="earthbound/noobbound",
        cfg="squda_ch4name",
    ),
]
    
class BaseSurveyWindow(bui.MainWindow):
    def __init__(self, *, height=670, transition='in_right', origin_widget=None):
        bui.set_analytics_screen('SURVEYWindow')
        uiscale = bui.app.ui_v1.uiscale

        width = 1000 if uiscale is bui.UIScale.SMALL else 800
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
                toolbar_visibility='menu_minimal',
            ),
            transition=transition,
            origin_widget=origin_widget,
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        self.title = bui.textwidget(
            parent=self._root_widget,
            position=(15, self._yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource='SURVEYWindow.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )
    @override
    def get_main_window_state(self):
        raise RuntimeError(
            f'{type(self).__name__} must override get_main_window_state()'
        )

class NameSurveyWindow(BaseSurveyWindow):
    @staticmethod
    def _create(t, o, step_index):
        return NameSurveyWindow(
            transition=t,
            origin_widget=o,
            step_index=step_index,
        )

    def __init__(self, *, step_index: int, **kw):
        super().__init__(**kw)

        self._step_index = step_index
        self.step = SURVEY_STEPS[step_index]
        self.key = self.step["cfg"]
        uiscale = bui.app.ui_v1.uiscale
        xoffs = 15
        yoffs = 0
        if uiscale is bui.UIScale.SMALL:
            xoffs = 30
            yoffs = -60
        self.prompt = bui.textwidget(
            parent=self._root_widget,
            text=self.step["prompt"],
            position=(self._width * 0.32 + xoffs, self._height - 220 + yoffs),
            size=(300, 200),
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
        )
        xoffs = 0
        yoffs = 0
        
        imgsize = (
            (220, 220) 
            if uiscale is 
            not bui.UIScale.SMALL 
            else (160, 160)
        )
        xoffs = 20
        if uiscale is bui.UIScale.SMALL:
            xoffs = 80
            yoffs = 0
        self.image = bui.imagewidget(
            parent=self._root_widget,
            position=(self._width * 0.35 + xoffs, self._height - 380 + yoffs),
            size=imgsize,
            texture=bui.gettexture(self.step["texture"]),
        )
        xoffs = 0

        if uiscale is bui.UIScale.SMALL:
            xoffs = -60
            yoffs = 30
        self._text_field = txt =  bui.textwidget(
            parent=self._root_widget,
            position=(self._width / 5.0 + xoffs, self._height - 470 + yoffs),
            size=(self._width - 270, 45),
            editable=True,
            autoselect=True,
        )
        
        # "confirm changes by pressing enter or ok"
        if uiscale is bui.UIScale.SMALL:
            xoffs = 0
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width / 5.5 + xoffs, self._height - 510 + yoffs),
            size=(self._width - 400, 45),
            text=bui.Lstr(
                resource='surveyHelpText', 
                subs=[
                    ('${OK}', bui.Lstr(resource='okText'))
                ],
            ),
            scale=0.7,
            color=bui.app.ui_v1.title_color
        )
        
        ok_scale = (80, 70)
        xoffs = 15
        if uiscale is bui.UIScale.SMALL:
            xoffs = -115
            yoffs += 20
            ok_scale = (500, 70)
        self.ok_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(370 + xoffs, self._height - 600 + yoffs),
            size=ok_scale,
            label=bui.Lstr(resource='okText'),
            on_activate_call=self._on_ok,
            enable_sound=False,
        )
        if self._step_index > 0:
            if uiscale is bui.UIScale.SMALL:
                bui.containerwidget(
                    edit=self._root_widget, on_cancel_call=self.on_back
                )
            else:
                btn = bui.buttonwidget(
                    parent=self._root_widget,
                    position=(self._width / 15.0, self._height - 50),
                    size=(60, 55),
                    scale=0.9,
                    label=bui.charstr(bui.SpecialChar.BACK),
                    button_type='backSmall',
                    extra_touch_border_scale=2.0,
                    autoselect=True,
                    on_activate_call=self.on_back,
                )
                bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        bui.textwidget(edit=txt, on_return_press_call=lambda: self._on_ok('survey_ok2'))

    def _on_ok(self, sound: str = 'survey_ok'):
        if not self.main_window_has_control():
            return
        bui.getsound(sound).play()
        user_input = cast(str, bui.textwidget(query=self._text_field)).strip()
        if user_input == '':
            bui.screenmessage('You must input a name.')
            bui.getsound('error').play()
            return

        bui.app.config[self.key] = user_input
        bui.app.config.apply_and_commit()
        bui.buttonwidget(edit=self.ok_btn, on_activate_call=None)
        bui.textwidget(edit=self._text_field, on_return_press_call=None)

        next_index = self._step_index + 1

        if next_index < len(SURVEY_STEPS):
            self.main_window_replace(
                NameSurveyWindow(
                    transition='in_right',
                    origin_widget=self._root_widget,
                    step_index=next_index,
                )
            )
        else:
            self.main_window_replace(
                SurveyIntroWindow(
                    transition='in_right',
                    origin_widget=self._root_widget,
                    step=0,
                )
            )
    def on_back(self):
        if self._step_index < 0:
            bui.getsound('error').play()
            return
        bui.getsound('survey_back').play()
        self.main_window_back()
    
    @override
    def get_main_window_state(self):
        return bui.BasicMainWindowState(
            create_call=lambda t, o, si=self._step_index:
                NameSurveyWindow._create(t, o, si)
        )

class SurveyIntroWindow(bui.MainWindow):
    """First-time setup intro flow before/after BombSquda settings."""
    @staticmethod
    def _create(t, o, step):
        return SurveyIntroWindow(
            transition=t,
            origin_widget=o,
            step=step,
        )
    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        step: int = 0,
    ):
        self._step = step

        bui.set_analytics_screen('SURVEYWindow')
        assert bui.app.classic is not None

        uiscale = bui.app.ui_v1.uiscale
        self.uiscale = uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 450

        screensize = bui.get_virtual_screen_size()
        safesize = bui.get_virtual_safe_area_size()
        smallscale = min(2.0, 1.5 * screensize[0] / safesize[0])
        scale = (
            smallscale
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
        )

        target_height = min(height - 70, screensize[1] / scale)
        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility='menu_minimal',
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )
        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(width / 10.0, yoffs - 80.0),
                size=(70, 70),
                scale=0.8,
                text_scale=1.2,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        self._build_step(height)

    # --------------------------------------------------

    def _build_step(self, height: float) -> None:
        if self._step == 0:
            text = 'Now, please select \nyour settings.'
            buttons = [('OK', self._start_settings)]

        elif self._step == 1:
            text = 'Do you acknowledge \nthe possibility\nof not enjoying \nthis experience?'
            buttons = [
                ('NO', self._next),
                ('YES', self._next),
            ]

        else:
            text = (
                'Good. Very good. \nYour answers\n'
                'shall be recorded.\n'
                'Do you want to move on?'
            )
            buttons = [
                ('NO', self._fucking_die),
                ('YES', self._finish),
            ]
        xoffs = 0
        if self.uiscale is bui.UIScale.SMALL:
            xoffs = 100
        bui.textwidget(
            parent=self._root_widget,
            text=text,
            position=(250 + xoffs, height - 280),
            maxwidth=400,
            size=(300, 300),
            scale=1.5,
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
        )

        x = 300 if len(buttons) > 1 else 360
        if self.uiscale is bui.UIScale.SMALL:
            size = (350, 80)
            xoffs = -30
            height_offs = 320
        else:
            size = (80, 70)
            height_offs = 400
        y = height - height_offs
        for label, call in buttons:
            bui.buttonwidget(
                parent=self._root_widget,
                position=(x + xoffs, y),
                size=size,
                autoselect=(label == 'YES' or label == 'OK'),
                label=label,
                on_activate_call=call,
            )
            if self.uiscale is bui.UIScale.SMALL:
                y -= 100
            else:
                x += 100

    # --------------------------------------------------

    def _next(self) -> None:
        if not self.main_window_has_control():
            return
        self.main_window_replace(
            SurveyIntroWindow(
                transition='in_right',
                origin_widget=self._root_widget,
                step=self._step + 1,
            )
        )
    def _start_settings(self) -> None:
        from bauiv1lib.settings.melsection import MelWindow
        if not self.main_window_has_control():
            return
        self.main_window_replace(
            MelWindow(
                transition='in_right',
                origin_widget=self._root_widget,
                first_time=True,
            )
        )
    def _fucking_die(self) -> None:
        if getattr(self, 'alrquit', False):
            return
        self.alrquit = True
        bui.screenmessage('Oh.')
        bs.setmusic(None)
        bui.apptimer(1.2, lambda: bui.screenmessage('well then gtfo jackass'))
        bui.apptimer(1.2, bui.getsound('boo').play)
        bui.apptimer(1.5, ba.quit)

    def _finish(self) -> None:
        if not self.main_window_has_control():
            return
        # set config and ui state
        bui.app.config['squda_playersfirsttime'] = False
        bui.app.config.apply_and_commit()
        bui.app.ui_v1.clear_main_window()
        # pushcall new session
        bs.pushcall(lambda: bs.new_host_session(SurveySessionThing2))


    # --------------------------------------------------
    @override
    def get_main_window_state(self):
        return bui.BasicMainWindowState(
            create_call=lambda t, o, s=self._step:
                SurveyIntroWindow._create(t, o, s)
        )
        
class SURVEYActivity(bs.Activity[bs.Player, bs.Team]):
    """A blue background. Not much to it."""
    _stdassets = bs.Dependency(bs.AssetPackage, 'stdassets@1')

    def __init__(self, settings: dict):
        super().__init__(settings)

    def on_transition_in(self) -> None:
        bs.setmusic(bs.MusicType.SURVEY)
        self.terrain = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('thePadBG'),
                    'color': (0.1, 0.1, 0.9),
                    'lighting': False,
                    'background': True,
                    'color_texture': bs.gettexture('menuBG'),
                },
            )
        )
        # im stupi (only start main window ON start, not init)
        with bs.ContextRef.empty():
            bui.app.ui_v1.set_main_window(
                NameSurveyWindow(step_index=0),
                is_top_level=True,
                suppress_warning=True,
            )

class SurveySessionThing(bs.Session):
    """Literally just start SURVEYActivity"""
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.setactivity(bs.newactivity(SURVEYActivity))
    @override
    def on_player_request(self, player: bs.SessionPlayer) -> bool:
        # Reject all player requests.
        return False
        
class SurveySessionThing2(bs.Session):
    """Literally just start SURVEYActivity2"""
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.setactivity(bs.newactivity(SURVEYActivity2))
    @override
    def on_player_request(self, player: bs.SessionPlayer) -> bool:
        # Reject all player requests.
        return False
        
class SURVEYActivity2(bs.Activity[bs.Player, bs.Team]):
    """Blue background that fades to our logo."""
    _stdassets = bs.Dependency(bs.AssetPackage, 'stdassets@1')

    def __init__(self, settings: dict):
        super().__init__(settings)
        
    def _makeplayer(self):
        bs.setmusic(bs.MusicType.LOGOTYPE)
        bs.animate_array(
            self.blackthing, 
            "color", 3, 
            {
                0: (0, 0, 0),
                2.5: (1, 1, 1),
                32: (1, 1, 1),
                33: (0, 0, 0),
            }
        )
        bs.animate(
            self.logo, 
            "opacity", 
            {
                3: 0,
                4.7: 1,
                32: 1,
                33: 0,
            }
        )
        sc = self._logo_scale
        sc2 = sc + 0.5
        intex = list(
            bs.gettexture(
                'title_mono_shaky' + str(i + 1)
            ) 
            for i in range(4)
        )
        texs = bs.newnode(
            'texture_sequence',
            attrs={'rate': 100, 'input_textures': intex},
        )
        texs.connectattr('output_texture', self.logo, 'texture')
        def anim():
            nonlocal texs
            bs.animate_array(
                self.logo, 
                "scale", 2, 
                {
                    0: (1024 * sc, 256 * sc),
                    0.07: (1024 * sc2, 256 * sc2),
                    0.4: (1024 * sc, 256 * sc),
                }
            )
            def on():
                nonlocal texs
                texs.rate = 30
            def tw():
                nonlocal texs
                texs.rate = 100
            bs.timer(0.07, on)
            bs.timer(0.4, tw)
        bs.timer(5.1, anim)
        bs.timer(10.5, anim)
        bs.timer(15.4, anim)
        bs.timer(24.5, anim)
        
        
    def on_transition_in(self) -> None:
        from bascenev1lib.mainmenu import MainMenuSession
        self._logo_scale = 0.8
        self.bgterrain = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('thePadBG'),
                    'color': (0.1, 0.1, 0.9),
                    'lighting': False,
                    'background': True,
                    'color_texture': bs.gettexture('menuBG'),
                },
            )
        )
        self.blackthing = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('white2'),
                'opacity': 0.0,
                'fill_screen': True,
                'color': (0, 0, 0)
            }
        )
        self.logo = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('title_mono'),
                'opacity': 0.0,
                'fill_screen': False,
                'color': (1, 1, 1),
                'scale': (1024 * self._logo_scale, 256 * self._logo_scale),
                'opacity': 0,
            }
        )
        bs.setmusic(None)
        bs.animate(
            self.blackthing, 
            "opacity", 
            {
                0.0: 0.0,
                1.5: 1.0
            }
        )
        bs.timer(2.5, self._makeplayer)
        bs.timer(36.0, lambda: bs.pushcall(bs.Call(bs.new_host_session, MainMenuSession)))