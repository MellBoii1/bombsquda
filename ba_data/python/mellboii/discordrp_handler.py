"""Handles rich presence for Discord."""
# originated from rich presence, 
# but i kinda rewrote it

import time
import threading
import asyncio
from mellboii.discordrp_folder import Presence
import babase
import bascenev1 as bs
from bascenev1lib.mainmenu import MainMenuActivity
from bascenev1._activitytypes import JoinActivity
from bascenev1._gameactivity import GameActivity
from babase._logging import squdalog
import mellboii.mell_resources as melly
import bauiv1 as bui

portal_id = "1419400467707859136"

maps: dict = {
    'Hockey Stadium': 'hockey_stadium', 
    'Football Stadium': 'football_stadium', 
    'Bridgit': 'bridgit', 
    'Big G': 'big_g', 
    'Roundabout': 'roundabout',
    'Monkey Face': 'monkey_face', 
    'Zigzag': 'zigzag', 
    'The Pad': 'the_pad', 
    'Doom Shroom': 'doom_shroom', 
    'Lake Frigid': 'lake_fridgid', 
    'Tip Top': 'tiptop', 
    'Crag Castle': 'crag_castle',
    'Tower D': 'tower_d', 
    'Happy Thoughts': 'happy_thoughts', 
    'Step Right Up': 'step_right_up', 
    'Courtyard': 'courtyard', 
    'Rampage': 'rampage', 
    'Nintendo DS': 'nintendoDS', 
    'SNES Battle Course 1': 'snes', 
    'Space': 'space', 
}

