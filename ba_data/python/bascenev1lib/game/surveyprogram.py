"""Script that contains a setup for first time players."""
# FIVE HUNDRED FUCKING WEAKCALLS OH MY GOD IM GONN A DIE
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Sequence, override, cast
import bascenev1 as bs
import babase as ba
import bauiv1 as bui
import random
from bascenev1lib.actor.parallax import ParallaxImage
from bascenev1lib.actor.virtual_keyboard import VirtualKeyboard
import mellboii.mell_resources as mell
from mellboii.easing import choppify

SURVEY_CHARS = [
    dict(
        title=bs.Lstr(resource='surveyPrompt1'),
        character="Spaz",
        default_name='Newbie',
        cfg="squda_ch1name",
    ),
    dict(
        title=bs.Lstr(resource='surveyPrompt2'),
        character="Kris",
        default_name='Kris',
        cfg="squda_ch2name",
    ),
    dict(
        title=bs.Lstr(resource='surveyPrompt3'),
        character="GummyBoiYT",
        default_name='Snake Shadow',
        cfg="squda_ch3name",
    ),
    dict(
        title=bs.Lstr(resource='surveyPrompt4'),
        character="Noob",
        default_name='Noob',
        cfg="squda_ch4name",
    ),
]
    
class SurveySessionThing(bs.Session):
    """Literally just start SURVEYActivity"""
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.lobby_autojoin = True
        self.setactivity(bs.newactivity(SURVEYActivity))
        
