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

if TYPE_CHECKING:
    pass


class MusicType(Enum):
    """Types of music available to play in-game.

    These do not correspond to specific pieces of music, but rather to
    'situations'. The actual music played for each type can be overridden
    by the game or by the user.
    """

    # ok lesson learned dont rename default music so it doesnt break vanilla online-play
    # perhaps should add music for when playing online?? seems cool audibly
    # also, don't rename the other names. they'll break if you pause and upnause.
    MENU = 'MENU'
    MENUPIANO = 'MENUPiano'
    MENU2 = 'MENU2'
    MENU3 = 'MENU3'
    MENU6 = 'MENU6'
    MENU7 = 'MENU7'
    MENU8 = 'MENU8'
    MENU9 = 'MENU9'
    MENU10 = 'MENU10'
    MENU11 = 'MENU11'
    MENU12 = 'MENU12'
    MENU67 = 'MENU67'
    VICTORY = 'Victory'
    VICTORYFINAL = 'VictoryFinal'
    CHAR_SELECT = 'Char_Select'
    CHAR_SELECT2 = 'Char_Select2'
    MINIONSELECT = 'Level Select'
    TUTORIAL = 'Tutorial'
    RUN_AWAY = 'Run_Away'
    MODULATINGTIME = 'ModulatingTime'
    HURRYUP = 'HURRYUP'
    ONSLAUGHT = 'Onslaught'
    CUTSCENE1 = 'Cutscene1'
    ONSLAUGHT2 = 'Onslaught2'
    ONSLAUGHT3 = 'Onslaught3'
    KEEP_AWAY = 'Keep_Away'
    RACE = 'Race'
    GAMBLING = 'Gambling'
    EPIC_RACE = 'Epic_Race'
    SCORES = 'Scores'
    GRAND_ROMP = 'Grand_Romp'
    METALCAPTIME = 'MetalCapTime'
    RAGE = 'Rage'
    NOISESUPER = 'NoiseSuper'
    REPRIEVE = 'Reprieve'
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
    D_RUNNIN = 'D_RUNNIN' # <- if you get the reference to what this is, you already know why its here.
    EPICFAST = 'EpicFast' # otherwise, it's used as the default music if there is a broken one
    SPORTS = 'Sports'
    HOCKEY = 'Hockey'
    FOOTBALL = 'Football'
    FLYING = 'Flying'
    FLYING2 = 'Flying2'
    SCARY = 'Scary'
    COOKIN = 'Cookin'
    MARCHING = 'Marching'
    DEFEAT = 'Defeat'
    BREAKFREE = 'BreakFree'
    CREDITS = 'Credits'
    THEFINALE = 'TheFinale'
    DEFEATQUMARK = 'DefeatQuMark'
    RUNAROUNDFINAL = 'RunaroundFinal'
    WAR = 'War'
    LAP0 = 'Lap0'
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
    
