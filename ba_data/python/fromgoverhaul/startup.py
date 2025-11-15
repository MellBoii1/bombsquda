import bascenev1 as bs
import babase
import os
import bauiv1 as bui
from .discordrp_handler import RichPresence
import threading
import json
import urllib.request
import _babase

class Startup():
    # very important stuff that needs to be set on startup
    
    # check if (not goverhaul, bombsquda) values exists in the config *** THX VISHUU!!! ***
    #pseudo-code
    global cfg
    cfg = bui.app.config
    # made by temp in the 'bombarmy' discussion in the discord server.
    config = bs.app.config
    conflist = {
    "parryalways": False,
    "richpresence": True,
    "spazfuckedup": False,
    "spazhardmode": False,
    "unlockedmel": False,
    "noisepolution": False,
    "canopencredits": False,
    "dontdomarioman": False,
    "dontshutdown": False,
    "enablemeter": False,
    "gamblingmode": False,
    "playersfirsttime": True,
    "isplayingmusic": False,
    "timesattracted": 1,
    }
    # "setdefault" to create config settings
    # won't affect already existing ones.
    for k,v in conflist.items():
        config.setdefault(k, v)
    # save changes
    cfg['isbombsqudaorsomething'] = None
    config.apply_and_commit()
    try:
        cfg['playersfirsttime']
    except:
        print('incredibly bad fuckin error.')
        print('something went bad in fromgoverhaul\'s startup, and we couldn\t add config stuff')

    if babase.app.classic.platform not in ['android', 'mac']:
        if babase.app.config.get("richpresence", True):
            try:
                babase.apptimer(1.3, RichPresence)
            except Exception as e:
                print(f'Enable to start rich presence: {e}')
    bui.app.config['isplayingmusic'] = False
    bui.app.config['timesattracted'] = 0