class SURVEYActivity(bs.Activity[bs.Player, bs.Team]):
    """A nice little activity for 
    first time setup."""
    _stdassets = bs.Dependency(bs.AssetPackage, 'stdassets@1')
    def on_player_join(self, player: bs.Player):
        if self._state == 'waiting_on_player':
            self._floaty_textnode.delete()
            self.make_floaty_text('Okay then, moving on!', callback=self._show_chars)
            
        elif self._state == 'naming':
            if self._keyboard:
                keyboard = self._keyboard
                player.assigninput(bs.InputType.JUMP_PRESS, keyboard.select)
                player.assigninput(bs.InputType.BOMB_PRESS, keyboard.back)
                player.assigninput(bs.InputType.LEFT_RIGHT, keyboard.left_right)
                player.assigninput(bs.InputType.UP_DOWN, keyboard.up_down)
                
        player.assigninput(bs.InputType.PICK_UP_PRESS, self._skip_all)

    def __init__(self, settings: dict):
        super().__init__(settings)
        folder = 'naming_seq'
        self._bg_tex = bs.gettexture(f'{folder}/bg')
        self._subtle_bg_tex = bs.gettexture(f'{folder}/bg2')
        self._big_star_tex = bs.gettexture(f'{folder}/star_big')
        self._med_star_tex = bs.gettexture(f'{folder}/star_med')
        self._small_star_tex = bs.gettexture(f'{folder}/star_small')
        self._stars_fg_tex = bs.gettexture(f'{folder}/stars2')
        self._stars_bg_tex = bs.gettexture(f'{folder}/stars1')
        self._arrow_tex = bs.gettexture(f'mother3/arrow_down')
        self._text_sound = bs.getsound('tap')
        self._char_nodes = {}
        self._character_names = {}
        self._keyboard = None
        self._character_naming_index = 0
        self._skip_text = None
        self._state = 'init'
        self._info_text = None
        self._allow_skip = False
    
    def _skip_all(self):
        if not self._allow_skip:
            return
        bs.getsound('swish').play()
        classic = bs.app.classic
        bs.app.config['squda_playersfirsttime'] = False
        bs.app.config.commit()
        if not self._character_names:
            for dictio in SURVEY_CHARS:
                char = dictio.get('character')
                name = dictio.get('default_name')
                self._character_names[char] = name
        cfg_keys = {
            char_dict['character']: char_dict['cfg']
            for char_dict in SURVEY_CHARS
        }
        for character, name in self._character_names.items():
            cfg_key = cfg_keys.get(character)
            if cfg_key:
                bs.app.config[cfg_key] = name
        
        classic.return_to_main_menu_session_gracefully()

    def _run_text_sequence(
        self,
        texts: Sequence[str | tuple[str, Callable[[], None]]],
        end_callback: Callable[[], None],
        index = 0,
    ) -> None:
        """Show a series of floaty-text lines one after another.

        Each entry in 'texts' can be a plain string, or a
        (text, start_callback) tuple where start_callback is fired
        the moment that line begins showing. Once the last line
        finishes, end_callback is called.
        """
        if index >= len(texts):
            return

        next_callback = (
            bs.WeakCall(
                self._run_text_sequence, 
                index=index + 1, 
                texts=texts,
                end_callback=end_callback,
            )
            if index + 1 < len(texts)
            else end_callback
        )

        text = texts[index]
        if isinstance(text, tuple):
            text, start_callback = text
            start_callback()

        self.make_floaty_text(text, callback=next_callback)

    def _intro_finished(self) -> None:
        if self.players:
            self._show_chars()
        else:
            self._ask_join()

    def on_transition_in(self) -> None:
        bs.setmusic(bs.MusicType.SURVEY)
        scs = self._screen_size = bui.get_virtual_safe_area_size()
        self._state = 'intro'
        self._bg = bs.newnode(
            'image',
            attrs={
                'texture': self._bg_tex,
                'fill_screen': True,
                'color': (0.1, 0.1, 0.5),
            }
        )
        
        self._subtle_bg = bs.newnode(
            'image',
            attrs={
                'texture': self._subtle_bg_tex,
                'scale': scs,
                'opacity': 0.1,
                'color': (0.3, 0.3, 1),
            }
        )
        bs.animate_array(
            self._subtle_bg,
            'scale', 2,
            {
                0: scs,
                2: (scs[0] * 1.2, scs[1] * 1.2),
                4: scs,
            },
            loop=True,
        )
        actor = self._stars_bg = ParallaxImage(
            texture=self._stars_bg_tex,
            position=(0, 0),
            size=scs,
            speed=(-4, 0),
        )
        opa = 0.1
        actor.node1.opacity = opa
        actor.node2.opacity = opa
        actor = self._stars_fg = ParallaxImage(
            texture=self._stars_bg_tex,
            position=(0, 0),
            size=(scs[0] * 1.3, scs[1] * 1.3),
        )
        opa = 0.3
        actor.node1.opacity = opa
        actor.node2.opacity = opa
        self._random_star_timer = bs.Timer(
            0.2,
            bs.WeakCall(self._random_star), 
            repeat=True
        )
        texts = [
            "Oh, hey! Hello there!",
            "Welcome to BombSquda!",
            "Before we start, I'd like you\nto answer some things for me...",
            "First time startup... and also I'd really like you to look at this!",
            "Pretty nice, right? Shame the rest of the game doesn't look as good.",
            (
                "Oh, and if you'd like to just skip ahead, you can just\npress GRAB and i'll try to fill in for you.", 
                bs.WeakCall(self._show_skip_btn)
            ),
            "This wiiiillll skip everything tho. Just letting you know.",
            "No worries tho, you can always redo this typa stuff from\nthe BombSquda settings window on the settings section.",
            "Otherwise, we can just start right now.",
        ]
        bs.timer(5, bs.Call(self._run_text_sequence, texts, bs.WeakCall(self._intro_finished)))
    
    def _ask_join(self):
        if self.players:
            self._show_chars()
            return
        self._state = 'waiting_on_player'
        self.make_floaty_text('Oh, and if you could, just press a button for me?', fadeout=False)
    
    def _show_chars(self):
        scale = 1.5
        size = (128 * scale, 128 * scale)
        x = -300
        y = 90
        def add_node(dic, x):
            nonlocal y, size, scale
            character = dic.get('character')
            character = bs.app.classic.spaz_appearances[character]
            tex = bs.gettexture(character.earthportrait)
            node = bs.newnode(
                'image',
                attrs={
                    'texture': tex,
                    'position': (x, y),
                    'scale': (0, 0),
                }
            )
            bs.animate_array(
                node,
                'scale', 2,
                {
                    0: (0, 0),
                    0.05: (size[0] * 1.3, size[1] * 1.3),
                    0.4: size,
                }
            )
            arrow = bs.newnode(
                'image',
                attrs={
                    'texture': self._arrow_tex,
                    'position': (x, y + 20),
                    'scale': (64 * scale, 32 * scale),
                    'opacity': 0,
                }
            )
            keys = {
                0: (x, y + 140),
                0.5: (x, y + 128),
                1: (x, y + 140),
            }
            keys = choppify(keys, fps=10)
            bs.animate_array(
                arrow,
                'position', 2,
                keys,
                loop=True,
            )
            self._char_nodes[character.name] = [node, arrow]
        
        i = 0.2
        for char_dict in SURVEY_CHARS:
            bs.timer(
                i, 
                bs.Call(
                    add_node, 
                    char_dict, 
                    x
                )
            )
            i += 0.15
            x += size[0] + 10
        i += 0.7
        bs.timer(i, self._start_naming_seq)
    
    def _dont_care(self):
        if not self._keyboard:
            return
        self._keyboard.text = SURVEY_CHARS[
            self._character_naming_index
        ].get('default_name')
        self._keyboard._refresh()
    
    def _update_current_naming_char(self):
        index = self._character_naming_index
        names = list(self._char_nodes.keys())
        name = names[index]
        for i, char_name in enumerate(names):
            _char, arrow = self._char_nodes[char_name]
            arrow.opacity = 1 if i == index else 0
        if self._keyboard:
            self._keyboard.text = self._character_names.get(name, '')
            self._keyboard._refresh()
    
    def previous_char(self):
        index = self._character_naming_index
        name = list(self._char_nodes.keys())[index]
        self._character_names[name] = ''
        if index <= 0:
            return
        self._character_naming_index -= 1
        self._update_current_naming_char()
    
    def next_char(self, text: str):
        if not text.strip():
            bs.screenmessage('Name can\'t be empty!!', color=(1, 0, 0))
            bs.getsound('error').play()
            return
        index = self._character_naming_index
        name = list(self._char_nodes.keys())[index]
        self._character_names[name] = text
        if index >= len(SURVEY_CHARS) - 1:
            self._finished_naming()
            return
        self._character_naming_index += 1
        self._update_current_naming_char()
    
    def _start_naming_seq(self):
        self._state = 'naming'
        self.make_floaty_text('Name these stupid goobers.\n(press ? for a default name)', fadeout=False)
        self._update_current_naming_char()
        rows = [
            "1234567890",
            "qwertyuiop",
            "asdfghjkl.",
            "zxcvbnm:/",
            f"{ba.charstr(ba.SpecialChar.SHIFT)}{ba.charstr(ba.SpecialChar.DELETE)}?_{ba.charstr(ba.SpecialChar.PLAY_BUTTON)}",
        ]
        callbacks = {
            '?': bs.WeakCall(self._dont_care),
        }
        keyboard = self._keyboard = VirtualKeyboard(
            width=900,
            height=260,
            max_length=30,
            rows=rows,
            key_callbacks=callbacks,
            position=(30, -160),
            on_submit=bs.WeakCall(self.next_char),
            on_cancel=bs.WeakCall(self.previous_char),
        )
        
        for player in self.players:
            player.assigninput(bs.InputType.JUMP_PRESS, keyboard.select)
            player.assigninput(bs.InputType.BOMB_PRESS, keyboard.back)
            player.assigninput(bs.InputType.LEFT_RIGHT, keyboard.left_right)
            player.assigninput(bs.InputType.UP_DOWN, keyboard.up_down)
    
    def _finished_naming(self):
        for player in self.players:
            player.resetinput()
            player.assigninput(bs.InputType.PICK_UP_PRESS, self._skip_all)

        if self._keyboard:
            self._keyboard.delete()
            self._keyboard = None

        self._state = 'done_naming'
        self._floaty_textnode.delete()

        for char, arrow in self._char_nodes.values():
            arrow.opacity = 0

        texts = [
            "Okay then!",
            "..before we continue tho...",
        ]
        self._run_text_sequence(texts, self._ask_names_okay)

    def _ask_names_okay(self):
        nodes = []
        self._state = 'checking_names'
        bottom_btn = ba.charstr(ba.SpecialChar.BOTTOM_BUTTON)
        right_btn = ba.charstr(ba.SpecialChar.RIGHT_BUTTON)
        self.make_floaty_text('Are these names okay?', fadeout=False)
        for i in list(self._char_nodes.keys()):
            char, arrow = self._char_nodes[i]
            pos = char.position
            names = self._character_names
            node = bs.newnode(
                'text',
                attrs={
                    'text': names[i],
                    'h_align': 'center',
                    'position': (pos[0], pos[1] - 140),
                    'shadow': 0.8,
                    'flatness': 0.6,
                }
            )
            bs.animate(
                node,
                'opacity',
                {
                    0: 0,
                    0.7: 1,
                }
            )
            nodes.append(node)
        self._info_text = bs.newnode(
            'text',
            attrs={
                'text': f'{bottom_btn} - YES\n{right_btn} - NO',
                'h_align': 'center',
                'position': (0, 60),
                'shadow': 0.8,
                'flatness': 0.6,
                'v_attach': 'bottom',
                'v_align': 'bottom',
                'scale': 1.3,
            }
        )
        bs.animate(
            self._info_text,
            'opacity',
            {
                0: 0,
                1: 1,
            }
        )
        def no():
            self._info_text.delete()
            self._floaty_textnode.delete()
            for node in nodes[:]:
                if node:
                    node.delete()
            for player in self.players:
                player.resetinput()
            self._start_naming_seq()
        def yes():
            self._info_text.delete()
            self._floaty_textnode.delete()
            for node in nodes[:]:
                if node:
                    node.delete()
            for player in self.players:
                player.resetinput()
            self._start_settings_section()
        for player in self.players:
            player.assigninput(bs.InputType.BOMB_PRESS, no)
            player.assigninput(bs.InputType.JUMP_PRESS, yes)
    
    def _start_settings_section(self):
        for char, arrow in self._char_nodes.values():
            arrow.delete()
            bs.animate(
                char,
                'opacity',
                {
                    0: 1,
                    0.7: 0,
                }
            )
            bs.timer(0.7, char.delete)

        texts = [
            "Nice, all's okay then.",
            "Now, time to setup the settings.",
            "This will bring up an UI, so you can get your\nmouse out for this one.",
        ]
        self._run_text_sequence(texts, self._show_settings_ui)
    
    def _show_settings_ui(self):
        from bauiv1lib.settings.melsection import MelWindow
        with ba.ContextRef.empty():
            ui = ba.app.ui_v1
            window = MelWindow(
                first_time=True,
                transition='in_scale',
            )
            ui.set_main_window(
                window,
                from_window=False,
                suppress_warning=True,
                is_top_level=True,
            )
        
    def _show_skip_btn(self):
        self._allow_skip = True
        top_btn = ba.charstr(ba.SpecialChar.TOP_BUTTON)
        self._skip_text = bs.newnode(
            'text',
            attrs={
                'text': f'{top_btn} - SKIP',
                'h_align': 'right',
                'position': (-10, 10),
                'shadow': 0.8,
                'flatness': 0.6,
                'v_attach': 'bottom',
                'h_attach': 'right',
            }
        )
        bs.animate(
            self._skip_text,
            'opacity',
            {
                0: 0,
                1: 1,
            }
        )
    
    def _settings_done(self):
        cfg_keys = {
            char_dict['character']: char_dict['cfg']
            for char_dict in SURVEY_CHARS
        }
        for character, name in self._character_names.items():
            cfg_key = cfg_keys.get(character)
            if cfg_key:
                bs.app.config[cfg_key] = name
        bs.app.config['squda_playersfirsttime'] = False
        bs.app.config.commit()

        texts = [
            "Alright, settings are in motion now. All of them,\nso even restarting now should be fine.",
            "You should probably see that by now...",
            "..if you turned on CERTAIN settings. Yup.",
            "Alright, there ya go. First time setup's done",
            "Of course, I didn't do an outro yet, so for\nnow I'll be dropping you in the main menu.",
            "See ya... In the BombSquda!!!!"
        ]
        classic = ba.app.classic
        self._run_text_sequence(texts, classic.return_to_main_menu_session_gracefully)
    
    def make_floaty_text(
        self, 
        text: str, 
        callback: Callable | None = None,
        position: tuple[float, float] = (0, 300),
        fadeout: bool = True,
    ):
        full_text = text
        current_text = ''
        sound = self._text_sound
        text_index = 0
        self._floaty_textnode = textnode = bs.newnode(
            'text',
            attrs={
                'text': current_text,
                'h_align': 'center',
                'position': position,
                'scale': 1.2,
                'shadow': 0.8,
                'flatness': 0.6,
            }
        )
        num1 = -0.2
        num2 = 0.2
        def anim():
            nonlocal textnode
            # copy pasted this one from 
            # REDACTED THING THAT I SHALL NOT DISCUSS
            # BEFORE ITS RELEASE
            # look i made the code for it im allowed to okay 3:<
            ymax = 5
            sub_x, sub_y = textnode.position
            bs.animate_array(
                textnode,
                'position', 2,
                {
                    0.00: (sub_x, sub_y),
                    0.35: (sub_x, sub_y + ymax * 0.60),
                    0.55: (sub_x, sub_y + ymax * 0.90),
                    0.70: (sub_x, sub_y + ymax),
                    0.85: (sub_x, sub_y + ymax * 0.95),
                    1.40: (sub_x, sub_y),

                    1.95: (sub_x, sub_y - ymax * 0.95),
                    2.10: (sub_x, sub_y - ymax),
                    2.25: (sub_x, sub_y - ymax * 0.90),
                    2.45: (sub_x, sub_y - ymax * 0.60),
                    2.80: (sub_x, sub_y),
                },
                loop=True,
            )
        anim()
        def fade_out():
            nonlocal fadeout, textnode
            if not fadeout or not textnode:
                return
            def deleteit():
                if callback and textnode:
                    callback()
                textnode.delete()
            bs.animate(textnode, 'opacity', {0: 1, 1: 0})
            bs.timer(1, deleteit)
            
        def _type_tick():
            nonlocal text_index, current_text, textnode, sound
            if not textnode:
                self._floaty_text_timer = None
                return
            if text_index >= len(full_text):
                self._floaty_text_timer = None
                bs.timer(1.3, fade_out)
                return
            sound.play()
            char = full_text[text_index]
            text_index += 1
            current_text += char
            textnode.text = current_text
        self._floaty_text_timer = bs.Timer(0.03, _type_tick, repeat=True)
    
    def _random_star(self):
        if random.random() > 0.8:
            return
        config = [
            (self._big_star_tex, 0.4),
            (self._med_star_tex, 0.35),
            (self._small_star_tex, 0.3),
        ]
        texture, scale = random.choice(config)
        position = (
            random.uniform(100, 1000),
            self._screen_size[1],
        )
        position_to = (
            random.uniform(-1000, 140),
            -self._screen_size[1],
        )
        node = bs.newnode(
            'image',
            attrs={
                'texture': texture,
                'scale': (128 * scale, 128 * scale),
                'opacity': 0.9,
                'position': position,
            }
        )
        endtime = random.uniform(1.7, 6)
        rotatetime = random.uniform(0.5, 1.7)
        bs.animate(
            node,
            'rotate',
            {
                0: 0,
                rotatetime: 360,
            },
            loop=True,
        )
        bs.animate_array(
            node,
            'position', 2,
            {
                0: position,
                endtime: position_to,
            },
        )
        bs.timer(endtime, node.delete)
