# Released under the MIT License. See LICENSE for details.
#
"""
don't use this one.
"""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1 as bs
import babase
import random
import time
import bauiv1 as bui

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard

if TYPE_CHECKING:
    from typing import Any, Sequence


class Player(bs.Player['Team']):
    """Our player type for this game."""
    
class LoopingBackground:
    """
    Makes a pretty simple
    scrolling looped background.
    Use this if yours isn't animated
    or if you want something simpler to use.
    """
    def __init__(self, texture_name: str = 'scrollingBG'):
        self.scroll_speed = 2.0  # pixels per tick

        tex = bs.gettexture(texture_name)
        self.images = [
            bs.newnode('image', attrs={
                'texture': tex,
                'absolute_scale': True,
                'position': (0, 0),
                'scale': (1290, 720),
            }),
            bs.newnode('image', attrs={
                'texture': tex,
                'absolute_scale': True,
                'position': (1290, 0),  # second copy just off-screen
                'scale': (1290, 720),
            })
        ]

        bs.timer(0.016, self._update, repeat=True)

    def _update(self):
        """Move images left, wrap when offscreen."""
        for img in self.images:
            if not img:
                return
            x, y = img.position
            x -= self.scroll_speed
            if x <= -1280:  # completely offscreen, reset to right side
                x += 1280 * 2
            img.position = (x, y)
    
class LoopingImageAnimation:
    """
    Makes looping animated images.
    You'd never have guessed.
    """
    def __init__(
        self,
        prefix: str = "animframe",  # example: animframe1, animframe2, ...
        frame_count: int = 12, # how many frames
        frame_delay: float = 0.1,   # seconds between frames
        scale: tuple = (300, 300), # size
        position: tuple = (0, 0), # pos
        loop: bool = True, # if we should loop
        fill_screen: bool = False # full screen?
    ):
        self.prefix = prefix
        self.frame_count = frame_count
        self.frame_delay = frame_delay
        self.loop = loop
        self._current_frame = 1

        # Create the image node.
        self.node = bs.newnode(
            "image",
            attrs={
                "texture": bs.gettexture(f"{self.prefix}{self._current_frame}"),
                "absolute_scale": True,
                "scale": scale,
                "position": position,
                "fill_screen": fill_screen,
                "opacity": 1.0,
            },
        )

        # Start the animation timer.
        self._timer = bs.Timer(frame_delay, self._next_frame, repeat=True)

    def _next_frame(self):
        """Advance to the next frame."""
        if not self.node:
            return

        self._current_frame += 1

        # Wrap around if looping.
        if self._current_frame > self.frame_count:
            if self.loop:
                self._current_frame = 1
            else:
                # Stop animation if not looping.
                self._timer = None
                return

        tex_name = f"{self.prefix}{self._current_frame}"
        try:
            self.node.texture = bs.gettexture(tex_name)
        except Exception:
            print(f"[LoopingImageAnimation] Missing texture: {tex_name}")
