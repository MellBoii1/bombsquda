# Released under the MIT License. See LICENSE for details.
#
"""Music related functionality."""
from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

import babase
import bascenev1
from babase._logging import squdalog
from bascenev1 import MusicType

if TYPE_CHECKING:
    from typing import Callable, Any

    import bauiv1


class MusicPlayMode(Enum):
    """Influences behavior when playing music."""

    REGULAR = 'regular'
    TEST = 'test'


@dataclass
class AssetSoundtrackEntry:
    """A music entry using an internal asset."""

    assetname: str
    volume: float = 1.0
    loop: bool = True


# What gets played by default for our different music types:
ASSET_SOUNDTRACK_ENTRIES: dict[MusicType, AssetSoundtrackEntry] = {
    MusicType.MENU1: AssetSoundtrackEntry('music/menuMusic'),
    MusicType.MENU2: AssetSoundtrackEntry('music/menuMusic2'),
    MusicType.MENU3: AssetSoundtrackEntry('music/menuMusic3'),
    MusicType.MENU4: AssetSoundtrackEntry('music/menuMusic4'),
    MusicType.MENU5: AssetSoundtrackEntry('music/menuMusic5'),
    MusicType.MENU6: AssetSoundtrackEntry('music/menuMusic6'),
    MusicType.MENU7: AssetSoundtrackEntry('music/menuMusic7'),
    MusicType.MENU8: AssetSoundtrackEntry('music/menuMusic8'), 
    MusicType.MENU9: AssetSoundtrackEntry('music/menuMusic9'),
    MusicType.MENU10: AssetSoundtrackEntry('music/menuMusic10'),
    MusicType.MENU11: AssetSoundtrackEntry('music/menuMusic11'),
    MusicType.MENU12: AssetSoundtrackEntry('music/menuMusic12'),
    MusicType.MENU13: AssetSoundtrackEntry('music/menuMusic13'),
    MusicType.MENU14: AssetSoundtrackEntry('music/menuMusic14'),
    MusicType.MENU15: AssetSoundtrackEntry('music/menuMusic15'),
    MusicType.MENU16: AssetSoundtrackEntry('music/menuMusic16'),
    MusicType.MENU17: AssetSoundtrackEntry('music/menuMusic17'),
    MusicType.MENU18: AssetSoundtrackEntry('music/menuMusic18'),
    MusicType.MENU19: AssetSoundtrackEntry('music/menuMusic19'),
    MusicType.MENU20: AssetSoundtrackEntry('music/menuMusic20'),
    MusicType.MENU21: AssetSoundtrackEntry('music/menuMusic21'),
    MusicType.MENU22: AssetSoundtrackEntry('music/menuMusic22'),
    MusicType.RMENU: AssetSoundtrackEntry('music/redditorMenu'),
    MusicType.MENU67: AssetSoundtrackEntry('music/stupidfuckingmenu'), 
    MusicType.VICTORY: AssetSoundtrackEntry(
        'music/victoryMusic', volume=1.2, loop=False
    ),
    MusicType.VICTORYFINAL: AssetSoundtrackEntry(
        'music/victoryFinal', volume=1.4, loop=False
    ),
    ##########
    MusicType.COOP_SELECT: AssetSoundtrackEntry('music/coopSelect', volume=1.0),
    MusicType.FINALE_SELECT: AssetSoundtrackEntry('music/finaleSelect', volume=1.0),
    MusicType.FFA_SELECT1: AssetSoundtrackEntry('music/ffaSelect1', volume=1.0),
    MusicType.TEAMS_SELECT1: AssetSoundtrackEntry('music/teamsSelect1', volume=1.0),
    MusicType.TEAMS_SELECT2: AssetSoundtrackEntry('music/teamsSelect2', volume=1.0),
    ###########
    MusicType.TUTORIAL: AssetSoundtrackEntry('music/tutorial', volume=1.4),
    MusicType.RUN_AWAY: AssetSoundtrackEntry('music/runAwayMusic', volume=1.0),
    MusicType.METALCAPTIME: AssetSoundtrackEntry('music/metalMusicALT', volume=2.0),
    MusicType.ONSLAUGHT: AssetSoundtrackEntry('music/onslaughtMusic', volume=1.0),
    MusicType.ONSLAUGHT2: AssetSoundtrackEntry('music/onslaughtMusic2', volume=1.0),
    MusicType.FINALDESTINATION: AssetSoundtrackEntry('music/finaldestination', volume=2.1),
    MusicType.THEFINALE: AssetSoundtrackEntry('music/bis_finale', volume=2.1),
    MusicType.NOISESUPER: AssetSoundtrackEntry('music/noisexpectancy', volume=1.0),
    MusicType.KAIZOKNIGHT: AssetSoundtrackEntry('music/knight_super', volume=1.0),
    MusicType.FEEL_THE_FURY: AssetSoundtrackEntry('music/feel_the_fury', volume=1.0),
    MusicType.RAINBOW_ROAD: AssetSoundtrackEntry('music/RAINBOW_ROAD', volume=1.0),
    MusicType.SURVEY: AssetSoundtrackEntry('music/SURVEYPROGRAM', volume=1.0),
    MusicType.LOGOTYPE: AssetSoundtrackEntry('music/LOGOTYPE', volume=1.0, loop=False),
    MusicType.WAR: AssetSoundtrackEntry('music/warneverends', volume=1.9),
    MusicType.WWR: AssetSoundtrackEntry('music/warwithoutreason', volume=1.0),
    MusicType.RUNAROUNDFINAL: AssetSoundtrackEntry('music/finalrunrou', volume=1.0),
    MusicType.HURRYUP: AssetSoundtrackEntry('music/hurryup', volume=1.0, loop=False),
    MusicType.SUPER: AssetSoundtrackEntry('music/super', volume=1.1, loop=True),
    MusicType.SRB2_PINCH: AssetSoundtrackEntry('music/srb2_pinch', volume=1.1, loop=True),
    MusicType.SRB2_OVERTIME: AssetSoundtrackEntry('music/srb2_overtime', volume=1.1, loop=True),
    MusicType.KEEP_AWAY: AssetSoundtrackEntry('music/keepAway', volume=1.0),
    MusicType.KEEP_AWAY2: AssetSoundtrackEntry('music/keepAway2', volume=1.0),
    MusicType.RACE: AssetSoundtrackEntry('music/raceMusic', volume=1.0),
    MusicType.GAMBLING: AssetSoundtrackEntry('music/gamblingMusic', volume=1.0),
    MusicType.CUTSCENE1: AssetSoundtrackEntry('music/cutscene1', loop=False),
    MusicType.CUTSCENE2: AssetSoundtrackEntry('music/cutscene2', loop=False),
    MusicType.EPIC_RACE: AssetSoundtrackEntry('music/slowRaceMusic', volume=1.0),
    MusicType.SCORES: AssetSoundtrackEntry(
        'music/scoresEpicMusic', volume=1.0, loop=True
    ),
    MusicType.CREDITS: AssetSoundtrackEntry('music/creditsroll', loop=False),
    MusicType.BUSINESS: AssetSoundtrackEntry('music/porky'),
    MusicType.DEFEAT: AssetSoundtrackEntry('music/coopResultsMusic'),
    MusicType.COOP_LOSS: AssetSoundtrackEntry('loss', volume=1.4),
    MusicType.GRAND_ROMP: AssetSoundtrackEntry('music/grandRompMusic', volume=1.5),
    MusicType.OPENING: AssetSoundtrackEntry('music/openingcreditsBTTDW', volume=1.0, loop=False),
    MusicType.RAGE: AssetSoundtrackEntry('music/ebhh_megalovania', volume=1.2),
    MusicType.TO_THE_DEATH: AssetSoundtrackEntry('music/DM_Music', volume=1.0),
    MusicType.TO_THE_DEATHFAST: AssetSoundtrackEntry('music/DMFMusic', volume=1.0),
    MusicType.TO_THE_DEATH2: AssetSoundtrackEntry('music/DM2Music', volume=1.4),
    MusicType.TO_THE_DEATH2FAST: AssetSoundtrackEntry('music/DMFMusic', volume=1.0),
    MusicType.TO_THE_DEATH3: AssetSoundtrackEntry('music/DM3Music', volume=1.0),
    MusicType.TO_THE_DEATH3FAST: AssetSoundtrackEntry('music/DM3FMusic', volume=1.0),
    MusicType.SNESCOURSE: AssetSoundtrackEntry('music/snesCourse', volume=1.0),
    MusicType.ONLINE: AssetSoundtrackEntry('music/acrosstheworld'),
    MusicType.PAUSE: AssetSoundtrackEntry('music/pausemusic'),
    MusicType.MODULATINGTIME: AssetSoundtrackEntry('music/O_TETR'),
    MusicType.D_RUNNIN: AssetSoundtrackEntry('music/d_runnin'),
    MusicType.SNESCOURSE2: AssetSoundtrackEntry('music/snesCourse2', volume=1.0),
    MusicType.DS1: AssetSoundtrackEntry('music/mkds3', volume=1.0),
    MusicType.DS2: AssetSoundtrackEntry('music/mkds1', volume=1.0),
    MusicType.DS3: AssetSoundtrackEntry('music/mkds2', volume=1.0),
    MusicType.CHOSEN_ONE: AssetSoundtrackEntry('music/survivalMusic', volume=0.8),
    MusicType.FORWARD_MARCH: AssetSoundtrackEntry(
        'music/forwardMarchMusic', volume=0.8
    ),
    MusicType.FLAG_CATCHER: AssetSoundtrackEntry(
        'music/flagCatcherMusic', volume=1.2
    ),
    MusicType.SURVIVAL: AssetSoundtrackEntry('music/survivalMusic', volume=0.8),
    MusicType.EPIC: AssetSoundtrackEntry('music/slowEpicMusic', volume=1.2),
    MusicType.EPICFAST: AssetSoundtrackEntry('music/fastEpicMusic'),
    MusicType.SPORTS: AssetSoundtrackEntry('music/sportsMusic', volume=0.8),
    MusicType.FOOTBALL: AssetSoundtrackEntry('music/footballMusic', volume=0.8),
    MusicType.ELIM_DANGER: AssetSoundtrackEntry('music/danger_mbm'),
    MusicType.ELIM_VERSUS: AssetSoundtrackEntry('music/versus_mbm'),
    MusicType.FLYING: AssetSoundtrackEntry('music/flyingMusic', volume=0.8),
    MusicType.FLYING2: AssetSoundtrackEntry('music/flyingMusic2'),
    MusicType.SCARY: AssetSoundtrackEntry('music/scaryMusic', volume=0.8),
    MusicType.LAP0: AssetSoundtrackEntry('music/lap0'),
    MusicType.LAP0H: AssetSoundtrackEntry('music/lap0H'),
    MusicType.LAP1: AssetSoundtrackEntry('music/lap1'),
    MusicType.LAP2: AssetSoundtrackEntry('music/lap2'),
    MusicType.LAP3: AssetSoundtrackEntry('music/lap3'),
    MusicType.LAP4: AssetSoundtrackEntry('music/lap4'),
    MusicType.LAP5: AssetSoundtrackEntry('music/lap5'),
    MusicType.LAP6: AssetSoundtrackEntry('music/lap6'),
    MusicType.LAP7: AssetSoundtrackEntry('music/lap7'),
    MusicType.LAP8: AssetSoundtrackEntry('music/lap8'),
    MusicType.LAP9: AssetSoundtrackEntry('music/lap9'),
    MusicType.CRASH_HANDLER: AssetSoundtrackEntry('music/crash_handler'),
    MusicType.SHOP: AssetSoundtrackEntry('music/shop'),
    MusicType.STARMAN: AssetSoundtrackEntry('music/starman', volume=1.0, loop=False),
    MusicType.HARDMODE1: AssetSoundtrackEntry('music/stronger', volume=1.0),
    MusicType.HARDMODE2: AssetSoundtrackEntry('music/asgore', volume=1.0),
    MusicType.HARDMODE3: AssetSoundtrackEntry('music/sans', volume=1.0),
    MusicType.COOP_VICTORY: AssetSoundtrackEntry('music/coop_victory', volume=1.0, loop=False),
    MusicType.MARCHING: AssetSoundtrackEntry(
        'music/runaroundMusic', volume=0.8
    ),
}