class RichPresence:
    """A class that handles Discord Rich Presence."""
    def __init__(self):           
        self.presence = Presence(portal_id)
        self.mode = 'menu'
        self._r = 'discordRPC'
        self.data = {}
        self._stop_event = threading.Event()
        self.current_thread = None
        self.current_time = 0
        self.set_time('app')
        self.map = None
        self.last_mode = None
        self.start()
        babase.app.add_shutdown_task(self._stop_thread())
    
    async def _stop_thread(self):
        self._stop_event.set()
        if self.current_thread:
            self.current_thread.join()
    
    def set_time(self, type: str):
        if type not in ['app', 'game']:
            raise TypeError('Specified time wasn\'t app or game.')
        if type == 'app':
            self.current_time = int(time.time())
        elif type == 'game':
            self.current_time = int(time.time() - bs.time())
    
    def _rpc_thread(self):
        # loop while we shouldn't
        # be dead
        while not self._stop_event.is_set():
            # helper for pushcall
            def push(call):
                bs.pushcall(
                    call,
                    from_other_thread=True,
                    other_thread_use_fg_context=True,
                )
            # update everythin
            push(self.check)
            push(self.update)
            # sleep just in case
            time.sleep(0.1)
            # then, set the presence's activity
            self.presence.set(self.data)
            # delay the next loop
            time.sleep(1.3)

    def start(self):
        """Starts the thread. Yup."""
        self.current_thread = threading.Thread(
            target=self._rpc_thread, daemon=True
        )
        self.current_thread.start()

    def _lstr(self, resource: str, **subs: str) -> str:
        return bs.Lstr(
            resource=f'{self._r}.{resource}',
            subs=[
                ('$' + '{' + str(k) + '}', v) for k, v in subs.items() # recreate the ${SUB} prefix
            ]
        ).evaluate()

    def _build_data(
        self,
        details: str,
        state: str,
        large_image: str,
        large_text: str = '',
        small_image: str | None = None,
        small_text: str = '',
        party: dict | None = None,
    ) -> dict:
        data = {
            'details': details,
            'state': state,
            'assets': {
                'large_image': large_image,
                'large_text': large_text,
                **(({'small_image': small_image, 'small_text': small_text})
                   if small_image else {}),
            },
            'timestamps': {'start': self.current_time},
        }
        if party is not None:
            data['party'] = party
        return data

    def _format_players(self, players: list) -> str:
        """Returns a state string describing the current players."""
        if len(players) > 1:
            names = [f'{p.getname()} ({p.character})' for p in players]
            plist = ', '.join(names) or self._lstr('noOne')
            return self._lstr('coopMultiplayerText', LIST=plist)
        else:
            name = players[0].getname() if players else self._lstr('noOne')
            char = players[0].character if players else self._lstr('noPlayers')
            return self._lstr('coopSingleplayerText', NAME=name, CHAR=char)

    def _session_info(self, fore_sesh) -> tuple[str, str | None]:
        """Returns (display name, image key) for the current session type."""
        session_types = {
            bs.FreeForAllSession: ('FFA',   'ffa'),
            bs.CoopSession:       ('Co-op', 'coop'),
            bs.DualTeamSession:   ('Teams', 'teams'),
        }
        for sesh_type, (name, image) in session_types.items():
            if isinstance(fore_sesh, sesh_type):
                return name, image
        return '???', None

    def _data_menu(self, **_) -> dict:
        window_r = babase.app.ui_v1.get_main_window()._r
        lstr = babase.Lstr(resource=f'{window_r}.rpcText')
        details = (
            self._lstr('menuAFKText')
            if self.mode == 'menu_idle'
            else self._lstr('menuText')
        )
        return self._build_data(
            details=details,
            state=lstr.evaluate(),
            large_image='logo',
            large_text=f'BombSquda v{melly.version} (In-dev)',
        )

    def _data_gameplay(self, fore_sesh, sesh_text, sesh_image) -> dict:
        activity = bs.get_foreground_host_activity()
        players = activity.players

        map_image = maps.get(self.map, 'unkmap')
        small_text = sesh_text
        party = None

        if isinstance(fore_sesh, bs.CoopSession):
            state = self._format_players(players)
            small_text += f' ({fore_sesh.campaign_level_name})'
            score = getattr(activity, '_score', None)
            meter = getattr(activity, 'ultrameter', None)
            rank = getattr(meter, '_rank', None)
            details = self._lstr('coopScoreRankText', SCORE=str(score), RANK=str(rank))
        else:
            state = bs.Lstr(resource='partyText').evaluate()
            party = {'id': '00', 'size': (max(0, len(activity.players)), 8)}
            details = self._lstr('activityPlaying', ACTIVITY=activity.name)

        return self._build_data(
            details=details,
            state=state,
            large_image=map_image,
            large_text=self.map,
            small_image=sesh_image,
            small_text=small_text,
            party=party,
        )

    def _data_lobby(self, fore_sesh, sesh_text, sesh_image) -> dict:
        roster_size = max(1, len(bs.get_game_roster()))
        party_size = (roster_size, bs.get_public_party_max_size())
        return self._build_data(
            details=self._lstr('charSelectText'),
            state='Party',
            large_image='background',
            large_text=self._lstr('lobbyText'),
            small_image=sesh_image,
            small_text=sesh_text,
            party={'id': '00', 'size': party_size},
        )

    def _data_online(self, **_) -> dict:
        try:
            name = bs.get_connection_to_host_info_2().name
        except Exception:
            name = self._lstr('partyNameFallback')
        return self._build_data(
            details=self._lstr('playingOnline', PARTY=name),
            state='Party',
            large_image='online',
            large_text=self._lstr('playingOnlineSimple'),
            party={'id': '00', 'size': (max(1, len(bs.get_game_roster())), 8)},
        )

    def _data_replay(self, **_) -> dict:
        return self._build_data(
            details=self._lstr('watchingReplay'),
            state='Party',
            large_image='replay',
            large_text=self._lstr('replayText'),
            party={'id': '00', 'size': (max(1, len(bs.get_game_roster())), 8)},
        )

    def update(self):
        try:
            fore_sesh = bs.get_foreground_host_session()
            sesh_text, sesh_image = self._session_info(fore_sesh)

            mode_handlers = {
                'menu':      self._data_menu,
                'menu_idle': self._data_menu,
                'gameplay':  self._data_gameplay,
                'lobby':     self._data_lobby,
                'online':    self._data_online,
                'replay':    self._data_replay,
            }

            handler = mode_handlers.get(self.mode)
            if handler:
                self.data = handler(
                    fore_sesh=fore_sesh,
                    sesh_text=sesh_text,
                    sesh_image=sesh_image,
                )
        except Exception as e:
            squdalog.debug(f'Error updating rich presence. ({e})')

    def check(self):
        try:
            map_name = bs.get_foreground_host_activity().map.name
        except Exception:
            map_name = None
        
        if map_name:
            self.map = map_name
        
        time_pref = 'app'
        fg = bs.get_foreground_host_activity()

        if isinstance(fg, JoinActivity):
            self.mode, self.last_mode, time_pref = 'lobby', 'lobby', 'app'
        elif isinstance(fg, MainMenuActivity):
            self.mode, self.last_mode, time_pref = 'menu', 'menu', 'app'
        elif isinstance(fg, GameActivity):
            self.mode, self.last_mode, time_pref = 'gameplay', 'gameplay', 'game'
        elif bui.get_input_idle_time() >= 30 and self.mode == 'menu':
            self.mode, self.last_mode, time_pref = 'menu_idle', 'menu', 'app'
        elif bui.get_input_idle_time() <= 30 and self.mode == 'menu_idle':
            self.mode, self.last_mode = 'menu', 'menu_idle'
        elif bs.get_connection_to_host_info_2():
            self.mode, self.last_mode, time_pref = 'online', 'online', 'app'
        elif bs.is_in_replay() and self.last_mode != 'replay':
            self.mode, self.last_mode, time_pref = 'replay', 'replay', 'game'

        if self.mode != self.last_mode:
            self.set_time(time_pref)


