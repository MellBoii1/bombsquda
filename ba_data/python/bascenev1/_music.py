# Released under the MIT License. See LICENSE for details.
#
"""Music related bits."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import _bascenev1
import bascenev1 as bs
import babase
import bauiv1 as bui
import babase as ba
import fromgoverhaul.mell_resources as mell
import json
import os
from babase._logging import squdalog

if TYPE_CHECKING:
    pass

class MusicType(Enum):
    """Types of music available to play in-game.

    These do not correspond to specific pieces of music, but rather to
    'situations'. The actual music played for each type can be overridden
    by the game or by the user.
    """
    
    # don't rename the strings, 
    # some music breaks if you do
    MENU1 = 'MENU1'
    MENU2 = 'MENU2'
    MENU3 = 'MENU3'
    MENU4 = 'MENU4'
    MENU5 = 'MENU5'
    MENU6 = 'MENU6'
    MENU7 = 'MENU7'
    MENU8 = 'MENU8'
    MENU9 = 'MENU9'
    MENU10 = 'MENU10'
    MENU11 = 'MENU11'
    MENU12 = 'MENU12'
    MENU13 = 'MENU13'
    MENU14 = 'MENU14'
    MENU15 = 'MENU15'
    MENU16 = 'MENU16'
    MENU17 = 'MENU17'
    MENU18 = 'MENU18'
    MENU19 = 'MENU19'
    MENU20 = 'MENU20'
    MENU21 = 'MENU21'
    MENU22 = 'MENU22'
    MENU67 = 'MENU67'
    RMENU = 'RMENU'
    VICTORY = 'Victory'
    VICTORYFINAL = 'VictoryFinal'
    COOP_SELECT = 'Coop_Select'
    FINALE_SELECT = 'Finale_Select'
    FFA_SELECT1 = 'FFA_Select1'
    TEAMS_SELECT1 = 'Teams_Select1'
    TEAMS_SELECT2 = 'Teams_Select2'
    TUTORIAL = 'Tutorial'
    RUN_AWAY = 'Run_Away'
    MODULATINGTIME = 'ModulatingTime'
    HURRYUP = 'HURRYUP'
    CUTSCENE1 = 'Cutscene1'
    CUTSCENE2 = 'Cutscene2'
    ONSLAUGHT = 'Onslaught'
    ONSLAUGHT2 = 'Onslaught2'
    KEEP_AWAY = 'Keep_Away'
    RACE = 'Race'
    GAMBLING = 'Gambling'
    EPIC_RACE = 'Epic_Race'
    SCORES = 'Scores'
    GRAND_ROMP = 'Grand_Romp'
    METALCAPTIME = 'MetalCapTime'
    RAGE = 'Rage'
    NOISESUPER = 'NoiseSuper'
    KAIZOKNIGHT = 'KaizoKnight'
    BUSINESS = 'Business'
    TO_THE_DEATH = 'To_The_Death'
    TO_THE_DEATHFAST = 'To_The_DeathFast'
    TO_THE_DEATH2FAST = 'To_The_Death2Fast'
    TO_THE_DEATH2 = 'To_The_Death2'
    TO_THE_DEATH3FAST = 'To_The_Death3Fast'
    TO_THE_DEATH3 = 'To_The_Death3'
    KEEP_AWAY2 = 'Keep_Away2'
    CHOSEN_ONE = 'Chosen_One'
    FORWARD_MARCH = 'Forward_March'
    FLAG_CATCHER = 'Flag_Catcher'
    SURVIVAL = 'Survival'
    EPIC = 'Epic'
    ONLINE = 'Online'
    PAUSE = 'Pause'
    SHOP = 'Shop'
    D_RUNNIN = 'D_RUNNIN'
    EPICFAST = 'EpicFast'
    SPORTS = 'Sports'
    FOOTBALL = 'Football'
    FLYING = 'Flying'
    FLYING2 = 'Flying2'
    SCARY = 'Scary'
    SUPER = 'Super'
    FEEL_THE_FURY = 'Feel_The_Fury'
    RAINBOW_ROAD = 'RAINBOW_ROAD'
    SRB2_OVERTIME = 'SRB2_Overtime'
    SRB2_PINCH = 'SRB2_Pinch'
    MARCHING = 'Marching'
    DEFEAT = 'Defeat'
    COOP_LOSS = 'Coop_Loss'
    CREDITS = 'Credits'
    THEFINALE = 'TheFinale'
    FINALDESTINATION = 'FinalDestination'
    RUNAROUNDFINAL = 'RunaroundFinal'
    WAR = 'War'
    WWR = 'Wwr'
    LAP0 = 'Lap0'
    LAP0H = 'Lap0H'
    LAP1 = 'Lap1'
    LAP2 = 'Lap2'
    LAP3 = 'Lap3'
    LAP4 = 'Lap4'
    LAP5 = 'Lap5'
    LAP6 = 'Lap6'
    LAP7 = 'Lap7'
    LAP8 = 'Lap8'
    LAP9 = 'Lap9'
    SNESCOURSE = 'SNESCourse'
    SNESCOURSE2 = 'SNESCourse2'
    DS1 = 'DS1'
    DS2 = 'DS2'
    DS3 = 'DS3'
    SURVEY = 'SURVEY'
    LOGOTYPE = 'LOGOTYPE'
    OPENING = 'Opening'
    CRASH_HANDLER = 'Crash_Handler'
    ELIM_DANGER = 'Elim_Danger'
    ELIM_VERSUS = 'Elim_Versus'
    STARMAN = 'Starman'
    HARDMODE1 = 'HardMode1'
    HARDMODE2 = 'HardMode2'
    HARDMODE3 = 'HardMode3'
    COOP_VICTORY = 'Coop_Victory'

def _get_free_slot(slots: dict) -> int:
    slot = 0
    while slot in slots:
        slot += 1
    return slot  

def get_music_value(music_name: str):
    path = os.path.join(
        babase.app.env.data_directory,
        'ba_data',
        'data',
        'musicvals.json',
    )
    with open(path, encoding='utf-8') as infile:
        music_names = json.loads(infile.read())
    if isinstance(music_name, str):
        for type in bs.MusicType:
            if type.value.lower() == music_name.lower():
                music_name = str(type)
    else:
        music_name = str(music_name)
    name = music_names.get(
        music_name,
        {
            'title': 'UNKNOWN',
            'artist': music_name, 
            'artist_keyword': 'from'
        }
    )
    return name
def setmusic(musictype: MusicType | None, continuous: bool = False, show_playing: bool = True) -> None:
    """Set the app to play (or stop playing) a certain type of music.

    This function will handle loading and playing sound assets as
    necessary, and also supports custom user soundtracks on specific
    platforms so the user can override particular game music with their
    own.

    Pass ``None`` to stop music.

    if ``continuous`` is True and musictype is the same as what is
    already playing, the playing track will not be restarted.
    """

    # All we do here now is set a few music attrs on the current globals
    # node. The foreground globals' current playing music then gets fed to
    # the do_play_music call in our music controller. This way we can
    # seamlessly support custom soundtracks in replays/etc since we're being
    # driven purely by node data.
    
    # Check if we have a activity.
    try:
        activity = bs.getactivity()
    # Use foreground host activity instead.
    except babase._error.ActivityNotFoundError:
        activity = bs.get_foreground_host_activity()
    gnode = activity.globalsnode
    gnode.music_continuous = continuous
    gnode.music = '' if musictype is None else musictype.value
    gnode.music_count += 1

    with bs.get_foreground_host_session().context:
        # Don't show game-set music if the player
        # is using the boombox, if the game doesn't
        # want to, or it's using a excluded music (or nothing)
        excluded = [
            None,
            bs.MusicType.CUTSCENE1,
            bs.MusicType.CUTSCENE2,
            bs.MusicType.HURRYUP,
        ]
        if (
            ba.app.config.get("squda_isplayingmusic")
            or not show_playing
            or musictype in excluded
        ):
            return
        def make():
            from bascenev1lib.actor.musicnotif import MusicNotifier
            MusicNotifier(music_type=musictype).autoretain()
    ba.apptimer(0, make)
    
def localsetmusic(musictype: MusicType | None, continuous: bool = False) -> None:
    """
    Allows you to set music locally,
    which is better than just muting the volume
    and using the fuckin music app
    Probably like a replacement for soundtracks
    on windows lfmafoafoafoaofa
    """
    musiclassic = bui.app.classic.music
    if musictype == None:
        musiclassic.set_music_play_mode(
            bui.app.classic.MusicPlayMode.REGULAR, force_restart=True
        )
    else:
        musiclassic.set_music_play_mode(bui.app.classic.MusicPlayMode.TEST)
        musiclassic.do_play_music(
            musictype,
            mode=bui.app.classic.MusicPlayMode.TEST,
        )
        
def getmusic():
    """
    gets the current playing music
    """
    return getattr(bs.MusicType, bs.get_foreground_host_activity().globalsnode.music.upper())

def test_musicnames():
    """
    this plays all music types that are in bs.MusicType.
    refrain from using this unless you wanna test 
    if the Now Playing is missing any musictypes
    """
    list = [
        getattr(bs.MusicType, music_type) for music_type in 
        dir(bs.MusicType) if not music_type.startswith('__')
    ]
    for musictype in list:
        bs.setmusic(musictype)