class MusicSubsystem:
    """Subsystem for music playback in the app.

    Access the single shared instance of this class at 'ba.app.music'.
    """

    def __init__(self) -> None:
        # pylint: disable=cyclic-import
        # self._music_node: _bascenev1.Node | None = None
        self._playing_internal_music = False
        self._music_mode: MusicPlayMode = MusicPlayMode.REGULAR
        self._music_player: MusicPlayer | None = None
        self._music_player_type: type[MusicPlayer] | None = None
        self.music_types: dict[MusicPlayMode, MusicType | None] = {
            MusicPlayMode.REGULAR: None,
            MusicPlayMode.TEST: None,
        }

        # Set up custom music players for platforms that support them.
        # FIXME: should generalize this to support arbitrary players per
        # platform (which can be discovered via ba_meta).
        # Our standard asset playback should probably just be one of them
        # instead of a special case.
        if self.supports_soundtrack_entry_type('musicFile'):
            from baclassic.osmusic import OSMusicPlayer

            self._music_player_type = OSMusicPlayer
        elif self.supports_soundtrack_entry_type('iTunesPlaylist'):
            from baclassic.macmusicapp import MacMusicAppMusicPlayer

            self._music_player_type = MacMusicAppMusicPlayer

    def on_app_loading(self) -> None:
        """Should be called by app on_app_loading()."""

        # If we're using a non-default playlist, lets go ahead and get our
        # music-player going since it may hitch (better while we're faded
        # out than later).
        try:
            cfg = babase.app.config
            if 'Soundtrack' in cfg and cfg['Soundtrack'] not in [
                '__default__',
                'Default Soundtrack',
            ]:
                self.get_music_player()
        except Exception:
            logging.exception('Error prepping music-player.')

    def on_app_shutdown(self) -> None:
        """Should be called when the app is shutting down."""
        if self._music_player is not None:
            self._music_player.shutdown()

    def have_music_player(self) -> bool:
        """Returns whether a music player is present."""
        return self._music_player_type is not None

    def get_music_player(self) -> MusicPlayer:
        """Returns the system music player, instantiating if necessary."""
        if self._music_player is None:
            if self._music_player_type is None:
                raise TypeError('no music player type set')
            self._music_player = self._music_player_type()
        return self._music_player

    def music_volume_changed(self, val: float) -> None:
        """Should be called when changing the music volume."""
        if self._music_player is not None:
            self._music_player.set_volume(val)

    def set_music_play_mode(
        self, mode: MusicPlayMode, force_restart: bool = False
    ) -> None:
        """Sets music play mode; used for soundtrack testing/etc."""
        old_mode = self._music_mode
        self._music_mode = mode
        if old_mode != self._music_mode or force_restart:
            # If we're switching into test mode we don't
            # actually play anything until its requested.
            # If we're switching *out* of test mode though
            # we want to go back to whatever the normal song was.
            if mode is MusicPlayMode.REGULAR:
                mtype = self.music_types[MusicPlayMode.REGULAR]
                self.do_play_music(None if mtype is None else mtype.value)

    def supports_soundtrack_entry_type(self, entry_type: str) -> bool:
        """Return whether provided soundtrack entry type is supported here."""
        # Note to self; can't access babase.app.classic here because
        # we are called during its construction.
        env = babase.env()
        platform = env.get('platform')
        assert isinstance(platform, str)
        if entry_type == 'iTunesPlaylist':
            return platform == 'mac' and babase.is_xcode_build()
        if entry_type in ('musicFile', 'musicFolder'):
            return (
                platform == 'android'
                and babase.android_get_external_files_dir() is not None
            )
        if entry_type == 'default':
            return True
        return False

    def get_soundtrack_entry_type(self, entry: Any) -> str:
        """Given a soundtrack entry, returns its type, taking into
        account what is supported locally."""
        try:
            if entry is None:
                entry_type = 'default'

            # Simple string denotes iTunesPlaylist (legacy format).
            elif isinstance(entry, str):
                entry_type = 'iTunesPlaylist'

            # For other entries we expect type and name strings in a dict.
            elif (
                isinstance(entry, dict)
                and 'type' in entry
                and isinstance(entry['type'], str)
                and 'name' in entry
                and isinstance(entry['name'], str)
            ):
                entry_type = entry['type']
            else:
                raise TypeError(
                    'invalid soundtrack entry: '
                    + str(entry)
                    + ' (type '
                    + str(type(entry))
                    + ')'
                )
            if self.supports_soundtrack_entry_type(entry_type):
                return entry_type
            raise ValueError('invalid soundtrack entry:' + str(entry))
        except Exception:
            logging.exception('Error in get_soundtrack_entry_type.')
            return 'default'

    def get_soundtrack_entry_name(self, entry: Any) -> str:
        """Given a soundtrack entry, returns its name."""
        try:
            if entry is None:
                raise TypeError('entry is None')

            # Simple string denotes an iTunesPlaylist name (legacy entry).
            if isinstance(entry, str):
                return entry

            # For other entries we expect type and name strings in a dict.
            if (
                isinstance(entry, dict)
                and 'type' in entry
                and isinstance(entry['type'], str)
                and 'name' in entry
                and isinstance(entry['name'], str)
            ):
                return entry['name']
            raise ValueError('invalid soundtrack entry:' + str(entry))
        except Exception:
            logging.exception('Error in get_soundtrack_entry_name.')
            return 'default'

    def on_app_unsuspend(self) -> None:
        """Should be run when the app resumes from a suspended state."""
        if babase.is_os_playing_music():
            self.do_play_music(None)

    def do_play_music(
        self,
        musictype: MusicType | str | None,
        continuous: bool = False,
        mode: MusicPlayMode = MusicPlayMode.REGULAR,
        testsoundtrack: dict[str, Any] | None = None,
    ) -> None:
        """Plays the requested music type/mode.

        For most cases, setmusic() is the proper call to use, which itself
        calls this. Certain cases, however, such as soundtrack testing, may
        require calling this directly.
        """

        # We can be passed a MusicType or the string value corresponding
        # to one.
        if musictype is not None:
            try:
                musictype = MusicType(musictype)
            except ValueError:
                print(f"Invalid music type: '{musictype}'")
                musictype = MusicType.D_RUNNIN

        with babase.ContextRef.empty():
            # If they don't want to restart music and we're already
            # playing what's requested, we're done.
            if continuous and self.music_types[mode] is musictype:
                return
            self.music_types[mode] = musictype

            # If the OS tells us there's currently music playing,
            # all our operations default to playing nothing.
            if babase.is_os_playing_music():
                musictype = None

            # If we're not in the mode this music is being set for,
            # don't actually change what's playing.
            if mode != self._music_mode:
                return

            # Some platforms have a special music-player for things like iTunes
            # soundtracks, mp3s, etc. if this is the case, attempt to grab an
            # entry for this music-type, and if we have one, have the
            # music-player play it.  If not, we'll play game music ourself.
            if musictype is not None and self._music_player_type is not None:
                if testsoundtrack is not None:
                    soundtrack = testsoundtrack
                else:
                    soundtrack = self._get_user_soundtrack()
                entry = soundtrack.get(musictype.value)
            else:
                entry = None

            # Go through music-player.
            if entry is not None:
                self._play_music_player_music(entry)

            # Handle via internal music.
            else:
                self._play_internal_music(musictype)

    def _get_user_soundtrack(self) -> dict[str, Any]:
        """Return current user soundtrack or empty dict otherwise."""
        cfg = babase.app.config
        soundtrack: dict[str, Any] = {}
        soundtrackname = cfg.get('Soundtrack')
        if soundtrackname is not None and soundtrackname != '__default__':
            try:
                soundtrack = cfg.get('Soundtracks', {})[soundtrackname]
            except Exception as exc:
                print(f'Error looking up user soundtrack: {exc}')
                soundtrack = {}
        return soundtrack

    def _play_music_player_music(self, entry: Any) -> None:
        # Stop any existing internal music.
        # if self._music_node is not None:
        #     self._music_node.delete()
        #     self._music_node = None
        if self._playing_internal_music:
            bascenev1.set_internal_music(None)
            self._playing_internal_music = False

        # Do the thing.
        self.get_music_player().play(entry)

    def _play_internal_music(self, musictype: MusicType | None) -> None:
        # Stop any existing music-player playback.
        if self._music_player is not None:
            self._music_player.stop()

        # Stop any existing internal music.
        # if self._music_node:
        #     self._music_node.delete()
        #     self._music_node = None
        if self._playing_internal_music:
            bascenev1.set_internal_music(None)
            self._playing_internal_music = False

        # Start up new internal music.
        if musictype is not None:
            entry = ASSET_SOUNDTRACK_ENTRIES.get(musictype)
            if entry is None:
                print(f"Unknown music: '{musictype}'")
                entry = ASSET_SOUNDTRACK_ENTRIES[MusicType.D_RUNNIN]

            # self._music_node = _bascenev1.newnode(
            #     type='sound',
            #     attrs={
            #         'sound': _bascenev1.getsound(entry.assetname),
            #         'positional': False,
            #         'music': True,
            #         'volume': entry.volume * 5.0,
            #         'loop': entry.loop,
            #     },
            # )
            bascenev1.set_internal_music(
                babase.getsimplesound(entry.assetname),
                volume=entry.volume * 5.0,
                loop=entry.loop,
            )
            self._playing_internal_music = True


