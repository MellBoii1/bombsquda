# Released under the MIT License. See LICENSE for details.
#
"""Session and Activity for displaying the main menu bg."""

from __future__ import annotations

import time
import random
import weakref
import datetime
from typing import TYPE_CHECKING, override

from bacommon.locale import LocaleResolved
import bascenev1 as bs
import bauiv1 as bui
import babase as ba
from bascenev1lib.game.surveyprogram import SURVEYActivity
from bascenev1lib.actor.cutsceneplayer import CutscenePlayer

if TYPE_CHECKING:
    from typing import Any

    import bacommon.bs


class MainMenuActivity(bs.Activity[bs.Player, bs.Team]):
    """Activity showing the rotating main menu bg stuff."""

    _stdassets = bs.Dependency(bs.AssetPackage, 'stdassets@1')

    _did_initial_transition = False

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._logo_node: bs.Node | None = None
        self._custom_logo_tex_name: str | None = None
        self._word_actors: list[bs.Actor] = []
        self.my_name: bs.NodeActor | None = None
        self._host_is_navigating_text: bs.NodeActor | None = None
        self.version: bs.NodeActor | None = None
        self.bottom: bs.NodeActor | None = None
        self.vr_bottom_fill: bs.NodeActor | None = None
        self.vr_top_fill: bs.NodeActor | None = None
        self.terrain: bs.NodeActor | None = None
        self.trees: bs.NodeActor | None = None
        self.bgterrain: bs.NodeActor | None = None
        self._ts = 0.86
        self._language: str | None = None
        self._update_timer: bs.Timer | None = None
        self._news: NewsDisplay | None = None
        self._attract_mode_timer: bs.Timer | None = None
        self._logo_rotate_timer: bs.Timer | None = None 
        self.today = datetime.datetime.now()
        self.cutscene_player = None
        self.canstartdemo = True

    
    @override
    def on_transition_in(self) -> None:
        # pylint: disable=too-many-locals
        super().on_transition_in()
        random.seed(123)
        app = bs.app
        env = app.env
        assert app.classic is not None

        plus = bs.app.plus
        assert plus is not None

        # Throw up some text that only clients can see so they know that
        # the host is navigating menus while they're just staring at an
        # empty-ish screen.
        tval = bs.Lstr(
            resource='hostIsNavigatingMenusText',
            subs=[('${HOST}', plus.get_v1_account_display_string())],
        )
        self._host_is_navigating_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'text': tval,
                    'client_only': True,
                    'position': (0, -200),
                    'flatness': 1.0,
                    'h_align': 'center',
                },
            )
        )

        if not self._did_initial_transition and self.my_name is not None:
            assert self.my_name.node
            bs.animate(self.my_name.node, 'opacity', {2.3: 0, 3.0: 1.0})


        # Throw in test build info.
        self.splashtext = self.beta_info_2 = None

        random.seed(time.time())
        chosen_text = bs.Lstr(resource=f'splashText{random.randint(1, 19)}')
        
        pos = (0, -250)
        self.splashtext = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'center',
                    'h_align': 'center',
                    'color': (1, 1, 0, 1),
                    'shadow': 0.5,
                    'flatness': 0.5,
                    'scale': 1,
                    'vr_depth': -60,
                    'position': pos,
                    'text': chosen_text,
                },
            )
        )
        self.modpack_name = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'center',
                    'h_align': 'center',
                    'color': (1, 1, 1, 1),
                    'shadow': 0.5,
                    'flatness': 0.5,
                    'scale': 1,
                    'vr_depth': -60,
                    'position': (225, 35),
                    'text': bs.Lstr(resource=f'modpackName'),
                },
            )
        )

        if not self._did_initial_transition:
            assert self.splashtext.node
            bs.animate(self.splashtext.node, 'opacity', {1.3: 0, 2.5: 1.0})

        mesh = bs.getmesh('snesCourseLevel')
        trees_mesh = bs.getmesh('kronkHand')
        trees_texture = bs.gettexture('kronkHand')
        bottom_mesh = bs.getmesh('kronkHand') # of course we have to use a "blank" model so it dont die...
        color_texture = bs.gettexture('snesCourseColor')
        bgtex = bs.gettexture('DSspace')
        bgmesh = bs.getmesh('DSspace')

        # Load these last since most platforms don't use them.
        vr_bottom_fill_mesh = bs.getmesh('thePadVRFillBottom')
        vr_top_fill_mesh = bs.getmesh('thePadVRFillTop')

        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'

        tint = (1, 1, 1)
        gnode.tint = tint
        gnode.ambient_color = (1.06, 1.04, 1.03)
        gnode.vignette_outer = (0.68, 0.67, 0.87)
        gnode.vignette_inner = (0.83, 0.87, 0.78)

        self.bottom = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bottom_mesh,
                    'lighting': False,
                    'reflection': 'soft',
                    'reflection_scale': [0.45],
                    'color_texture': color_texture,
                },
            )
        )
        self.vr_bottom_fill = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': vr_bottom_fill_mesh,
                    'lighting': False,
                    'vr_only': True,
                    'color_texture': color_texture,
                },
            )
        )
        self.vr_top_fill = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': vr_top_fill_mesh,
                    'vr_only': True,
                    'lighting': False,
                    'color_texture': bgtex,
                },
            )
        )
        self.terrain = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': mesh,
                    'color_texture': color_texture,
                    'reflection': 'soft',
                    'reflection_scale': [0.3],
                },
            )
        )
        self.trees = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': trees_mesh,
                    'lighting': False,
                    'reflection': 'char',
                    'reflection_scale': [0.1],
                    'color_texture': trees_texture,
                },
            )
        )
        self.bgterrain = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bgmesh,
                    'color': (0.92, 0.91, 0.9),
                    'lighting': False,
                    'background': True,
                    'color_texture': bgtex,
                },
            )
        )

        self._update_timer = bs.Timer(0.1, self._update, repeat=True)
        self._update()

        # Hopefully this won't hitch but lets space these out anyway.
        bs.add_clean_frame_callback(bs.WeakCall(self._start_preloads))

        random.seed()

        # Need to update this for toolbar mode; currenly doesn't fit.
        # if bool(False):
        #     if not (env.demo or env.arcade):
        #         self._news = NewsDisplay(self)

        self._attract_mode_timer = bs.Timer(
            3.12, self._update_attract_mode, repeat=True
        )

        app.classic.invoke_main_menu_ui()

    def _update(self) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        app = bs.app
        assert app.classic is not None

        # Update logo in case it changes.
        if self._logo_node:
            custom_texture = self._get_custom_logo_tex_name()
            if custom_texture != self._custom_logo_tex_name:
                self._custom_logo_tex_name = custom_texture
                self._logo_node.texture = bs.gettexture(
                    custom_texture if custom_texture is not None else 'logo'
                )
                self._logo_node.mesh_opaque = (
                    None if custom_texture is not None else None
                )
                self._logo_node.mesh_transparent = (
                    None
                    if custom_texture is not None
                    else None
                )

        # If language has changed, recreate our logo text/graphics.
        lang = app.lang.language
        if lang != self._language:
            self._language = lang
            y = 20
            base_scale = 1.1
            self._word_actors = []
            base_delay = 0.8
            delay = base_delay
            delay_inc = 0.02

            # Come on faster after the first time.
            if self._did_initial_transition:
                base_delay = 0.0
                delay = base_delay
                delay_inc = 0.02

            base_x = -170
            x = base_x - 20
            spacing = 55 * base_scale
            y_extra = 0
            xv1 = x
            delay1 = delay
            for shadow in (True, False):
                x = xv1
                delay = delay1
                self._make_word(
                    'B',
                    x - 50,
                    y - 23 + 0.8 * y_extra,
                    scale=1.3 * base_scale,
                    delay=delay,
                    vr_depth_offset=3,
                    shadow=shadow,
                )
                x += spacing
                delay += delay_inc
                self._make_word(
                    'm',
                    x,
                    y + y_extra,
                    delay=delay,
                    scale=base_scale,
                    shadow=shadow,
                )
                x += spacing * 1.25
                delay += delay_inc
                self._make_word(
                    'b',
                    x,
                    y + y_extra - 10,
                    delay=delay,
                    scale=1.1 * base_scale,
                    vr_depth_offset=5,
                    shadow=shadow,
                )
                x += spacing * 0.85
                delay += delay_inc
                self._make_word(
                    'S',
                    x,
                    y - 25 + 0.8 * y_extra,
                    scale=1.35 * base_scale,
                    delay=delay,
                    vr_depth_offset=14,
                    shadow=shadow,
                )
                x += spacing
                delay += delay_inc
                self._make_word(
                    'q',
                    x,
                    y + y_extra,
                    delay=delay,
                    scale=base_scale,
                    shadow=shadow,
                )
                x += spacing * 0.9
                delay += delay_inc
                self._make_word(
                    'u',
                    x,
                    y + y_extra,
                    delay=delay,
                    scale=base_scale,
                    vr_depth_offset=7,
                    shadow=shadow,
                )
                x += spacing * 0.9
                delay += delay_inc
                self._make_word(
                    'd',
                    x,
                    y + y_extra,
                    delay=delay,
                    scale=base_scale,
                    shadow=shadow,
                )
                x += spacing * 0.64
                delay += delay_inc
                self._make_word(
                    'a',
                    x,
                    y + y_extra - 10,
                    delay=delay,
                    scale=1.1 * base_scale,
                    vr_depth_offset=6,
                    shadow=shadow,
                )
            self._make_logo(
                base_x - 28,
                125 + y + 1.2 * y_extra,
                0.32 * base_scale,
                delay=base_delay,
            )

    def _make_word(
        self,
        word: str,
        x: float,
        y: float,
        *,
        scale: float = 1.0,
        delay: float = 0.0,
        vr_depth_offset: float = 0.0,
        shadow: bool = False,
    ) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        if shadow:
            word_obj = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'position': (x, y),
                        'big': True,
                        'color': (0.0, 0.0, 0.2, 0.08),
                        'tilt_translate': 0.09,
                        'opacity_scales_shadow': False,
                        'shadow': 0.2,
                        'vr_depth': -130,
                        'v_align': 'center',
                        'project_scale': 0.97 * scale,
                        'scale': 1.0,
                        'text': word,
                    },
                )
            )
            self._word_actors.append(word_obj)
        else:
            word_obj = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'position': (x, y),
                        'big': True,
                        'color': (1.2, 1.15, 1.15, 1.0),
                        'tilt_translate': 0.11,
                        'shadow': 0.2,
                        'vr_depth': -40 + vr_depth_offset,
                        'v_align': 'center',
                        'project_scale': scale,
                        'scale': 1.0,
                        'text': word,
                    },
                )
            )
            self._word_actors.append(word_obj)

        # Add a bit of stop-motion-y jitter to the logo (unless we're in
        # VR mode in which case its best to leave things still).
        if not bs.app.env.vr:
            cmb: bs.Node | None
            cmb2: bs.Node | None
            if not shadow:
                cmb = bs.newnode(
                    'combine', owner=word_obj.node, attrs={'size': 2}
                )
            else:
                cmb = None
            if shadow:
                cmb2 = bs.newnode(
                    'combine', owner=word_obj.node, attrs={'size': 2}
                )
            else:
                cmb2 = None
            if not shadow:
                assert cmb and word_obj.node
                cmb.connectattr('output', word_obj.node, 'position')
            if shadow:
                assert cmb2 and word_obj.node
                cmb2.connectattr('output', word_obj.node, 'position')
            keys = {}
            keys2 = {}
            time_v = 0.0
            for _i in range(10):
                val = x + (random.random() - 0.5) * 0.8
                val2 = x + (random.random() - 0.5) * 0.8
                keys[time_v * self._ts] = val
                keys2[time_v * self._ts] = val2 + 5
                time_v += random.random() * 0.1
            if cmb is not None:
                bs.animate(cmb, 'input0', keys, loop=True)
            if cmb2 is not None:
                bs.animate(cmb2, 'input0', keys2, loop=True)
            keys = {}
            keys2 = {}
            time_v = 0
            for _i in range(10):
                val = y + (random.random() - 0.5) * 0.8
                val2 = y + (random.random() - 0.5) * 0.8
                keys[time_v * self._ts] = val
                keys2[time_v * self._ts] = val2 - 9
                time_v += random.random() * 0.1
            if cmb is not None:
                bs.animate(cmb, 'input1', keys, loop=True)
            if cmb2 is not None:
                bs.animate(cmb2, 'input1', keys2, loop=True)

        if not shadow:
            assert word_obj.node
            bs.animate(
                word_obj.node,
                'project_scale',
                {delay: 0.0, delay + 0.1: scale * 1.1, delay + 0.2: scale},
            )
        else:
            assert word_obj.node
            bs.animate(
                word_obj.node,
                'project_scale',
                {delay: 0.0, delay + 0.1: scale * 1.1, delay + 0.2: scale},
            )

    def _get_custom_logo_tex_name(self) -> str | None:
        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_misc_read_val('easter', False):
            return 'logoEaster'
        return None

    # Pop the logo and menu in.
    def _make_logo(
        self,
        x: float,
        y: float,
        scale: float,
        delay: float,
        *,
        custom_texture: str | None = None,
        jitter_scale: float = 1.0,
        rotate: float = 0.0,
        vr_depth_offset: float = 0.0,
    ) -> None:
        # pylint: disable=too-many-locals
        if custom_texture is None:
            custom_texture = self._get_custom_logo_tex_name()
        self._custom_logo_tex_name = custom_texture
        ltex = bs.gettexture(
            custom_texture if custom_texture is not None else 'logo'
        )
        mopaque = None if custom_texture is not None else None
        mtrans = (
            None
            if custom_texture is not None
            else None
        )
        logo_attrs = {
            'position': (x, y),
            'texture': ltex,
            'mesh_opaque': mopaque,
            'mesh_transparent': mtrans,
            'vr_depth': -10 + vr_depth_offset,
            'rotate': rotate,
            'attach': 'center',
            'tilt_translate': 0.21,
            'absolute_scale': True,
        }
        if custom_texture is None:
            logo_attrs['scale'] = (2000.0, 2000.0)
        logo = bs.NodeActor(bs.newnode('image', attrs=logo_attrs))
        self._logo_node = logo.node
        self._word_actors.append(logo)

        # Add a bit of stop-motion-y jitter to the logo (unless we're in
        # VR mode in which case its best to leave things still).
        assert logo.node

        def jitter() -> None:
            if not bs.app.env.vr:
                cmb = bs.newnode('combine', owner=logo.node, attrs={'size': 2})
                cmb.connectattr('output', logo.node, 'position')
                keys = {}
                time_v = 0.0

                # Gen some random keys for that stop-motion-y look
                for _i in range(10):
                    keys[time_v] = (
                        x + (random.random() - 0.5) * 0.7 * jitter_scale
                    )
                    time_v += random.random() * 0.1
                bs.animate(cmb, 'input0', keys, loop=True)
                keys = {}
                time_v = 0.0
                for _i in range(10):
                    keys[time_v * self._ts] = (
                        y + (random.random() - 0.5) * 0.7 * jitter_scale
                    )
                    time_v += random.random() * 0.1
                bs.animate(cmb, 'input1', keys, loop=True)

        # Do a fun spinny animation on the logo the first time in.
        if (
            custom_texture is None
            and bs.app.classic is not None
            and not self._did_initial_transition
        ):
            jitter()
            cmb = bs.newnode('combine', owner=logo.node, attrs={'size': 2})

            delay = 0.0
            keys = {
                delay: 5000.0 * scale,
                delay + 0.4: 530.0 * scale,
                delay + 0.45: 620.0 * scale,
                delay + 0.5: 590.0 * scale,
                delay + 0.55: 605.0 * scale,
                delay + 0.6: 600.0 * scale,
            }
            bs.animate(cmb, 'input0', keys)
            bs.animate(cmb, 'input1', keys)
            cmb.connectattr('output', logo.node, 'scale')

            keys = {
                delay: 100.0,
                delay + 0.4: 370.0,
                delay + 0.45: 357.0,
                delay + 0.5: 360.0,
            }
            bs.animate(logo.node, 'rotate', keys)
            type(self)._did_initial_transition = True
        else:
            # For all other cases do a simple scale up animation.
            jitter()
            cmb = bs.newnode('combine', owner=logo.node, attrs={'size': 2})

            keys = {
                delay: 0.0,
                delay + 0.1: 700.0 * scale,
                delay + 0.2: 600.0 * scale,
            }
            bs.animate(cmb, 'input0', keys)
            bs.animate(cmb, 'input1', keys)
            cmb.connectattr('output', logo.node, 'scale')
            
    import bascenev1 as bs

    def play_lyrics(self):
        """Plays a timed sequence of lyrics onscreen."""

        # Define lyrics as (text, delay_in_seconds)
        lyrics = [
            ("PAPA CERDITO", 2.5),
            ("VS", 1.5),
            ("BEBE GEORGE", 1.3),
            ("QUE LA BATALLA COMENCE", 1.5),
            ("Bebé George te estás pasando de la raya", 2.0),
            ("No eres rapero así que vámonos a casa", 2.2),
            ("Cada día estás peor educado", 2.5),
            ("La culpa es de tu madre por haberte malcriado", 2.3),
            ("Quieres competir conmigo y me das risa", 2.2),
            ("No sabes que en la experiencia no se improvisa", 2.1),
            ("No me vas a ganar lo siento", 2.5),
            ("Soy el mejor rapero de todos los tiempos", 2.2),
            ("¿Crees que puedes ganar? Me das risa", 2.3),
            ("No pudiste ganarle ni a Peppa tu hermanita", 2.1),
            ("Cometiste un error queriendo batallar", 2.4),
            ("Soy tu padre y llevo tipo haciendo rap", 2.0),
            ("Nunca he perdido una batalla", 2.3),
            ("Tú tienes varias batallas y cero ganadas", 2.0),
            ("Así que bebé George guárdame respeto", 2.7),
            ("Soy tu padre y te recuerdo que yo te mantengo", 2.0),
            ("A las batallas de rap llegaste tarde", 3.0),
            ("Sigo en victo no me importa quien venga a enfrentarme", 2.2),
            ("Ya seas tú, Peppa o mi madre", 2.2),
            ("Siempre es lo mismo voy a derrotarles", 2.2),
            ("Le ganó a Peppa y a cualquiera que me enfrente", 2.2),
            ("Tengo más talento y eso es evidente ", 2.2),
            ("Una batalla más y voy a ganarte", 2.2),
            ("Ya soy grande mira no uso pañales", 2.2),
            ("Tú me mantienes y tienes razón", 2.2),
            ("Pero piénsalo un segundo, es tu obligación", 2.2),
            ("Eres viejo y no tienes experiencia", 2.2),
            ("Porque tus neuronas parecen que están muertas", 2.1),
            ("Tienes el cráneo hueco", 2.2),
            ("Te olvidaron en la repartición de cerebro", 2.2),
            ("Préstame atención señor barriga", 2.2),
            ("En esta batalla te di una paliza", 2.2),
        ]

        start_time = 0.0
        fade_time = 2.0

        for text, delay in lyrics:
            # For each lyric, create a timer with cumulative time
            start_time += delay

            def make_text_fn(t=text):
                try:
                    # Create and show the lyric
                    node = bs.newnode(
                        'text',
                        attrs={
                            'text': t,
                            'position': (0, -50),
                            'scale': 1.2,
                            'color': (1, 1, 1),
                            'h_align': 'center',
                            'v_attach': 'center',
                        },
                    )

                    # Fade out smoothly
                    bs.animate(node, 'opacity', {0.0: 1.0, fade_time: 0.0})
                    bs.timer(fade_time + 0.2, node.delete)

                except Exception as e:
                    print(f"Lyrics error: {e}")

            # Schedule it
            bs.timer(start_time, make_text_fn)

    def _start_preloads(self) -> None:
        # FIXME: The func that calls us back doesn't save/restore state
        #  or check for a dead activity so we have to do that ourself.
        if self.expired:
            return
        with self.context:
            _preload1()

        def _start_menu_music() -> None:
            assert bs.app.classic is not None
            music_choices = [
                bs.MusicType.MENU,
                bs.MusicType.MENU2,
                bs.MusicType.MENU6,
                bs.MusicType.MENU7,
                bs.MusicType.MENU8,
                bs.MusicType.MENU9,
                bs.MusicType.MENU10,
                bs.MusicType.MENU11,
                bs.MusicType.MENU12,
                bs.MusicType.MENU,
                bs.MusicType.MENU2,
                bs.MusicType.MENU6,
                bs.MusicType.MENU7,
                bs.MusicType.MENU8,
                bs.MusicType.MENU9,
                bs.MusicType.MENU10,
                bs.MusicType.MENU11,
                bs.MusicType.MENU12,
                bs.MusicType.MENU67
            ]
            self.chosen_music = random.choice(music_choices)
            bs.setmusic(self.chosen_music)
            if self.chosen_music == bs.MusicType.MENU12:
                self.play_lyrics()
                bs.timer(101.0, self.play_lyrics, repeat=True)

        bui.apptimer(0.1, _start_menu_music)        

    def _update_attract_mode(self) -> None:
        if bui.app.classic is None:
            return
            
        if bui.get_input_idle_time() < 0.3:
            if self.cutscene_player:
                self.cutscene_player.stop()
                self.cutscene_player = None
                bs.getsound('swish').play()
                bs.setmusic(self.chosen_music)
                self.startdemotimer = None
                self.startmusictimer = None
                bui.app.config['timesattracted'] = 1
                self.canstartdemo = True

        if not bui.app.config.resolve('Show Demos When Idle'):
            return

        if self.canstartdemo == False:
            return
        
        threshold = 20.0
        
        # If we're idle *and* have been in this activity for that long,
        # flip over to our cpu demo.
        if bui.get_input_idle_time() > threshold and bs.time() > threshold:
            if ba.app.config.get("timesattracted") == 3:
                self.cutscene_player = CutscenePlayer(
                    cutscene_id=1,
                    frame_delays=[3.0, 3.0, 2.0, 15.0, 3.0, 3.0],
                    fade_duration=2.0
                )
                bs.setmusic(bs.MusicType.CUTSCENE1)
                self.canstartdemo = False
                bui.app.config['timesattracted'] = 1
                def setstartdemo():
                    self.canstartdemo = True
                def setchosenmusic():
                    bs.setmusic(self.chosen_music)
                self.startmusictimer = bs.Timer(30.0, setchosenmusic)
                self.startdemotimer = bs.Timer(56.0, setstartdemo)
            else:
                bui.app.classic.run_stress_test(
                    playlist_type='Random',
                    playlist_name='__default__',
                    player_count=8,
                    round_duration=75,
                    attract_mode=True,
                )
                if not ba.app.config.get("isplayingmusic", True):
                    bs.localsetmusic(bs.MusicType.OPENING)
                bui.app.config['timesattracted'] += 1


