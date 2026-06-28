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
from .server_ping import ServerPing
import threading, time
import uuid
import ctypes
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
csh = bs.camerashake
def camerashake(intensity: float = 1.0):
    # shake window too!!!!
    mell.shake_window(intensity=intensity * 10)
    return csh(intensity)
bs.camerashake = camerashake

class Startup():
    platform = ba.app.classic.platform
    # suffix is dds if we're not on android
    suffix = '.dds' if platform not in ['android'] else '.ktx'
    # check if the 'kamikaze' file exists,
    # and if it doesn't exit with a error code
    kamikaze = os.path.join(
        _babase.app.env.data_directory,
        'ba_data',
        'textures',
        'cowtato' + suffix,
    )
    kamikaze = Path(kamikaze)
    if not kamikaze.is_file():
        os._exit(2)
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
        "squda_disableping": False,
        "squda_randomgrace": False,
        "squda_nowiggledance": False,
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
        'squda_border_res': [1433.6, 806.4],
        'squda_border_style': 'basic',
        'squda_border_toggle': True,
        'squda_ultrameter': 'normal',
        'squda_coop_levels_beaten_hardmode': {},
        'squda_disablewindowshake': True,
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
    # try getting user32, but if
    # it fails assume we're on multi-platform
    # and just default
    try:
        user32 = ctypes.windll.user32
    except:
        user32 = None
    title = 'BombSquad'    
    if user32:
        hwnd = user32.FindWindowW(None, title)
    else:
        hwnd = None
    ba.app.window_hwnd = hwnd
    # by default, we rename the window too :3
    mell.rename_window('BombSquda')

    if babase.app.config.get("squda_richpresence", True):
        try:
            babase.apptimer(1.8, RichPresence)
        except Exception as e:
            print(f'Unable to start rich presence: {e}')
    bui.app.config['squda_isplayingmusic'] = False
    bui.app.config['squda_timesattracted'] = 0
    squdalog.debug('config stuff is done')
    
    owned = ba.app.config.get('squda_storeowned')
    removed_chars = {
        'characters.baller': 'Baller',
    }
    time = 4
    # for every character that got removed,
    # refund their price
    for char in removed_chars.keys():
        if owned.get(char, False):
            def do_it():
                # config stuff
                name = removed_chars[char]
                key = char
                price = mell.store_prices[key]
                owned = ba.app.config.get('squda_storeowned')
                owned[key] = False
                ba.app.config.commit()
                # get text
                bottom_lstr = bs.Lstr(
                    resource='notifications.removalRefundText',
                    subs=[
                        ('${COUNT}', str(price)),
                        ('${NAME}', name),
                    ]
                ).evaluate()
                top_lstr = bs.Lstr(resource='notifications.characterRemovalRefundTitle').evaluate()
                # show notification
                mell.show_notification(
                    top_text=top_lstr,
                    bottom_text=bottom_lstr,
                    icon='spaztickets',
                )
                # refund them the amount they paid
                mell.add_spaz(amount=price, notif_type='screen')
            ba.apptimer(time, do_it)
            time += 1
        
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
    
    ServerPing()
    squdalog.debug('everything should be good to go :3')
    