class MusicPlayer:
    """Wrangles soundtrack music playback.

    Music can be played either through the game itself
    or via a platform-specific external player.
    """

    def __init__(self) -> None:
        self._have_set_initial_volume = False
        self._entry_to_play: Any = None
        self._volume = 1.0
        self._actually_playing = False

    def select_entry(
        self,
        callback: Callable[[Any], None],
        current_entry: Any,
        selection_target_name: str,
    ) -> bauiv1.MainWindow:
        """Summons a UI to select a new soundtrack entry."""
        return self.on_select_entry(
            callback, current_entry, selection_target_name
        )

    def set_volume(self, volume: float) -> None:
        """Set player volume (value should be between 0 and 1)."""
        self._volume = volume
        self.on_set_volume(volume)
        self._update_play_state()

    def play(self, entry: Any) -> None:
        """Play provided entry."""
        if not self._have_set_initial_volume:
            self._volume = babase.app.config.resolve('Music Volume')
            self.on_set_volume(self._volume)
            self._have_set_initial_volume = True
        self._entry_to_play = copy.deepcopy(entry)

        # If we're currently *actually* playing something,
        # switch to the new thing.
        # Otherwise update state which will start us playing *only*
        # if proper (volume > 0, etc).
        if self._actually_playing:
            self.on_play(self._entry_to_play)
        else:
            self._update_play_state()

    def stop(self) -> None:
        """Stop any playback that is occurring."""
        self._entry_to_play = None
        self._update_play_state()

    def shutdown(self) -> None:
        """Shutdown music playback completely."""
        self.on_app_shutdown()

    def on_select_entry(
        self,
        callback: Callable[[Any], None],
        current_entry: Any,
        selection_target_name: str,
    ) -> bauiv1.MainWindow:
        """Present a GUI to select an entry.

        The callback should be called with a valid entry or None to
        signify that the default soundtrack should be used.."""
        raise NotImplementedError()

    # Subclasses should override the following:

    def on_set_volume(self, volume: float) -> None:
        """Called when the volume should be changed."""

    def on_play(self, entry: Any) -> None:
        """Called when a new song/playlist/etc should be played."""

    def on_stop(self) -> None:
        """Called when the music should stop."""

    def on_app_shutdown(self) -> None:
        """Called on final app shutdown."""

    def _update_play_state(self) -> None:
        # If we aren't playing, should be, and have positive volume, do so.
        if not self._actually_playing:
            if self._entry_to_play is not None and self._volume > 0.0:
                self.on_play(self._entry_to_play)
                self._actually_playing = True
        else:
            if self._entry_to_play is None or self._volume <= 0.0:
                self.on_stop()
                self._actually_playing = False


def do_play_music(*args: Any, **keywds: Any) -> None:
    """A passthrough used by the C++ layer."""
    assert babase.app.classic is not None
    babase.app.classic.music.do_play_music(*args, **keywds)

# PS. DO NOT USE THIS UNLESS YOU'RE EITHER
# A MASOCHIST OR YOU HAVE A NASA PC.
# i tested this earlier so it was easier
# to preload music, but even if it does work
# it makes the game straight up start lagging
# i'm only leaving this here incase there's a fix for it
def preload_all_music():
    import bascenev1 as bs

    squdalog.debug('[MusicPreloader] Starting preload...')

    total = 0
    failed = 0

    for mtype, entry in ASSET_SOUNDTRACK_ENTRIES.items():
        try:
            asset = entry.assetname

            squdalog.debug(f'[MusicPreloader] {mtype.value} -> {asset}')

            bs.getsound(asset)

            total += 1
        except Exception as e:
            failed += 1
            squdalog.debug(f'[MusicPreloader] FAILED {mtype.value}: {e}')

    squdalog.debug(f'[MusicPreloader] Done. Loaded={total} Failed={failed}')