class TypewriterText:
    def __init__(self, text: str, position=(0, 0), delay: float = 0.05, color=(1, 1, 1), scale: float = 1.0):
        """
        Display text letter by letter.
        :param text: The full text to display
        :param position: (x, y) position
        :param delay: Time between letters
        :param color: RGB color tuple
        """
        self.full_text = text
        self.displayed = ""
        self.index = 0
        self.delay = delay
        self.finished = False

        self.node = bs.newnode(
            'text',
            attrs={
                'text': '',
                'position': position,
                'scale': scale,
                'h_align': 'center',
                'v_align': 'center',
                'color': color,
                'shadow': 0.5,
                'flatness': 0.7,
            },
        )

        # Begin ticking
        self._tick()

    def _tick(self):
        if self.index < len(self.full_text):
            try:
                self.displayed += self.full_text[self.index]
                self.node.text = self.displayed
                self.index += 1
                bs.timer(self.delay, self._tick)
            except babase._error.NodeNotFoundError:
                return
        else:
            self.finished = True


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class MaskedManFight(bs.TeamGameActivity[Player, Team]):
    """you're  fighting a mf with a mask. ...that reminds me of a youtuber, yk?"""

    name = 'Battle Against the Masked Man'
    description = 'Fight against the \nMasked Man from \nMOTHER 3 replicated \nin BombSquad.'

    # dont show zooming text
    # it looks incredibly stupid when you 
    # launch the activity lol
    suppress_zoomtext = True

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        assert bs.app.classic is not None
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.default_music = bs.MusicType.STRONGONE
        # Player's variables; PP is magic.
        self.player_hp = 250
        self.player_pp = 75
        # Enemy variables.
        self.enemy_hp = 3500
        self.enemy_name = 'Masked Man'
        # Option we start at.
        self.currentoption = 'Bash'
        # This is for when a action is happening.
        # mainly for whenever you shouldn't be using the menu.
        self.in_action = False
        # Whether you can do rhythmic attacks.
        self.can_chain = False
        # Text for winning or losing
        self.endtext = None
        # Damage text for the enemy or you.
        self.damagetext = None
        # Whether we can start rhythm attacks or not.
        self.cant_chain = False
        # Sound index for instrument attack
        # sounds.
        self.sound_index = 0
        # If the fight ended or not.
        self.ended = False
        # If the enemy already died.
        # Got pretty mad while naming this.
        self.enemyfuckingdied = False
        # What our last option was.
        self.lastoption = None
        # Instrument sound. 
        self.instrumentsound = None
        # Error text.
        self.errortext = None
        # Timer for rhythm attacks.
        self.chain_timer = None
        # How many times we've attacked rhythmically.
        self.timeschained = 0
        # Whether we're on the PSI Menu.
        self.psimenumode = False
        # I dunno. Sorry.
        self.alreadyended = False
        # If player is guarding.
        self.is_guarding = False
        # Dunno. Not referenced anywhere...
        self.currentpsi = None
        # Chosen group of instrument sounds.
        self.chosen_group = None
        # Value important for BombSquda.
        self.ismother3BS = True

    # On begin stuff.
    @override
    def on_begin(self) -> None:
        super().on_begin()
        for player in self.players:
            player.assigninput(bs.InputType.LEFT_PRESS, self.go_left)
            player.assigninput(bs.InputType.RIGHT_PRESS, self.go_right)
            player.assigninput(bs.InputType.JUMP_PRESS, self.select)
            player.assigninput(bs.InputType.PUNCH_PRESS, self.select)
            player.assigninput(bs.InputType.BOMB_PRESS, self.go_back)
            player.assigninput(bs.InputType.UP_DOWN, self.donothing)
            player.assigninput(bs.InputType.LEFT_RIGHT, self.donothing)
        bs.timer(0.2, self.do_ui)
        self.anticutout = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('white2'),
                'absolute_scale': True,
                'position': (0, -300),
                'attach': 'center',
                'opacity': 1.0,
                'fill_screen': True,
                'color': (0, 0, 0)
            }
        )

    def shake_node(self, node: bs.Node, intensity: float = 10.0, duration: float = 1.0, interval: float = 0.02):
        """
        Shake a node.
        Args:
            node: The node to shake (like your image or text).
            intensity: How strong shall we shake.
            duration: How much it shall take before stopping.
            interval: How fast will it go.
        """
        if node is None:
            return

        original_pos = tuple(node.position)
        total_steps = int(duration / interval)
        step = 0

        def _update_shake():
            nonlocal step
            if not node or step >= total_steps:
                # Snap back to original position at the end
                if node:
                    node.position = original_pos
                return

            # Calculate diminishing shake strength (optional)
            progress = step / total_steps
            falloff = 1.0 - progress
            current_intensity = intensity * falloff

            # Random offset around original position
            offset_x = random.uniform(-current_intensity, current_intensity)
            offset_y = random.uniform(-current_intensity, current_intensity)
            node.position = (
                original_pos[0] + offset_x,
                original_pos[1] + offset_y,
            )

            step += 1
            bs.timer(interval, _update_shake)

        _update_shake()
    def hideicons(self):
        """
        Hides menu icons.
        """
        self.guardicon.opacity = 0.0
        self.itemicon.opacity = 0.0
        self.bashicon.opacity = 0.0
        self.psicon.opacity = 0.0
    
    # psi  moves
    def psimove(self):
        """
        Does a magic/PSI 
        move of choice.
        You may add more here.
        """
        if self.in_action:
            return  # ignore if already doing smth
        elif self.currentoption == 'Lifeup' and self.player_pp <= 17:
            if self.errortext:
                self.errortext.node.delete()
            self.errortext = TypewriterText(
                'Not enough PP!',
                position=(0, 300),
                delay=0.01,
                color=(1, 1, 1),
                scale=1.5,
            )
            bs.timer(1.3, self.errortext.node.delete)
            bs.getsound('error').play()
            return
        elif self.currentoption == 'Love' and self.player_pp <= 26:
            if self.errortext:
                self.errortext.node.delete()
            self.errortext = TypewriterText(
                'Not enough PP!',
                position=(0, 300),
                delay=0.01,
                color=(1, 1, 1),
                scale=1.5,
            )
            bs.timer(1.3, self.errortext.node.delete)
            bs.getsound('error').play()
            return
        self.in_action = True
        self.hideicons()
        self.can_chain = False

        name = self.players[0].actor.node.name
        bs.getsound('allypsimove').play()
        self.psypwrtext.text = str(self.player_pp)
        
        self.text = TypewriterText(
            f"{name} tried {self.currentoption}!",
            position=(0, 300),
            delay=0.01,
            color=(1, 1, 1),
            scale=1.5,
        )
        def trylifeup():
            bs.getsound('lifeup').play()
            self.player_hp += 50
            self.ups()
            bs.animate_array(self.earthchar, "position", 2,{
                0.5: (self.meterx, self.metery + 100),
                1.0: (self.meterx, self.metery - 40)
            })
            bs.timer(1.0, self.enemy_turn)
        def trypmag():
            bs.getsound('ppgain').play()
            randnumber = random.randint(1,8)
            self.player_pp += randnumber
            self.ups()
            bs.animate_array(self.earthchar, "position", 2,{
                0.5: (self.meterx, self.metery + 100),
                1.0: (self.meterx, self.metery - 40)
            })
            bs.timer(1.0, self.enemy_turn)
        def trylove():
            bs.getsound('pklove').play()
            bs.animate_array(self.earthchar, "position", 2,{
                0.5: (self.meterx, self.metery + 100),
                1.0: (self.meterx, self.metery - 40)
            })
            self.pkloveanim = LoopingImageAnimation(
                prefix="pklove",
                frame_count=30,
                frame_delay=0.045,
                scale=(1500, 1000),
                position=(10, -15),
                fill_screen=False,
                loop=False
            )
            def damageenemy():
                self.damagenum = random.randint(310,410)
                self.enemy_hp -= self.damagenum
                self.ues()
                self.shake_node(self.enemy, intensity=13.0, duration=0.5)
                bs.getsound('enemybashed').play()
                bs.timer(1.1, self.damagetext.node.delete)
            bs.timer(1.8, damageenemy)
            bs.timer(2.5, self.enemy_turn)
        if self.currentoption == 'Lifeup':
            bs.timer(0.2, lambda: bs.getsound('psiheal').play())
            bs.timer(1.0, trylifeup)
            self.player_pp -= 17
            bs.timer(1.0, self.text.node.delete)
        elif self.currentoption == 'PSI Magnet':
            bs.timer(0.2, lambda: bs.getsound('psimagnet').play())
            bs.timer(1.0, trypmag)
            bs.timer(1.0, self.text.node.delete)
        elif self.currentoption == 'Love':
            bs.timer(0.4, trylove)
            self.player_pp -= 26
            bs.timer(0.4, self.text.node.delete)
        bs.animate_array(self.earthchar, "position", 2,{
            0.0: (self.meterx, self.metery - 40),
            0.5: (self.meterx, self.metery + 100)
        })
        self.ups()
            
    # initiate attack
    def attack(self):
        if self.in_action:
            return  # ignore if already in action
        self.in_action = True
        self.hideicons()
        self.can_chain = False

        name = self.players[0].actor.node.name
        bs.getsound('allyturn').play()

        self.text = TypewriterText(
            f"{name} attacks!",
            position=(0, 300),
            delay=0.01,
            color=(1, 1, 1),
            scale=1.5,
        )
        self.alreadyended = False
        # After short delay, perform actual hit
        bs.timer(1.0, self._perform_attack)
        bs.animate_array(self.earthchar, "position", 2,{
            0.0: (self.meterx, self.metery - 40),
            0.5: (self.meterx, self.metery + 100)
        })
        # set your character's sound groups here
        if self.players[0].actor.character == 'Zoe':
            groups = ['kumatoraA', 'kumatoraB', 'kumatoraC', 'kumatoraD', 'kumatoraE', 'kumatoraF']
            self.chosen_group = random.choice(groups)
            self.sound_index = 0
        elif self.players[0].actor.character == 'Grumbledorf':
            groups = ['salsaA', 'salsaB', 'salsaC', 'salsaD', 'salsaE', 'salsaF']
            self.chosen_group = random.choice(groups)
            self.sound_index = 0
        elif self.players[0].actor.character == 'Snake Shadow':
            groups = ['clausA', 'clausB', 'clausC', 'clausD', 'clausE', 'clausF']
            self.chosen_group = random.choice(groups)
            self.sound_index = 0
        elif self.players[0].actor.character == 'Spaz':
            groups = ['lucasA', 'lucasB', 'lucasC', 'lucasD', 'lucasE', 'lucasF']
            self.chosen_group = random.choice(groups)
            self.sound_index = 0
        elif self.players[0].actor.character == 'John':
            groups = ['flintA', 'flintB', 'flintC', 'flintD', 'flintE', 'flintF']
            self.chosen_group = random.choice(groups)
            self.sound_index = 0
        
    # guard
    def guard(self):
        if self.in_action:
            return  # ignore if already in action
        self.in_action = True
        self.hideicons()
        self.is_guarding = True
        
        name = self.players[0].actor.node.name
        self.text = TypewriterText(
            f"{name} guards.",
            position=(0, 300),
            delay=0.01,
            color=(1, 1, 1),
            scale=1.5,
        )
        bs.timer(1.3, self.text.node.delete)
        bs.timer(1.3, self.enemy_turn)
        bs.animate_array(self.earthchar, "position", 2,{
            0.0: (self.meterx, self.metery - 40),
            0.5: (self.meterx, self.metery + 100),
            1.0: (self.meterx, self.metery + 100),
            1.5: (self.meterx, self.metery - 40)
        })
    # short for "Check for Mortal Damage".
    # Checks if the player died.
    def cfmd(self):
        if self.player_hp <= 0:
            name = self.players[0].actor.node.name
            self.endtext = TypewriterText(
                f"{name} got hurt and collapsed...",
                position=(0, 300),
                delay=0.01,
                color=(1, 0.8, 0.8),
                scale=1.5,
            )
            self.ended = True
            self.hideicons()
            bs.setmusic(None)
            bs.getsound('allydown').play()
            bs.timer(3.5, lambda: bs.setmusic(bs.MusicType.DEFEAT)) 
            bs.timer(3.5, lambda: TypewriterText(
                'im to lazy to get the actual music lamfao',
                position=(0, 300 + 20),
                delay=0.02,
                color=(1, 1, 1),
                scale=1.5,
            ))
            bs.timer(5.5, lambda: TypewriterText(
                'press space to exit btw',
                position=(0, 260 + 20),
                delay=0.02,
                color=(1, 1, 1),
                scale=1.3,
            ))
            bs.timer(6.5, lambda: TypewriterText(
                '(cuz u lost hahahaha)',
                position=(0, 220 + 20),
                delay=0.02,
                color=(1, 1, 1),
                scale=1.1,
            ))
            bs.timer(3.5, self.endtext.node.delete)
            self.players[0].actor.node.handlemessage(bs.DieMessage())
    
    # short for "Update Player Stats".
    def ups(self):
        self.hptext.text = str(self.player_hp)
        self.psypwrtext.text = str(self.player_pp)
        bs.timer(1.5, self.cfmd)
            
    # short for "Update Enemy Stats".
    def ues(self):
        if self.damagetext:
            self.damagetext.node.delete()
        randomx = random.randint(-80, 80)
        randomy = random.randint(-80, 140)
        self.damagetext = TypewriterText(
            str(self.damagenum),
            position=(randomx, randomy),
            delay=0.015,
            color=(1, 1, 1),
            scale=1.5,
        )
        if self.enemy_hp <= 0:
            self.endtext = TypewriterText(
                f"{self.enemy_name} stopped moving!",
                position=(0, 300),
                delay=0.01,
                color=(1, 1, 1),
                scale=1.5,
            )
            bs.animate(self.enemy, "opacity", {
                0.0: (1.0),
                0.3: (0.0)
            })
            bs.getsound('enemydown').play()
            self.enemyfuckingdied = True
            def do_end_thing():
                self.endtext.node.delete()
                self.endtext = TypewriterText(
                    'YOU WON!',
                    position=(0, 300),
                    delay=0.10,
                    color=(0.4, 0.4, 1.0),
                    scale=2.1,
                )
                self.ended = True
                bs.getsound('boxingBell').play()
                bs.timer(4.0, lambda: bs.setmusic(bs.MusicType.SCORES)) 
                bs.timer(7.5, lambda: TypewriterText(
                    '(press space to exit btw)',
                    position=(0, 250),
                    delay=0.02,
                    color=(1, 1, 1),
                    scale=1.5,
                ))
                bs.animate_array(self.earthchar, "position", 2,{
                    0.0: (self.meterx, self.metery - 40),
                    0.5: (self.meterx, self.metery + 100)
                })
                bs.animate_array(self.topborder, "position", 2,{
                    0.0: (0.0, 310),
                    1.0: (0.0, 530)
                })
                bs.animate_array(self.bottomborder, "position", 2,{
                    0.0: (0.0, -310),
                    1.0: (0.0, -530)
                })
                bs.setmusic(None)
            bs.timer(1.4, do_end_thing)
            
    # Do enemy's turn.
    def enemy_turn(self):
        if self.enemyfuckingdied == True:
            return
        if self.ended == True:
            return
        def enemy_attack():
            if self.is_guarding == True:
                self.damagenum = random.randint(4,19)
            else:
                self.damagenum = random.randint(14,35)
            self.player_hp -= self.damagenum
            mortalintensity = 53.0
            if self.player_hp <= 0:
                bs.getsound('mortaldamage').play()
                self.shake_node(self.earthmeter, intensity=mortalintensity, duration=2.0)
                self.shake_node(self.background.node, intensity=mortalintensity, duration=2.0)
                self.shake_node(self.enemy, intensity=mortalintensity, duration=2.0)
                self.shake_node(self.topborder, intensity=mortalintensity, duration=2.0)
                self.shake_node(self.bottomborder, intensity=mortalintensity, duration=2.0)
                self.ended = True
            else:
                bs.getsound('allydamage').play()
                self.shake_node(self.earthmeter, intensity=8.0, duration=0.8)
            self.ups()
            self.text.node.delete()
            name = self.players[0].actor.node.name
            self.text = TypewriterText(
                f"{name} took {str(self.damagenum)} HP of damage!",
                position=(0, 300),
                delay=0.01,
                color=(1, 1, 1),
                scale=1.5,
            )
            bs.timer(1.0, self._reset_action_state)
        self.text = TypewriterText(
            f"{self.enemy_name} attacks!",
            position=(0, 300),
            delay=0.01,
            color=(1, 1, 1),
            scale=1.5,
        )
        bs.getsound('enemyturn').play()
        bs.timer(1.3, enemy_attack)
    # Shouldn't rhythmic attack anymore. Our player either failed,
    # or we did a 16-beat attack
    def _end_chain_window(self):
        if self.timeschained == 0:
            return
        if self.damagetext:
            self.damagetext.node.delete()
        self.can_chain = False
        # Show how many beats we did.
        self.beatstext = TypewriterText(
            f"{self.timeschained} HITS",
            position=(0, 140),
            delay=0.02,
            color=(1, 1, 1),
            scale=1.7,
        )
        self.cant_chain = True
        self.timeschained = 0
        # small delay before allowing full control again
        bs.timer(0.8, self.beatstext.node.delete)
        bs.timer(0.9, self.enemy_turn)
        bs.animate_array(self.earthchar, "position", 2,{
            0.0: (self.meterx, self.metery + 100),
            0.5: (self.meterx, self.metery - 40)
        })

    # reset stufff
    def _reset_action_state(self):
        self.text.node.delete()
        if self.enemyfuckingdied == True:
            return
        self.in_action = False
        self.alreadyended = False
        self.cant_chain = False
        self.is_guarding = False
        self.currentoption = self.lastoption
        self.optiontext.text = self.currentoption
        self.guardicon.opacity = 1.0
        self.itemicon.opacity = 1.0
        self.bashicon.opacity = 1.0
        self.psicon.opacity = 1.0
        self.psimenumode = False
        
    # perform a attack; this is merged with sound attacking
    def _perform_attack(self):
        def actualattack():
            # character-specific instruments
            if self.chosen_group:
                if self.instrumentsound:
                    # stop the sound if it exists
                    self.instrumentsound.stop()
                sounds = [f"{self.chosen_group}{i}" for i in range(1, 4)]
                snd = sounds[self.sound_index]
                self.instrumentsound = bui.getsound(snd)
                self.instrumentsound.play()
                self.sound_index = (self.sound_index + 1) % len(sounds)
            else:
                sounds = self.players[0].actor.node.attack_sounds
                random.choice(sounds).play()
            bs.getsound('enemybashed').play()
            if self.timeschained == 0:
                self.damagenum = random.randint(71,175)
            else:
                self.damagenum = random.randint(21,35)
            self.enemy_hp -= self.damagenum
            self.ues()
            self.shake_node(self.enemy, intensity=10.0, duration=0.5)
        actualattack()
        self.text.node.delete()
        
        if self.timeschained >= 16:
            return
        self.can_chain = False
        # slight window where the player can
        # rhythmically time attacks
        def setchain():
            if self.cant_chain == True:
                return
            self.can_chain = True
        bs.timer(0.3, setchain)
        self.timeschained += 1
        # close that window if we didn't do anything
        self.chain_timer = bs.Timer(0.4, self._end_chain_window)
         
    def select(self):
        """Called when pressing confirm/jump."""
        if self.ended == True:
            # If we're all done, go straight to results screen.
            results = bs.GameResults()
            # Background for the ending fade out.
            self.endbackground = bs.newnode('image', 
                attrs={
                    'texture': bs.gettexture('bg'),
                    'absolute_scale': True,
                    'position': (0, 0),
                    'attach': 'center',
                    'opacity': 0.0,
                    'fill_screen': True,
                    'color': (1, 1, 1)
                }
            )
            bs.animate(self.endbackground, "opacity", {
                0.0: (0.0),
                1.5: (1.0)
            })
            self.end(results=results)
            return
        if self.enemyfuckingdied == True:
            return
        if self.in_action:
            if self.can_chain:
                self._perform_attack()
                if self.timeschained >= 16:
                    bs.getsound('cheer2').play()
                    self._end_chain_window()
            else:
                self._end_chain_window()
            # ignore if mid-attack but not in chain window
            return
        bs.getsound('swish').play()
        # normal menu behaviour
        if self.currentoption == 'Bash':
            self.attack()
            self.optiontext.text = ''
            self.lastoption = 'Bash'
        elif self.currentoption == 'PSI':
            self.openpsi()
            self.lastoption = 'PSI'
        elif self.currentoption == 'Guard':
            self.guard()
            self.optiontext.text = ''
            self.lastoption = 'Guard'
        elif self.currentoption in ['Lifeup', 'PSI Magnet', 'Love']:
            self.psimove()
            self.optiontext.text = ''
        else:
            print(f"Unknown menu option: {self.currentoption}")
            bs.getsound('error').play()
            
            
    def openpsi(self):
        self.psimenumode = True
        self.currentoption = 'Lifeup'
        self.optiontext.text = self.currentoption
    
    def go_right(self):
        """
        Choose options to the right.
        FIXME: Perhaps this is a bit hack-y?
               There are a lot of ways to make 
               rpg menus better than this.
        """
        if self.in_action == True:
            return
        if self.ended == True:
            return
        bs.getsound('click01').play()
        if self.psimenumode == True:
            if self.currentoption == 'Lifeup':
                self.currentoption = 'PSI Magnet'
            elif self.currentoption == 'PSI Magnet':
                self.currentoption = 'Love'
            elif self.currentoption == 'Love':
                self.currentoption = 'Lifeup'
            else:
                print(f"Unknown menu option: {self.currentoption}")
                bs.getsound('error').play()
        else:
            if self.currentoption == 'Bash':
                self.bashicon.texture = bs.gettexture('bashgrey')
                self.currentoption = 'Items'
                self.itemicon.texture = bs.gettexture('itemwhite')
            elif self.currentoption == 'Items':
                self.itemicon.texture = bs.gettexture('itemgrey')
                self.currentoption = 'PSI'
                self.psicon.texture = bs.gettexture('psiwhite')
            elif self.currentoption == 'PSI':
                self.psicon.texture = bs.gettexture('psigrey')
                self.currentoption = 'Guard'
                self.guardicon.texture = bs.gettexture('guardwhite')
            elif self.currentoption == 'Guard':
                self.guardicon.texture = bs.gettexture('guardgrey')
                self.currentoption = 'Bash'
                self.bashicon.texture = bs.gettexture('bashwhite')
            else:
                print(f"Unknown menu option: {self.currentoption}")
                bs.getsound('error').play()
        self.optiontext.text = self.currentoption       
            
    def go_left(self):
        """
        Choose options to the left.
        FIXME: Perhaps this is a bit hack-y?
               There are a lot of ways to make 
               rpg menus better than this.
        """
        if self.in_action == True:
            return
        if self.ended == True:
            return
        bs.getsound('click01').play()
        if self.psimenumode == True:
            if self.currentoption == 'Lifeup':
                self.currentoption = 'Love'
            elif self.currentoption == 'PSI Magnet':
                self.currentoption = 'Lifeup'
            elif self.currentoption == 'Love':
                self.currentoption = 'PSI Magnet'
            else:
                print(f"Unknown menu option: {self.currentoption}")
                bs.getsound('error').play()
        else:
            if self.currentoption == 'Bash':
                self.bashicon.texture = bs.gettexture('bashgrey')
                self.currentoption = 'Guard'
                self.guardicon.texture = bs.gettexture('guardwhite')
            elif self.currentoption == 'Items':
                self.itemicon.texture = bs.gettexture('itemgrey')
                self.currentoption = 'Bash'
                self.bashicon.texture = bs.gettexture('bashwhite')
            elif self.currentoption == 'PSI':
                self.psicon.texture = bs.gettexture('psigrey')
                self.currentoption = 'Items'
                self.itemicon.texture = bs.gettexture('itemwhite')
            elif self.currentoption == 'Guard':
                self.guardicon.texture = bs.gettexture('guardgrey')
                self.currentoption = 'PSI'
                self.psicon.texture = bs.gettexture('psiwhite')
            else:
                print(f"Unknown menu option: {self.currentoption}")
                bs.getsound('error').play()
        self.optiontext.text = self.currentoption
        
    def go_back(self):
        if self.in_action == True:
            return
        if self.enemyfuckingdied == True:
            return
        bs.getsound('back').play()
        if self.psimenumode == True:
            self.psimenumode = False
            self.currentoption = 'PSI'
            self.optiontext.text = self.currentoption
            
    def do_ui(self):
        """
        Make a bunch of ui-y stuff.
        """
        self.meterx = 0
        self.metery = -300
        playeractor = self.players[0].actor
        self.background = LoopingImageAnimation(
            prefix="mmbg",
            frame_count=12,
            frame_delay=0.15,
            scale=(1500, 1000),
            position=(1, 0),
        )
        self.topborder = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('white2'),
                'absolute_scale': True,
                'position': (0, 310),
                'attach': 'center',
                'opacity': 1.0,
                'scale': (2000, 200),
                'color': (0, 0, 0)
            }
        )
        self.bottomborder = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('white2'),
                'absolute_scale': True,
                'position': (0, -310),
                'attach': 'center',
                'opacity': 1.0,
                'scale': (2000, 200),
                'color': (0, 0, 0)
            }
        )
        self.earthchar = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture(playeractor.charimage),
                'absolute_scale': True,
                'position': (self.meterx, self.metery - 40),
                'attach': 'center',
                'opacity': 1.0,
                'scale': (150, 150),
                'color': (1, 1, 1)
            }
        )
        icon_scale = (250, 250)
        icon_x = 70
        icon_y = -70
        spacing = 120
        self.bashicon = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('bashwhite'),
                'absolute_scale': True,
                'position': (icon_x, icon_y),
                'attach': 'topLeft',
                'opacity': 1.0,
                'scale': icon_scale,
                'color': (1, 1, 1)
            }
        )
        self.itemicon = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('itemgrey'),
                'absolute_scale': True,
                'position': (icon_x + spacing, icon_y),
                'attach': 'topLeft',
                'opacity': 1.0,
                'scale': icon_scale,
                'color': (1, 1, 1)
            }
        )
        self.psicon = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('psigrey'),
                'absolute_scale': True,
                'position': (icon_x + spacing * 2, icon_y),
                'attach': 'topLeft',
                'opacity': 1.0,
                'scale': icon_scale,
                'color': (1, 1, 1)
            }
        )
        self.guardicon = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('guardgrey'),
                'absolute_scale': True,
                'position': (icon_x + spacing * 3, icon_y),
                'attach': 'topLeft',
                'opacity': 1.0,
                'scale': icon_scale,
                'color': (1, 1, 1)
            }
        )
        self.earthmeter = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('altearthmeter'),
                'absolute_scale': True,
                'position': (self.meterx, self.metery),
                'attach': 'center',
                'opacity': 1.0,
                'scale': (300, 300),
                'color': (1, 1, 1)
            }
        )
        self.nametext = bs.newnode(
            'text',
            attrs={
                'text': playeractor.node.name,
                'h_align': 'center',
                'position': (self.meterx, self.metery + 25),
                'scale': 1.4,
                'color': (1, 1, 1),
                'shadow': 0.7,
                'flatness': 0.6,
            },
        )
        self.hptext = bs.newnode(
            'text',
            attrs={
                'text': str(self.player_hp),
                'h_align': 'center',
                'position': (self.meterx + 45, self.metery - 20),
                'scale': 1.3,
                'color': (1, 1, 1),
                'shadow': 0.7,
                'flatness': 0.6,
            },
        )
        self.psypwrtext = bs.newnode(
            'text',
            attrs={
                'text': str(self.player_pp),
                'h_align': 'center',
                'position': (self.meterx + 45, self.metery - 65),
                'scale': 1.3,
                'color': (1, 1, 1),
                'shadow': 0.7,
                'flatness': 0.6,
            },
        )
        self.optiontext = bs.newnode(
            'text',
            attrs={
                'text': 'Bash',
                'h_align': 'left',
                'position': (-50, 280),
                'scale': 1.9,
                'color': (1, 1, 1),
                'shadow': 0.7,
                'flatness': 0.6,
            },
        )
        self.enemy = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('maskedman'),
                'absolute_scale': True,
                'position': (-10, 0),
                'attach': 'center',
                'opacity': 1.0,
                'scale': (220, 220),
                'color': (1, 1, 1)
            }
        )
    def donothing(self, value: float):
        # FIXME: shouldn't be stopping input with this.
        #        perhaps there's another way of removing input?
        return


