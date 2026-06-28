import babase as ba
import fromgoverhaul.mell_resources as mell
import threading
import urllib
import asyncio

class ServerPing:
    """Server pinger."""
    def __init__(self):
        """Instantiate a class.
        This will automatically start the thread."""
        self._bs_id: str | None = None
        self._status: dict = {}
        self._connection_success_logged = False
        self._connection_failed_logged = False
        self._current_thread: threading.Thread | None = None
        self._stop_event: threading.Event = threading.Event()
        ba.app.add_shutdown_task(self._stop_thread())

        if not ba.app.config.get('squda_disableping'):
            self.start()
    
    async def _stop_thread(self):
        self._stop_event.set()
        if self._current_thread:
            self._current_thread.join()

    def start(self):
        self._current_thread = threading.Thread(
            target=self._loop, daemon=True
        )
        self._current_thread.start()

    def _fetch_bs_id(self):
        import fromgoverhaul.mell_resources as mell
        self._bs_id = mell.get_unique_bs_id()

    def _build_payload(self) -> dict:
        return {
            'bs_id': self._bs_id,
            'account': bui.app.plus.get_v1_account_display_string(),
            'bs_version': ba.app.env.engine_version,
            'squda_version': mell.version,
            'squda_updatedate': mell.update_date,
            'squda_status': self._status,
        }

    def _get_local_player(self, activity) -> object | None:
        """Returns the local (non-remote) player from the activity, if any."""
        for plr in getattr(activity, 'players', []):
            if not plr._sessionplayer.inputdevice.is_remote_client:
                return plr
        return None

    def _update_status(self):
        activity = bs.get_foreground_host_activity()
        session = bs.get_foreground_host_session()
        player = self._get_local_player(activity)

        aname = (
            f'{activity.__class__.__module__}.{activity.__class__.__name__}'
            if activity else None
        )
        sname = (
            f'{session.__class__.__module__}.{session.__class__.__name__}'
            if session else None
        )

        pchar = getattr(player, 'character', None)
        pname = player.getname() if player else None
        profile = f'{pname} ({pchar})'

        self._status = {
            'activity_module': str(activity.__class__.__module__),
            'activity_class': str(activity.__class__.__name__),
            'activity_full': aname,
            'session_module': str(session.__class__.__module__),
            'session_class': str(session.__class__.__name__),
            'session_full': sname,
            'coop': isinstance(session, CoopSession),
            'score': getattr(activity, '_score', 0),
            'rank': getattr(activity, 'ultrameter._rank', str(None)),
            'hidden': False,
            'profile': profile,
            'online': bool(bs.get_connection_to_host_info_2()),
        }

    def _handle_response(self, response: dict):
        new_msgs = response.get('new_messages')
        if not new_msgs:
            return

        delay = 0.5
        delay_inc = 0.5
        for msg_id, msg_text in new_msgs.items():
            info = mell.get_info_from_id(msg_id)
            name = info.get('username', info.get('account_name', 'Unknown'))
            ba.pushcall(
                ba.Call(
                    ba.apptimer,
                    delay,
                    ba.Call(
                        mell.show_notification,
                        top_text=name,
                        bottom_text=msg_text,
                        icon=info.get('avatar', 'null'),
                    ),
                ),
                from_other_thread=True,
            )
            delay += delay_inc

    def _on_ping_success(self, response: dict):
        squdalog.debug(f'GOT RESPONSE: {response}')
        self._handle_response(response)
        if not self._connection_success_logged:
            squdalog.info('Connection to the BombSquda server established.')
            self._connection_success_logged = True
            self._connection_failed_logged = False

    def _on_ping_failure(self, e: Exception):
        squdalog.debug(f'Server connection failed: {e}')
        if not self._connection_failed_logged:
            squdalog.info('Connecting to the BombSquda server failed.')
            self._connection_success_logged = False
            self._connection_failed_logged = True

    def _ping(self):
        payload = self._build_payload()
        request = urllib.request.Request(
            f'{SERVER}/ping',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
        )
        squdalog.debug('PINGING SERVER')
        response = json.loads(
            urllib.request.urlopen(request, timeout=2).read().decode('utf-8')
        )
        return response

    def _loop(self):
        # Wait for the app to be active
        while not ba.app.mode._active:
            time.sleep(2)

        # Wait until  is ready
        while self._bs_id is None:
            self._fetch_bs_id()
            time.sleep(0.2)

        while not self._stop_event.is_set():
            bs.pushcall(self._update_status, from_other_thread=True)
            try:
                response = self._ping()
                self._on_ping_success(response)
                time.sleep(7)
            except Exception as e:
                self._on_ping_failure(e)
                time.sleep(5)