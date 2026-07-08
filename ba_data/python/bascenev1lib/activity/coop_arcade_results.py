"""Activity for coop session (arcade mode) results."""
from typing import override
import bascenev1 as bs
import random
from bascenev1lib.actor.parallax import ParallaxImage
from bascenev1lib.actor.spazfactory import SpazFactory

class CoopArcadeResults(bs.Activity[bs.Player, bs.Team]):
    def on_begin(self):
        self._score_text = 0
        self._header_sound = bs.getsound('cashRegister2')
        self._player_entry_sound = bs.getsound('player_ready')
        self._no_penalties_sound = bs.getsound('berdly_applause')
        self._final_rank_drumroll = bs.getsound('delta_drumroll')
        self._final_rank_good_sound = bs.getsound('berdly_applause')
        self._final_rank_bad_sound = bs.getsound('crowd_gasp')
        self._penalty_sound = bs.getsound('impactMedium')
        self._score_tick_sound = bs.getsound('tap')
        bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white2'),
                'color': (0, 0, 0),
                'fill_screen': True,
            }
        )
        scale = 3
        y = 340
        # start parallax stripes
        img1 = ParallaxImage(
            texture=bs.gettexture('stripes_top'),
            position=(0, y),
            size=(512 * scale, 64 * scale),
        )
        img2 = ParallaxImage(
            texture=bs.gettexture('stripes_bottom'),
            position=(0, -y),
            size=(512 * scale, 64 * scale),
        )
        img1.autoretain()
        img2.autoretain()
        def anim(node):
            bs.animate(
                node, 
                'opacity',
                {
                    0: 0,
                    1: 1,
                }
            )
        anim(img1.node1)
        anim(img1.node2)
        anim(img2.node1)
        anim(img2.node2)
        bs.timer(2, self.show_players)
    
    def show_players(self):
        lstr = bs.Lstr(
            value='- ${A} -',
            subs=[
                ('${A}', bs.Lstr(r='resultsPlayerText')),
            ],
        )
        self._header_sound.play()
        pos = (-300, 150)
        bs.newnode(
            'text',
            attrs={
                'text': lstr,
                'scale': 1.1,
                'position': pos,
                'h_align': 'center',
                'color': (0.8, 0.9, 1),
            }
        )
        y = pos[1] - 40
        i = 2
        for player in self.players:
            def do_it(p: bs.Player, y: int):
                self._player_entry_sound.play()
                fac = SpazFactory.get()
                media = fac.get_media(p.character)
                random.choice(media['jump_sounds']).play()
                bs.newnode(
                    'text',
                    attrs={
                        'text': p.getname(full=True),
                        'color': bs.safecolor(p.color),
                        'position': (pos[0], y),
                        'h_align': 'center',
                    }
                )
            bs.timer(i, bs.Call(do_it, p=player, y=y))
            y -= 30
            i += 0.7
        i += 1.3
        bs.timer(i, self.show_penalties)
    
    def show_penalties(self):
        penalties = []
        lstr = bs.Lstr(
            value='- ${A} -',
            subs=[
                ('${A}', bs.Lstr(r='resultsPenaltiesText')),
            ],
        )
        self._header_sound.play()
        pos = (-100, 150)
        bs.newnode(
            'text',
            attrs={
                'text': lstr,
                'scale': 1.1,
                'position': pos,
                'h_align': 'center',
                'color': (1, 0.8, 7),
            }
        )
        y = pos[1] - 40
        i = 2         
        def do_it(sound, text, color=(0.9, 0.8, 0.8), scale=1.0):
            sound.play()
            bs.newnode(
                'text',
                attrs={
                    'text': text,
                    'color': color,
                    'position': (pos[0], y),
                    'scale': scale,
                    'h_align': 'center',
                }
            )
        if penalties:
            for penalty, score_dec in penalties:
                text = bs.Lstr(
                    value='-${A} ${B}',
                    subs=[
                        ('${A}', score_dec),
                        ('${B}', penalty),
                    ],
                )
                bs.timer(i, 
                    bs.Call(
                        do_it, 
                        self._penalty_sound, 
                        text
                    )
                )
                y -= 30
                i += 0.4
        else:
            text = bs.Lstr(r='resultsNoPenaltiesText')
            y -= 10
            bs.timer(i, 
                bs.Call(
                    do_it, 
                    sound=self._no_penalties_sound,
                    text=text,
                    color=(0.6, 0.7, 1.0),
                    scale=1.3,
                )
            )
        i += 1.3
        bs.timer(i, self.show_score) 
    
    def show_score(self):
        lstr = bs.Lstr(
            value='- ${A} -',
            subs=[
                ('${A}', bs.Lstr(r='resultsScoreText')),
            ],
        )
        self._header_sound.play()
        pos = (100, 150)
        bs.newnode(
            'text',
            attrs={
                'text': lstr,
                'scale': 1.1,
                'position': pos,
                'h_align': 'center',
                'color': (1, 1, 0.6),
            }
        )

        y = pos[1] - 40
        i = 2        
        score_node = bs.newnode(
            'text',
            attrs={
                'text': '0',
                'position': (pos[0], y),
                'h_align': 'center',
            }
        )
        def do_it():
            self._score_text += 1
            score_node.text = str(self._score_text)
            self._score_tick_sound.play()
            
        for _ in range(self.session._total_score):
            bs.timer(i, do_it)
            i += 0.01
        i += 0.6
        bs.timer(i, self.show_final_rank)
    
    def show_final_rank(self):
        self._final_rank_drumroll.play()
        pos = (270, -100)
        # if this is eggplant, means 
        # that we're likely just testing; or no rank implementations yet.
        rank = 'eggplant'
        if rank in ['S', 'A', 'B']:
            music = bs.MusicType.FINALRESULTS_GOOD
            sound = self._final_rank_good_sound
        else:
            music = bs.MusicType.FINALRESULTS_BAD
            sound = self._final_rank_bad_sound
        lstr = bs.Lstr(
            value='${A}:',
            subs=[
                ('${A}', bs.Lstr(r='resultsYourRankText')),
            ],
        )
        bs.newnode(
            'text',
            attrs={
                'text': lstr,
                'scale': 1.1,
                'position': pos,
                'h_align': 'right',
            }
        )
        i = 1.1
        def do_it():
            sound.play()
            scale = 1.1
            bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture(f'finalRank{rank}'),
                    'position': (pos[0] + 70, pos[1] - 7),
                    'scale': (128 * scale, 128 * scale),
                }
            )
        bs.timer(i, do_it)
        i += 1.3
        bs.timer(i, bs.Call(bs.setmusic, music))
        def do_it2():
            scale = 1.1
            text = bs.Lstr(r=f'resultsRank{rank}Sub')
            node = bs.newnode(
                'text',
                attrs={
                    'text': text,
                    'color': (0.8, 0.8, 0.8),
                    'position': (pos[0] + 20, pos[1] - 130),
                    'scale': 0.9,
                    'h_align': 'center',
                }
            )
            bs.animate(
                node,
                'opacity',
                {
                    0: 0,
                    1: 1,
                }
            )
        i += 0.6
        bs.timer(i, do_it2)
        i += 2
        bs.timer(i, self.assign_controls)

    def assign_controls(self):
        scale = 0.5
        color = (0.2, 0.9, 0.1)
        pos = (550, -200)
        node = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('buttonJump'),
                'position': (pos[0], pos[1]),
                'scale': (128 * scale, 128 * scale),
            }
        )
        flash_inc = 0.3
        bs.animate_array(
            node,
            'color', 3,
            {
                0: color,
                0.2: (
                    color[0] + flash_inc, 
                    color[1] + flash_inc, 
                    color[2] + flash_inc
                ),
                0.4: color,
            },
            loop=True
        )
        bs.animate(
            node,
            'opacity',
            {
                0: 0,
                0.3: 1,
            }
        )
        classic = bs.app.classic
        func = classic.return_to_main_menu_session_gracefully
        for player in self.players:
            player.assigninput(bs.InputType.JUMP_PRESS, func)