import bascenev1 as bs
from babase._logging import squdalog
import babase
import babase as ba
import baclassic as bsc
import _baclassic as _bsc
import os
import bauiv1 as bui
from .discordrp_handler import RichPresence
from typing import Sequence, override
from bascenev1._coopsession import CoopSession
import json
import urllib
import _babase
import sys
import traceback
import datetime
import bascenev1 as bs
import fromgoverhaul.mell_resources as mell
import threading, time
import uuid
from pathlib import Path
SERVER = mell.server
BS_ID = None
ID_FILE = 'bs_device_id.json'
current_activity = None

sst = _bsc.set_stress_testing
def setstresstestin(
    testing: bool, 
    player_count: int, 
    attract_mode: bool
):
    ba.app.stress_testing = testing
    return sst(
        testing, 
        player_count, 
        attract_mode
    )
_bsc.set_stress_testing = setstresstestin

class stupid_attribute_holder:
    # basically we're gonna tell this 
    # fucker "here hold these attributes"
    def __init__(self):
        self._connection_failed_logged = False
        self._connection_success_logged = False
    def __dict__(self):
        return {}

class Startup():
    platform = ba.app.classic.platform
    suffix = '.dds' if platform not in ['android'] else '.ktx'
    file = os.path.join(
        _babase.app.env.data_directory,
        'ba_data',
        'textures',
        'cowtato' + suffix,
    )
    file = Path(file)
    if not file.is_file():
        os._exit(1)
    # alright we're ready to do startup stuff
    squdalog.info(f'bombsquda v{mell.version}, updated as of {mell.update_date}')
    # very important stuff that needs to be set on startup
    _last_error_time = None
    _recent_error = False
    # check if values exist
    global cfg
    cfg = bui.app.config
    # made by temp in the 'bombarmy' discussion in the discord server.
    config = bs.app.config
    # disable some default options on android
    if platform in ['android']:
        disable_wiggledance = True
    else:
        disable_wiggledance = False
    conflist = {
        "squda_parryalways": False,
        "squda_skipintro": False,
        "squda_chaosemeralds": True,
        "squda_disablemortal": False,
        "squda_richpresence": False,
        "squda_spazfuckedup": False,
        "squda_spazhardmode": False,
        "squda_unlockedmel": False,
        "squda_noisepolution": False,
        "squda_canopencredits": False,
        "squda_dontdomarioman": False,
        "squda_dontshutdown": False,
        "squda_enablemeter": False,
        "squda_gamblingmode": False,
        "squda_speedrunner": False,
        "squda_nosugarcoats": False,
        "squda_playersfirsttime": True,
        "squda_isplayingmusic": False,
        "squda_customfont": False,
        "squda_debugprints": False,
        "squda_blood": True,
        "squda_timesattracted": 1,
        "squda_timeserrored": 0,
        "squda_parrytype": 2,
        "squda_spaztix": 500,
        "squda_spaztokens": 5,
        "squda_showerrors": False,
        "squda_foxyjumpscare": False,
        "squda_pausemusic": True,
        "squda_noonline": False,
        "squda_randomgrace": False,
        "squda_nowiggledance": disable_wiggledance,
        "squda_entitychance": 0.1,
        "squda_botnames": True,
        "squda_favchar": None,
        "squda_ch1name": "NEWBIE",
        "squda_ch2name": "KRIS",
        "squda_ch3name": "SNAKESHADOW",
        "squda_ch4name": "NOOB",
        "squda_menumusic": 'None',
        "squda_storeowned": {},
        "squda_achievements": {},
        'squda_disable_online_music': False,
    }
    # "setdefault" to create config settings
    # won't affect already existing ones.
    for k,v in conflist.items():
        config.setdefault(k, v)
    config.apply_and_commit()
    squdalog.debug('set default config stuff applied!')
    try:
        squdalog.debug('attempting to check config')
        cfg['squda_playersfirsttime']
    except Exception as e:
        logging.critical(
            (
                'An error occured; default config values couldn\'t'
                'be set. Please contact @mellboii on Discord...'
                '\nError: {e}' 
            )
        )

    if babase.app.config.get("squda_richpresence", True):
        try:
            babase.apptimer(1.8, RichPresence)
        except Exception as e:
            print(f'Unable to start rich presence: {e}')
    bui.app.config['squda_isplayingmusic'] = False
    bui.app.config['squda_timesattracted'] = 0
    squdalog.debug('config stuff is done')
    
    owned = ba.app.config.get('squda_storeowned')
    if owned.get('characters.baller', False):
        def do_it():
            name = 'Baller'
            key = 'characters.baller'
            price = mell.store_prices[key]
            owned = ba.app.config.get('squda_storeowned')
            owned[key] = False
            ba.app.config.commit()
            bottom_lstr = bs.Lstr(
                resource='notifications.removalRefundText',
                subs=[
                    ('${COUNT}', str(price)),
                    ('${NAME}', name),
                ]
            ).evaluate()
            top_lstr = bs.Lstr(resource='notifications.characterRemovalRefundTitle').evaluate()
            mell.show_notification(
                top_text=top_lstr,
                bottom_text=bottom_lstr,
                icon='spaztickets',
            )
            with bs.get_foreground_host_activity().context:
                mell.add_spaz(amount=price)
        ba.apptimer(4, do_it)
        
    def auto_module_import():
        """
        Automatically imports modules,
        and makes them usable to the console.
        (could possibly slow down loading, and if so
        just disable the callable below)
        """
        # import le modules...
        import sys
        import babase as ba
        import bascenev1 as bs
        import bauiv1 as bui
        # and install them to the console
        globals = sys.modules['__main__'].__dict__
        globals['ba'] = ba
        globals['bs'] = bs
        globals['bui'] = bui
        globals['ga'] = bs.getactivity
        globals['gp'] = bs.getplayers
        globals['gs'] = bs.getsession
        globals['mell'] = mell
        squdalog.debug('console globals done!')
    # call it
    auto_module_import()
    
    def my_global_exception_hook(exc_type, exc_value, exc_traceback):
        """
        custom ass exception hook
        """
        global _last_error_time, _recent_error
        
        # don't "hide" systemexit and keyboardinterrupt
        # keyword "hide" because i doubt this does anything
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # convert a error to text
        error_text = ''.join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        
        _last_error_time = datetime.datetime.now()
        _recent_error = True
        # Log it somewhere visible
        print(error_text)
        if not ba.app.config.get("squda_showerrors"):
            return
        bs.broadcastmessage(
            f"An error occured:\n{error_text}", 
            color=(1, 0, 0)
        )
        try:
            activity = bs.get_foreground_host_activity()
        except:
            activity = None
        if activity:
            with activity.context:
                bs.getsound('dev_epicfail').play()
        else:
            bui.getsound('dev_epicfail').play()
        
    # Install the hook
    sys.excepthook = my_global_exception_hook
    squdalog.debug('global exception hook is ready!')
    # define our thread loop
    def loop():
        global status
        loopt = stupid_attribute_holder()
        status = {}
        def set_bs_id():
            import fromgoverhaul.mell_resources as mell
            global BS_ID
            BS_ID = mell.get_unique_bs_id()
        
        while not getattr(ba.app.mode, '_active', False):
            time.sleep(2)

        while BS_ID is None:
            set_bs_id()
            time.sleep(0.2)  # wait until ID is ready
        
        # while we exist, keep pinging the server
        while True:
            def update_status():
                global status
                activity = bs.get_foreground_host_activity()
                session = bs.get_foreground_host_session()
                player = None

                aname = (
                    f"{activity.__class__.__module__}."
                    f"{activity.__class__.__name__}"
                    if activity else None
                )
                players = getattr(activity, 'players', [])
                for plr in players:
                    inputdevice = plr._sessionplayer.inputdevice
                    if not inputdevice.is_remote_client:
                        player = plr
                        break
                pchar = getattr(player, 'character', None)
                pname = getattr(player, 'getname()', None)
                profile = f'{pname} ({pchar})'

                sname = (
                    f"{session.__class__.__module__}."
                    f"{session.__class__.__name__}"
                    if session else None
                )
                coop = isinstance(session, CoopSession)
                score = getattr(activity, '_score', 0)
                rank = getattr(activity, 'ultrameter._rank', str(None))
                share_status = True
                if share_status:
                    status = {
                        'activity_module': str(activity.__class__.__module__),
                        'activity_class': str(activity.__class__.__name__),
                        'activity_full': aname,
                        'session_module': str(session.__class__.__module__),
                        'session_class': str(session.__class__.__name__),
                        'session_full': sname,
                        'coop': coop,
                        'score': score,
                        'rank': rank,
                        'hidden': False,
                        'profile': profile,
                        'online': True if bs.get_connection_to_host_info_2() else False,
                    }
                else:
                    status = {
                        'hidden': True,
                    }
            # update the status
            bs.pushcall(update_status, from_other_thread=True)
            data = {
                "bs_id": BS_ID,
                "account": bui.app.plus.get_v1_account_display_string(),
                "device_id": BS_ID.split(":")[-1],
                "bs_version": ba.app.env.engine_version,
                "squda_version": mell.version,
                "squda_updatedate": mell.update_date,
                "squda_status": status,
            }
            # make a request to the server with the data (as dumped json)
            request = urllib.request.Request(
                f"{SERVER}/ping",
                data=json.dumps(data).encode('utf-8'),
                headers={
                    "Content-Type": "application/json"
                },
            )
            squdalog.debug('PINGING SERVER')
            # now try opening the response
            try:
                open = urllib.request.urlopen(request, timeout=2)
                response = json.loads(open.read().decode('utf-8'))
                new_msgs = response.get('new_messages')
                squdalog.debug(f'GOT RESPONSE: {response}')
                if new_msgs:
                    delay_inc = 0.5
                    delay = 0.5
                    for msg in new_msgs.keys():
                        info = mell.get_info_from_id(msg)
                        name = info.get('username', info.get('account_name', 'Unknown'))
                        ba.pushcall(
                            ba.Call(ba.apptimer,
                                delay, 
                                ba.Call(
                                    mell.show_notification,
                                    top_text=name,
                                    bottom_text=new_msgs[msg],
                                    icon=info.get('avatar', 'null'),
                                ),
                            ),
                            from_other_thread=True
                        )
                        delay += delay_inc
                    
                if not loopt._connection_success_logged:
                    squdalog.info('Connection to the BombSquda server established successfully.')
                    loopt._connection_success_logged = True
                    loopt._connection_failed_logged = False
                time.sleep(7)
            # exception likely means no connection could be made
            except Exception as e:
                squdalog.debug(f"Server connection failed: {e}")
                time.sleep(5)
                if not loopt._connection_failed_logged:
                    squdalog.info('Connecting to the BombSquda server failed.')
                    loopt._connection_success_logged = False
                    loopt._connection_failed_logged = True
                    
    # ONLY run the thread if online is enabled
    if not ba.app.config.get('squda_noonline'):
        threading.Thread(target=loop, daemon=True).start()
    squdalog.debug('everything should be good to go :3')
    




