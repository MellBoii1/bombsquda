# Released under the MIT License. See LICENSE for details.
#
"""Music related bits."""

from __future__ import annotations
from typing import TYPE_CHECKING

import _bascenev1
import bascenev1 as bs
import babase
import bauiv1 as bui
import babase as ba
import mellboii.mell_resources as mell
import json
import os
from babase._logging import squdalog

if TYPE_CHECKING:
    pass

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
        with bs.get_foreground_host_session().context:
            from bascenev1lib.actor.musicnotif import MusicNotifier
            MusicNotifier(music_type=musictype)
    with ba.ContextRef.empty():
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