class NewsDisplay:
    """Wrangles news display."""

    def __init__(self, activity: bs.Activity):
        self._valid = True
        self._message_duration = 10.0
        self._message_spacing = 2.0
        self._text: bs.NodeActor | None = None
        self._activity = weakref.ref(activity)
        self._phrases: list[str] = []
        self._used_phrases: list[str] = []
        self._phrase_change_timer: bs.Timer | None = None

        # If we're signed in, fetch news immediately. Otherwise wait
        # until we are signed in.
        self._fetch_timer: bs.Timer | None = bs.Timer(
            1.0, bs.WeakCall(self._try_fetching_news), repeat=True
        )
        self._try_fetching_news()

    # We now want to wait until we're signed in before fetching news.
    def _try_fetching_news(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() == 'signed_in':
            self._fetch_news()
            self._fetch_timer = None

    def _fetch_news(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        assert bs.app.classic is not None
        bs.app.classic.main_menu_last_news_fetch_time = time.time()

        # UPDATE - We now just pull news from MRVs.
        news = plus.get_v1_account_misc_read_val('n', None)
        if news is not None:
            self._got_news(news)

    def _change_phrase(self) -> None:
        from bascenev1lib.actor.text import Text

        app = bs.app
        assert app.classic is not None

        # If our news is way out of date, lets re-request it; otherwise,
        # rotate our phrase.
        assert app.classic.main_menu_last_news_fetch_time is not None
        if time.time() - app.classic.main_menu_last_news_fetch_time > 600.0:
            self._fetch_news()
            self._text = None
        else:
            if self._text is not None:
                if not self._phrases:
                    for phr in self._used_phrases:
                        self._phrases.insert(0, phr)
                val = self._phrases.pop()
                if val == '__ACH__':
                    vrmode = app.env.vr
                    Text(
                        bs.Lstr(resource='nextAchievementsText'),
                        color=((1, 1, 1, 1) if vrmode else (0.95, 0.9, 1, 0.4)),
                        host_only=True,
                        maxwidth=200,
                        position=(-300, -35),
                        h_align=Text.HAlign.RIGHT,
                        transition=Text.Transition.FADE_IN,
                        scale=0.9 if vrmode else 0.7,
                        flatness=1.0 if vrmode else 0.6,
                        shadow=1.0 if vrmode else 0.5,
                        h_attach=Text.HAttach.CENTER,
                        v_attach=Text.VAttach.TOP,
                        transition_delay=1.0,
                        transition_out_delay=self._message_duration,
                    ).autoretain()
                    achs = [
                        a
                        for a in app.classic.ach.achievements
                        if not a.complete
                    ]
                    if achs:
                        ach = achs.pop(random.randrange(min(4, len(achs))))
                        ach.create_display(
                            -180,
                            -35,
                            1.0,
                            outdelay=self._message_duration,
                            style='news',
                        )
                    if achs:
                        ach = achs.pop(random.randrange(min(8, len(achs))))
                        ach.create_display(
                            180,
                            -35,
                            1.25,
                            outdelay=self._message_duration,
                            style='news',
                        )
                else:
                    spc = self._message_spacing
                    keys = {
                        spc: 0.0,
                        spc + 1.0: 1.0,
                        spc + self._message_duration - 1.0: 1.0,
                        spc + self._message_duration: 0.0,
                    }
                    assert self._text.node
                    bs.animate(self._text.node, 'opacity', keys)
                    # {k: v
                    #  for k, v in list(keys.items())})
                    self._text.node.text = val

    def _got_news(self, news: str) -> None:
        # Run this stuff in the context of our activity since we need to
        # make nodes and stuff.. should fix the serverget call so it.
        activity = self._activity()
        if activity is None or activity.expired:
            return
        with activity.context:
            self._phrases.clear()

            # Show upcoming achievements in non-vr versions (currently
            # too hard to read in vr).
            self._used_phrases = (['__ACH__'] if not bs.app.env.vr else []) + [
                s for s in news.split('<br>\n') if s != ''
            ]
            self._phrase_change_timer = bs.Timer(
                (self._message_duration + self._message_spacing),
                bs.WeakCall(self._change_phrase),
                repeat=True,
            )

            assert bs.app.classic is not None
            scl = (
                1.2
                if (bs.app.ui_v1.uiscale is bs.UIScale.SMALL or bs.app.env.vr)
                else 0.8
            )

            color2 = (1, 1, 1, 1) if bs.app.env.vr else (0.7, 0.65, 0.75, 1.0)
            shadow = 1.0 if bs.app.env.vr else 0.4
            self._text = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'v_attach': 'top',
                        'h_attach': 'center',
                        'h_align': 'center',
                        'vr_depth': -20,
                        'shadow': shadow,
                        'flatness': 0.8,
                        'v_align': 'top',
                        'color': color2,
                        'scale': scl,
                        'maxwidth': 900.0 / scl,
                        'position': (0, -10),
                    },
                )
            )
            self._change_phrase()