def show_music_now_playing(music_type: bs.MusicType) -> None:
        """
        Display current music on screen.
        """
        from bascenev1lib.actor.text import Text
        excluded_types = [
            None,
            bs.MusicType.CUTSCENE1,
            bs.MusicType.HURRYUP,
            bs.MusicType.PAUSE, 
            bs.MusicType.SURVEY,
            bs.MusicType.LOGOTYPE
        ]
        
        if music_type in excluded_types:
            return
        try:
            bs.getactivity()
        except babase._error.ActivityNotFoundError:
            return

        # Define a list of display names for each type
        # Here you should put music names and artists.
        music_names = {
            # bs.MusicType.MUSICTYPE: "musictitleandartistmaybe",
            bs.MusicType.TO_THE_DEATH: "Daniel Bautista - Intro",
            bs.MusicType.TO_THE_DEATH2: "Chrono Symphonic - Darkness Dueling (Plastic Men and Iron Blades)",
            bs.MusicType.TO_THE_DEATH2FAST: "Daniel Bautista - Flight of the Bumblebee",
            bs.MusicType.TO_THE_DEATH3FAST: "Bãtutã la trompeta - Rabbids Go Home",
            bs.MusicType.TO_THE_DEATH3: "Bãtutã din Moldova - Rabbids Go Home",
            bs.MusicType.TO_THE_DEATHFAST: "Daniel Bautista - Flight of the Bumblebee",
            bs.MusicType.EPIC: "Nocturne no. 2 in E-Flat major, op. 9 no. 2",
            bs.MusicType.CHAR_SELECT: "Overworld Map - Mario Kart World",
            bs.MusicType.REPRIEVE: "RETALIATION - Grace OST",
            bs.MusicType.TUTORIAL: "Doing it Right - Mario & Luigi: Bowser's Inside Story",
            bs.MusicType.ONLINE: "Across The World - Tyron",
            bs.MusicType.D_RUNNIN: "Runnin from Evil - Doom II", 
            bs.MusicType.BUSINESS: "Porky Means Business! - EarthBound",
            bs.MusicType.PAUSE: "As You Wish - MOTHER 3",
            bs.MusicType.SCORES: "Result (1st Place ~ 3rd Place)\n - Mario Kart: Double Dash!!",
            bs.MusicType.CHAR_SELECT2: "Sky Map - Mario Kart World",
            bs.MusicType.RACE: "VS Metal Sonic - Sonic Mania",
            bs.MusicType.MENU: "Mother Earth - Mother Encore",
            bs.MusicType.MENUPIANO: "Mother Earth Piano - Mother Encore",
            bs.MusicType.MENU2: "SMK Title Remastered - Turret 3471",
            bs.MusicType.MENU3: "Mario vs Luigi 2.0 Title Theme Remix - Goldyber",
            bs.MusicType.MENU6: "Cascade Zone Act 2 (Track B) - Bomb Boy",
            bs.MusicType.MENU7: "Mario vs Luigi 2.0 Title Theme",
            bs.MusicType.MENU8: "Mario Kart: Double Dash!! Title Theme",
            bs.MusicType.MENU9: "Start your Engines - CTGP-7",
            bs.MusicType.MENU10: "The Great Strategy - badliz",
            bs.MusicType.MENU11: "Title Theme -  Mario Kart 7",
            bs.MusicType.MENU12: "Friends no More x Papá Cerdito vs Bebé George",
            bs.MusicType.MENU67: "what the fuck is this",
            bs.MusicType.CREDITS: "Staff Roll - Mario Kart DS",
            bs.MusicType.SNESCOURSE: "SNES Battle Course - Mario Kart World",
            bs.MusicType.SNESCOURSE2: "Battle Course - Super Mario Kart",
            bs.MusicType.DEFEAT: "Blues in Velvet Room - Persona 3",
            bs.MusicType.THEFINALE: "Final Destination - Super Smash Bros Melee",
            bs.MusicType.WAR: "Thousand March - Pizza Tower",
            bs.MusicType.LAP0: "It's Pizza Time! - Pizza Tower",
            bs.MusicType.GAMBLING: "WEXECUTED (Instrumental) - Sherry",
            bs.MusicType.METALCAPTIME: "IT'S TV TIME but it's \nMetal Cap Theme\n - @secret_fan48",
            bs.MusicType.COOKIN: "True Final Boss - Sonic Mania",
            bs.MusicType.FOOTBALL: "Koopa Cape - Mario Kart Wii",
            bs.MusicType.RAGE: "Dr. Andonuts' Rage SSBU Mix - Frakture",
            bs.MusicType.GRAND_ROMP: "It's TV Time! - Deltarune",
            bs.MusicType.HOCKEY: "Koopa Cape - Mario Kart Wii",
            bs.MusicType.VICTORY: "Stars and Stripes Forever (Metal Rock Remix)\n - Blue Claw Philharmonic",
            bs.MusicType.VICTORYFINAL: "Stars and Stripes Forever (Metal Rock Remix, Longer)\n - Blue Claw Philharmonic",
            bs.MusicType.ONSLAUGHT2: "Ruder Buster - Deltarune",
            bs.MusicType.SURVIVAL: "Tough Guy Alert! - M&L:BIS GaMetal Remix",
            bs.MusicType.ONSLAUGHT3: "Rude Buster - Deltarune",
            bs.MusicType.NOISESUPER: "Unexpectancy Gatcha Remix - ClascyJitto",
        }
        # Get the music name from the list above.
        # If we don't get any, tell the player it's either unknown
        # or will be added later down the line. Laziness kills the mellboii.
        name = music_names.get(music_type, "TBA/Unknown")

        # Create text node (off-screen initially)
        txt = Text(
            f"Now playing: {name}",
            position=(1000, 20),
            h_attach=Text.HAttach.CENTER,
            h_align=Text.HAlign.CENTER,
            v_attach=Text.VAttach.BOTTOM,
            color=(1, 1, 1, 1),
            scale=0.8,
            shadow=0.5,
            flatness=0.5,
        ).autoretain()
        
        # Animate position: slide in then out after a delay
        bs.animate_array(
            txt.node,
            "position",
            2,
            {
                0.0: (1000, 20),
                1.0: (400, 20),  # visible position
                6.0: (400, 20),  # stay for ~6s
                7.0: (1000, 20),  # slide back out
            },
        )

        # Delete after finished.
        bs.timer(10.0, txt.node.delete)


def setmusic(musictype: MusicType | None, continuous: bool = False) -> None:
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
        gnode = _bascenev1.getactivity().globalsnode
    # If we get a activity not found error here, perhaps we're being used in UI context.
    # We'll use get_foreground_host_activity instead.
    # This should also clear the way for using music in UI, instead of resorting to activity-context.
    except babase._error.ActivityNotFoundError:
        gnode = bs.get_foreground_host_activity().globalsnode
    gnode.music_continuous = continuous
    gnode.music = '' if musictype is None else musictype.value
    gnode.music_count += 1
    show_music_now_playing(music_type=musictype)
    
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