def _preload1() -> None:
    """Pre-load some assets a second or two into the main menu.

    Helps avoid hitches later on.
    """
    for mname in [
        'plasticEyesTransparent',
        'playerLineup1Transparent',
        'playerLineup2Transparent',
        'playerLineup3Transparent',
        'playerLineup4Transparent',
        'angryComputerTransparent',
        'scrollWidgetShort',
        'windowBGBlotch',
    ]:
        bs.getmesh(mname)
    for tname in ['playerLineup', 'lock']:
        bs.gettexture(tname)
    for tex in [
        'iconRunaround',
        'iconOnslaught',
        'medalComplete',
        'medalBronze',
        'medalSilver',
        'medalGold',
        'characterIconMask',
    ]:
        bs.gettexture(tex)
    bs.gettexture('bg')
    from bascenev1lib.actor.powerupbox import PowerupBoxFactory

    PowerupBoxFactory.get()
    bui.apptimer(0.1, _preload2)


def _preload2() -> None:
    # FIXME: Could integrate these loads with the classes that use them
    #  so they don't have to redundantly call the load
    #  (even if the actual result is cached).
    for mname in ['powerup', 'powerupSimple']:
        bs.getmesh(mname)
    for tname in [
        'powerupBomb',
        'powerupSpeed',
        'powerupPunch',
        'powerupIceBombs',
        'powerupStickyBombs',
        'powerupShield',
        'powerupImpactBombs',
        'powerupHealth',
    ]:
        bs.gettexture(tname)
    for sname in [
        'powerup01',
        'boxDrop',
        'boxingBell',
        'scoreHit01',
        'scoreHit02',
        'dripity',
        'spawn',
        'gong',
    ]:
        bs.getsound(sname)
    from bascenev1lib.actor.bomb import BombFactory

    BombFactory.get()
    bui.apptimer(0.1, _preload3)


def _preload3() -> None:
    from bascenev1lib.actor.spazfactory import SpazFactory

    for mname in ['bomb', 'bombSticky', 'impactBomb']:
        bs.getmesh(mname)
    for tname in [
        'bombColor',
        'bombColorIce',
        'bombStickyColor',
        'impactBombColor',
        'impactBombColorLit',
    ]:
        bs.gettexture(tname)
    for sname in ['freeze', 'fuse01', 'activateBeep', 'warnBeep']:
        bs.getsound(sname)
    SpazFactory.get()
    bui.apptimer(0.2, _preload4)


def _preload4() -> None:
    for tname in ['bar', 'meter', 'null', 'flagColor', 'achievementOutline']:
        bs.gettexture(tname)
    for mname in ['frameInset', 'meterTransparent', 'achievementOutline']:
        bs.getmesh(mname)
    for sname in ['metalHit', 'metalSkid', 'refWhistle', 'achievement']:
        bs.getsound(sname)
    from bascenev1lib.actor.flag import FlagFactory

    FlagFactory.get()


class MainMenuSession(bs.Session):
    """Session that runs the main menu environment."""

    def __init__(self) -> None:
        # Gather dependencies we'll need (just our activity).
        self._activity_deps = bs.DependencySet(bs.Dependency(MainMenuActivity))

        super().__init__([self._activity_deps])
        self._locked = False
        if ba.app.config.get("playersfirsttime", True):
            self.setactivity(bs.newactivity(SURVEYActivity))
        else:
            self.setactivity(bs.newactivity(MainMenuActivity))

    @override
    def on_activity_end(self, activity: bs.Activity, results: Any) -> None:
        if self._locked:
            bui.unlock_all_input()

        # Any ending activity leads us into the main menu one.
        self.setactivity(bs.newactivity(MainMenuActivity))

    @override
    def on_player_request(self, player: bs.SessionPlayer) -> bool:
        # Reject all player requests.
        return False