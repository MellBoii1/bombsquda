""" 
Resources that should be easier to edit in a shared code,
like lists, dicts, server address, game version, and some useful functions.
"""

screams = ['screams/scream' + str(i + 1) + '' for i in range(15)]
server = "https://bombsquda.tailc76b25.ts.net/"
version = '2.5'
update_date = '6/1/2026'
from babase._logging import squdalog
# A dict for each store character that stores their price.
# They are hardcoded to be spaz tickets only, for now.
store_prices = {
    'characters.susie': 620,
    'characters.ralsei': 550,
    'characters.rayman': 450,
    #'characters.kris': 600,
    'characters.rk': 1450,
    #'characters.noob': 1200,
    'characters.mell': 4300,
    'characters.sparkii': 2500,
    #'characters.gummyboiyt': 750,
    'characters.rayman': 670,
    'characters.bowser': 1150,
    'characters.orangecap': 850,
    'characters.noise': 1200,
    'characters.taobao': 800,
    'characters.mario': 800,
    'characters.sonic': 950,
    'characters.kirby': 860,
    'characters.tails': 960,
    'characters.buddie': 1100,
    'characters.rem': 1400,
    'characters.grace': 860,
    'characters.baller': 350,
    'characters.homer': 870,
    'characters.ogspaz': 700,
    'characters.kookoo': 1300,
    'characters.fancypants': 1100,
    'characters.isaac': 800,
}
# A dict for store character names (basically coded 
# names like characters.charname) that correspond to a spazappearance name.
# This is used to simplify the system for getting whether we own a character.
appearance_dict = {
    'characters.susie': 'Susie',
    'characters.rayman': 'Rayman',
    #'characters.kris': 'Kris',
    'characters.ralsei': 'Ralsei',
    'characters.rk': 'Roaring Knight',
    #'characters.noob': 'Noob',
    'characters.mell': 'Mell',
    'characters.sparkii': 'Sparkii',
    #'characters.gummyboiyt': 'GummyBoiYT',
    'characters.rayman': 'Rayman',
    'characters.bowser': 'Bowser',
    'characters.orangecap': 'Orangecap',
    'characters.noise': 'The Noise',
    'characters.taobao': 'SqudaTaobaoMascot',
    'characters.mario': 'SM64 Mario',
    'characters.sonic': 'Sonic',
    'characters.kirby': 'Kirby',
    'characters.tails': 'Tails',
    'characters.buddie': 'Buddie',
    'characters.rem': 'Rem',
    'characters.grace': 'John Grace',
    'characters.homer': 'Homer',
    'characters.ogspaz': 'OG Spaz',
    # Shouldn't be on store or etc but still use same system
    'characters.ire': 'Ire',
    'characters.dozer': 'Dozer',
    # ---
    'characters.kookoo': 'Kookoo',
    'characters.fancypants': 'Fancy Pants',
    'characters.isaac': 'Isaac',
}
# A dict we use in character select, profile edit, 
# etc... to swapout vanilla or Gummy's Overhaul characters for ours.
# (this is so we don't always get spaz, just to have a little 
# variety even if we keep changing characters and modpacks)
swapout_dict = {
    'Zoe': 'Kris',
    'Kronk': 'Susie',
    'Orange Cap': 'Orangecap',
    'Jack Morgan': 'John Grace',
    'Snake Shadow': 'GummyBoiYT',
    'Agent Johnson': 'Homer',
    'Agent Johnson': 'Homer',
    'mell': 'Mell',
    'Mel': 'Mell',
    'B-9000': 'Roaring Knight',
    'Penny': 'Ire',
    'Space Guy': 'SM64 Mario',
}

def get_festivity():
    """Gets the current festivity 
    (april fools, christmas, etc)"""
    from datetime import date
    import bauiv1 as bui
    plus = bui.app.plus
    today = date.today()
    day = today.day
    month = today.month
    christmas = month == 12 and day == 25
    aprilfools = (
        month == 4 and day == 1
        or bui.app.config.get('squda_forceapril', False)
    )
    easter = plus.get_v1_account_misc_read_val('easter', False)
    if aprilfools:
        return "april_fools"
    if christmas:
        return "christmas"
    if easter:
        return "easter"

def translate_char_name(name: str):
    import babase
    return babase.Lstr(
        translate=('characterNames', name)
    ).evaluate()

def lstr_char_name(name: str):
    import babase
    return babase.Lstr(
        translate=('characterNames', name)
    )

def clamp(num, min_val, max_val):
    return max(min(num, max_val), min_val)

def add_spaz(
    amount: int | float = 50,
    currency: str = 'tix',
    text_pos=None,
    notif_type: str = 'screen',
):
    """Adds a specific amount of tickets or tokens
    to our count and also shows it onscreen/ingame."""
    import bascenev1 as bs
    import babase as ba
    # gotta leave here otherwise doesn't work
    CURRENCIES = {
        'tix': {
            'config_key': 'squda_spaztix',
            'glyph': ba.SpecialChar.OUYA_BUTTON_Y,
            'resource': 'spazTickets',
        },
        'tokens': {
            'config_key': 'squda_spaztokens',
            'glyph': ba.SpecialChar.OUYA_BUTTON_A,
            'resource': 'spazTokens',
        },
    }

    # validate whether said currency is in ours
    if currency not in CURRENCIES:
        raise TypeError(
            f"{currency} is invalid. Allowed: {list(CURRENCIES.keys())}"
        )

    data = CURRENCIES[currency]

    # Safely update config
    config_key = data['config_key']
    ba.app.config[config_key] = ba.app.config.get(config_key, 0) + amount
    ba.app.config.apply_and_commit()

    # Shared values
    glyph = ba.charstr(data['glyph'])
    activity = bs.get_foreground_host_activity()
    prefix = '+' if amount > 0 else '-'
    sound = 'gainCur'

    # popup messages
    if notif_type == 'popup':
        # raise error if no activity
        if not (text_pos and activity):
            raise TypeError("Popup requires text_pos and active activity")

        with activity.context:
            from bascenev1lib.actor.popuptext import PopupText

            PopupText(
                f'{prefix}{amount}{glyph}',
                position=text_pos,
                color=(0.643, 0.4, 0.961),
                scale=1.4,
                lifespan=3.5,
            ).autoretain()

            bs.getsound(sound).play(volume=1.7, position=text_pos)

    # screen messages
    elif notif_type == 'screen':
        display = f"{glyph} {bs.Lstr(resource=data['resource']).evaluate()}"

        bs.broadcastmessage(
            bs.Lstr(
                resource='wonCustomCurrency',
                subs=[
                    ('${AMOUNT}', str(amount)),
                    ('${CURRENCY}', display),
                ],
            )
        )
        try:
            bs.getsound(sound).play(volume=2.0)
        except ba._error.ContextError:
            bui.getsound(sound).play(volume=2.0)
    # not in valid types
    else:
        raise TypeError(
            f"{notif_type} invalid. Allowed: ['screen', 'popup']"
        )

def announcer_say(voiceline: str):
    import bascenev1 as bs
    import random
    thisannouncer = 'announcer'
    volume = 1.0
    # make a function for getting sound that uses the
    # path to our voicelines
    def gs(sound: str):
        return bs.getsound(f'voicelines/{thisannouncer}/{sound}')
    # voiceline should correlate to something here
    sound_dict = {
        # situations
        'overtime': gs('overtime'),
        'homerun': gs('homerun'),
        'out_park': gs('out_park'),
        'winneris': gs('winneris'),
        'youwon': gs('youwon'),
        'hurryup': gs('hurryup'),
        'game': gs('game'),
        'draw': gs('draw'),
        'team': gs('team'),
        # team colors
        'purple': gs('purple'),
        'orange': gs('orange'),
        'green': gs('green'),
        'blue': gs('blue'),
        'red': gs('red'),
        'yellow': gs('yellow'),
        'white': gs('white'),
        'black': gs('black'),
        # numbers
        '0': gs('zero'),
        '1': gs('one'),
        '2': gs('two'),
        '3': gs('three'),
        '4': gs('four'),
        # characters
        'Susie': gs('susie'),
        'Rayman': gs('rayman'),
        'Kris': gs('kris'),
        'Ralsei': gs('ralsei'),
        'Roaring Knight': gs('knight'),
        'Noob': gs('noob'),
        'Mell': gs('mell'),
        'GummyBoiYT': gs('snakeling'),
        'Rayman': gs('rayman'),
        'Bowser': gs('bowser'),
        'Orangecap': gs('ocap'),
        'The Noise': gs('noise'),
        'SqudaTaobaoMascot': gs('taobao'),
        'SM64 Mario': gs('mario'),
        'Sonic': gs('sonic'),
        'Kirby': gs('kirby'),
        'Tails': gs('tails'),
        'Buddie': gs('buddie'),
        'Rem': gs('rem'),
        'John Grace': gs('john'),
        'Homer': gs('homer'),
        'OG Spaz': gs('ogspaz'),
        'Ire': gs('ire'),
        'Dozer': gs('dozer'),
        'Spaz': gs('spaz'),
    }
    # get the voiceline sound equivalent and play it
    if voiceline in sound_dict:
        choice = sound_dict[voiceline]
        # if its a list, we can pick a random sound of it
        if isinstance(choice, list):
            random.choice(choice).play(volume=volume)
        else:
            choice.play(volume=volume)
    else:
        # don't say anything if it's 
        # us preloading sounds
        if voiceline == 'PRELOADPROCESS':
            return
        gs('unknown').play(volume=volume)
        squdalog.info(f'ANNOUNCER VOICELINE {voiceline} IS UNKNOWN')

def hex_to_color(hex_color: str) -> tuple:
    # Remove the '#' from the string if provided.
    if hex_color.startswith('#'):
        hex_color = hex_color.lstrip('#')
    # Check if this has a valid length.
    hexlength = len(hex_color)
    if not hexlength in [6, 8]:
        raise ValueError(f'Invalid HEX color provided: "{hex_color}"')

    # Convert the hex bytes to their true byte form.
    ar, ag, ab, aa = (
        (int.from_bytes(bytes.fromhex(hex_color[0:2]))),
        (int.from_bytes(bytes.fromhex(hex_color[2:4]))),
        (int.from_bytes(bytes.fromhex(hex_color[4:6]))),
        (
            (int.from_bytes(bytes.fromhex(hex_color[6:8])))
            if hexlength == 8
            else None
        ),
    )
    # Divide all numbers by 255 and return.
    nr, ng, nb, na = (
        x / 255 if x is not None else None for x in (ar, ag, ab, aa)
    )
    return (nr, ng, nb, na) if aa is not None else (nr, ng, nb)

def award_hardmode_ach():
    import bascenev1 as bs
    hardcamp = bs.app.classic.getcampaign('Default')
    easycamp = bs.app.classic.getcampaign('Easy')
    beaten = bs.app.config.get('squda_coop_levels_beaten_hardmode', {})
    # if all levels in the hard campaign were beaten
    # in hardmode, grant it's achievement
    if all(('Default:' + level.name) in beaten for level in hardcamp.levels):
        bs.app.classic.ach.award_local_achievement(
            'HardmodeHardCampaign'
        )
    # do the same for easy campaign
    if all(('Easy:' + level.name) in beaten for level in easycamp.levels):
        bs.app.classic.ach.award_local_achievement(
            'HardmodeEasyCampaign'
        )

def get_unique_bs_id():
    """Gets the player's unique BombSquda ID.
    If it exists in the config, just returns that.
    Otherwise, it generates one, saves it, then deletes it."""
    import babase as ba
    if ba.app.config.get('squda_accountid'):
        return ba.app.config.get('squda_accountid')
    def get_device_id():
        if os.path.exists(ID_FILE):
            return json.load(open(ID_FILE))["id"]

        new_id = str(uuid.uuid4())
        json.dump({"id": new_id}, open(ID_FILE, "w"))
        return new_id
        
    def clean_account_name(s: str) -> str:
        return "".join(c for c in s if not (0xE000 <= ord(c) <= 0xF8FF))
        
    display = bui.app.plus.get_v1_account_display_string()
    name = clean_account_name(display)
    full_str = f"{name}:{get_device_id()}"
    ba.app.config['squda_accountid'] = full_str
    if os.path.exists(ID_FILE):
        os.remove(ID_FILE)
    return full_str
    
def withdraw_currency(amount: int, type: str):
    """Withdraw a specific amount with our ID from the server.
    WARNING: You must do checks yourself, otherwise amount can go negative."""
    import urllib
    import json
    id = get_unique_bs_id()
    data = {
        "bs_id": id,
        "amount": amount,
        "type": type,
    }
    request = urllib.request.Request(
        f"{server}/withdrawcur",
        data=json.dumps(data).encode('utf-8'),
        headers={
            "Content-Type": "application/json"
        },
    )
    
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            read = response.read()
            thefuckingjson = json.loads(read.decode('utf-8'))
            squdalog.debug(f'Withdrawing currency {thefuckingjson}')
            return thefuckingjson
    except urllib.error.URLError as e:
        return None

def get_currency(type: str):
    """Get our balance from a currency 
    with our ID from the server."""
    import urllib
    import json
    id = get_unique_bs_id()
    data = {
        "bs_id": id,
        "type": type,
    }
    request = urllib.request.Request(
        f"{server}/getcur",
        data=json.dumps(data).encode('utf-8'),
        headers={
            "Content-Type": "application/json"
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            read = response.read()
            thefuckingjson = json.loads(read.decode('utf-8'))
            squdalog.debug(f'Got currency {thefuckingjson}')
            return thefuckingjson
    except urllib.error.URLError as e:
        return None

def send_currency(amount: int, currency: str):
    """Deposit a specific amount with our ID from the server.
    WARNING: You must do checks yourself, otherwise amount can go negative."""
    import urllib
    import json
    assert currency in ['tickets', 'tokens']
    id = get_unique_bs_id()
    data = {
        "bs_id": id,
        "amount": amount,
        "type": currency,
    }
    request = urllib.request.Request(
        f"{server}/sendcur",
        data=json.dumps(data).encode('utf-8'),
        headers={
            "Content-Type": "application/json"
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            read = response.read()
            thefuckingjson = json.loads(read.decode('utf-8'))
            squdalog.debug(f'sending currency {thefuckingjson}')
            return thefuckingjson
    except urllib.error.URLError as e:
        return None

def show_unlockable(tex: str | dict):
    """Show a popup that a unlockable has been acquired.
    This does NOT change config, it only shows a popup. 
    You do that manually."""
    import bascenev1 as bs
    scale = (210, 210)
    scale2 = (130, 130)
    if not isinstance(tex, dict):
        texture = bs.gettexture(tex)
        mask = None
        tint1 = None
        tint2 = None
    else:
        texture = bs.gettexture(tex['texture'])
        mask = bs.gettexture(tex['mask'])
        tint1 = tex['tint1']
        tint2 = tex['tint2']
    x = 490
    front = True
    initial_y = -scale[0]
    end_y = scale[0] - 80
    # create our node
    node = bs.newnode('image', 
        attrs={
            'texture': bs.gettexture('tauntBorder'),
            'position': (x, initial_y), 
            'scale': scale,
            'opacity': 1.0,
            'absolute_scale': True,
            'attach': 'bottomCenter',
            'front': front,
        }
    )
    node2 = bs.newnode('image', 
        attrs={
            'texture': texture,
            'mask_texture': (
                bs.gettexture(
                    'characterIconMask'
                ) if mask else None
            ),
            'tint_texture': mask,
            'position': (x, initial_y), 
            'scale': scale2,
            'opacity': 1.0,
            'absolute_scale': True,
            'attach': 'bottomCenter',
            'front': front,
        }
    )
    node2.tint_color = tint1
    node2.tint2_color = tint2
    # create text
    textnode = bs.newnode("text", 
        attrs={
            "text": bs.Lstr(resource='gotUnlockable'),
            "position": (x, initial_y),
            "scale": 1.5,
            "h_attach": "center",
            "v_attach": "bottom",
            "h_align": "center",
            "color": (1, 1, 0),
            'front': front,
        }
    )
    
    # create a math node
    # (used to add a bit y offset)
    mathnode = bs.newnode(
        'math',
        owner=node,
        attrs={'input1': (0, 80), 'operation': 'add'},
    )
    node.connectattr('position', mathnode, 'input2')
    node.connectattr('position', node2, 'position')
    mathnode.connectattr('output', textnode, 'position')
    # aaanimate!
    def rotate():
        if node:
            node.rotate += 1
    bs.animate_array(node, 'position', 2, {
        0.0: (x, initial_y),
        0.5: (x, end_y),
        5.0: (x, end_y),
        6.0: (x, initial_y),
    })
    bs.timer(0.01, rotate, repeat=True)
    bs.timer(6.1, node.delete)
    bs.timer(6.1, node2.delete)
    bs.timer(6.1, textnode.delete)
    bs.getsound('unlockable').play()
    

def get_texture_for_powerup(
    ptype: str,
    ui: bool = False,
    preload: bool = False
):
    """Get a texture from a powerup string from a factory.
    Doesn't specifically have to be PowerupBoxFactory, 
    but you should use that."""
    import babase as ba
    import bascenev1 as bs
    import bauiv1 as bui
    from babase._logging import squdalog
    texture_map = {
        'triple_bombs': 'powerupBomb',
        'punch': 'powerupPunch',
        'ice_bombs': 'powerupIceBombs',
        'sticky_bombs': 'powerupStickyBombs',
        'shield': 'powerupShield',
        'impact_bombs': 'powerupImpactBombs',
        'health': 'powerupHealth',
        'land_mines': 'powerupLandMines',
        'curse': 'powerupCurse',
        'metal': 'powerupMetal',
        'deton': 'powerupDeton',
        'hook': 'powerupHook',
        'fireball': 'powerupFireball',
        'bloxy': 'powerupBloxy',
        'strong': 'powerupStrong',
        'spongebob': 'powerupSponge',
        'shotgun': 'powerupShotgun',
        'random': 'powerupRandom',
        'kookoo': 'curseKookoo',
        'dozer': 'curseDozer',
        'ire': 'curseIre',
        'sorrow': 'curseSorrow',
        'mime': 'curseMime',
        'litany': 'curseLitany',
        'watercooler': 'bombColorIce',
    }
    if preload:
        for texture in list(texture_map.values()):
            bs.gettexture(texture)
        return True
    texture_name = texture_map.get(ptype, 'white')
    texture = (
        bs.gettexture(texture_name)
        if not ui else bui.gettexture(texture_name)
    )
    if ptype not in texture_map:
        squdalog.error(f'{ptype} is not in the texture map. Please add it to mell_resources.\ndumbass')
    return texture

# wow... old code...
def shake_node(
    node, 
    intensity: float = 10.0, 
    duration: float = 1.0, 
    interval: float = 0.02,
    array_num: int = 2,
):
    """
    Shake a node.
    :param node: The node to shake (like your image or text).
    :param intensity: How strong shall we shake.
    :param duration: Duration of the shake.
    :param interval: The interval it updates at. Lower values are smoother but 
    often can go fast, and higher values are staticky but slower.
    :param array_num: Number of arrays. Using anything other than 2 uses 3 array numbers.
    """
    import bascenev1 as bs
    import random
    if not node:
        return

    original_pos = tuple(node.position)
    total_steps = int(duration / interval)
    step = 0

    def _update_shake():
        nonlocal step
        if not node or step >= total_steps:
            # Snap back to original position at the end
            if node:
                node.position = original_pos
            return

        # Calculate diminishing shake strength (optional)
        progress = step / total_steps
        falloff = 1.0 - progress
        current_intensity = intensity * falloff

        # Random offset around original position
        offset_x = random.uniform(-current_intensity, current_intensity)
        offset_y = random.uniform(-current_intensity, current_intensity)
        if array_num == 2:
            node.position = (
                original_pos[0] + offset_x,
                original_pos[1] + offset_y,
            )
        else:
            # we don't shake z pos, so it's not really weird
            node.position = (
                original_pos[0] + offset_x,
                original_pos[1] + offset_y,
                original_pos[2]
            )

        step += 1
        bs.timer(interval, _update_shake)

    _update_shake()

def show_notification(
    top_text: str = 'Notification',
    bottom_text: str = 'Bottom Text',
    icon: str | dict | None = None,
    mini_icon: str | None = None,
    sound: str = 'notification',
):
    """Shows a notification.
    important determines whether the notification
    is a normal, important notification, or a 
    non-important notification."""

    import bascenev1 as bs
    import textwrap

    session = bs.get_foreground_host_session()
    if not session:
        return

    with session.context:

        # keep track of notifications
        if not hasattr(bs.app, 'notifications'):
            bs.app.notifications = {}

        def _get_free_slot(entries: dict) -> int:
            slot = 0
            while slot in entries:
                slot += 1
            return slot

        # simple text wrapping
        wrap_width = 34
        wrapped_bottom = textwrap.fill(bottom_text, width=wrap_width)
        line_count = wrapped_bottom.count('\n') + 1

        slot = _get_free_slot(bs.app.notifications)
        bs.app.notifications[slot] = True

        width = 320

        # dynamically resize window
        extra_lines = max(0, line_count - 2)
        height = 70 + (extra_lines * 23)

        base_x = 470
        base_y = -40

        # account for resized notifications
        for i in range(slot):
            base_y -= 75

        base_y -= extra_lines * 8
        extra_box_y = extra_lines * 10

        nodes: list[bs.Node] = []
        transitioning = False
        front = True

        # play a sound based on importance
        bs.getsound(sound).play(volume=1.5)

        # background
        bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('softRect'),
                'position': (base_x, base_y - extra_box_y),
                'scale': (width, height),
                'color': (0.1, 0.1, 0.1),
                'opacity': 0.85,
                'attach': 'topCenter',
                'front': front,
            },
        )
        nodes.append(bg)

        # title
        title = bs.newnode(
            'text',
            attrs={
                'text': top_text,
                'position': (base_x - 110, base_y + 20),
                'scale': 1.1,
                'maxwidth': 150,
                'color': (1.0, 1.0, 1.0, 1.0),
                'h_align': 'left',
                'v_align': 'center',
                'shadow': 1.0,
                'flatness': 0.0,
                'v_attach': 'top',
                'front': front,
            },
        )
        nodes.append(title)

        # description
        desc = bs.newnode(
            'text',
            attrs={
                'text': wrapped_bottom,
                'position': (base_x - 110, base_y + 7),
                'scale': 0.9,
                'maxwidth': 270,
                'color': (0.85, 0.85, 0.85, 1.0),
                'h_align': 'left',
                'v_align': 'top',
                'shadow': 0.8,
                'flatness': 0.0,
                'v_attach': 'top',
                'front': front,
            },
        )
        nodes.append(desc)

        # main icon
        if icon:
            icon_node = bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture(icon),
                    'position': (base_x - 145, base_y),
                    'scale': (42, 42),
                    'attach': 'topCenter',
                    'front': front,
                },
            )
            nodes.append(icon_node)

            # mini icon
            if mini_icon:
                mini = bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture(mini_icon),
                        'position': (base_x - 125, base_y - 18),
                        'scale': (20, 20),
                        'attach': 'topCenter',
                        'front': front,
                    },
                )
                nodes.append(mini)

        # animate in
        for node in nodes:
            time = 0.05

            if node.getnodetype() == 'text':
                bs.animate(node, 'opacity', {
                    0.0: 0.0,
                    time: 1.0,
                })
            else:
                bs.animate(node, 'opacity', {
                    0.0: 0.0,
                    time: node.opacity,
                })

            bs.animate_array(
                node,
                'position',
                2,
                {
                    0.0: (node.position[0], node.position[1] + 20),
                    time: node.position,
                }
            )

        def trans_out():
            nonlocal transitioning

            if transitioning:
                return

            transitioning = True

            bs.app.notifications.pop(slot, None)

            for node in nodes:
                try:
                    current = getattr(node, 'opacity', 1.0)
                    time = 0.3

                    bs.animate(node, 'opacity', {
                        0.0: current,
                        time: 0.0,
                    })

                    bs.timer(time, node.delete)

                except Exception:
                    pass

        # auto-remove
        bs.timer(4.0, trans_out)

def steam_message(
    name: str,
    text: str,
    avatar: dict | str = 'null',
    bar_color: tuple[float, float, float] = (0.5, 0.7, 1.0)
):
    import bascenev1 as bs
    import textwrap
    scale = 0.9
    text_limit = 69
    name_limit = 25
    sound = 'steamMessage'

    session = bs.get_foreground_host_session()
    if not session:
        return

    with session.context:
        # keep track of notifications
        if not hasattr(bs.app, 'steam_msgs'):
            bs.app.steam_msgs = {}

        def _get_free_slot(entries: dict) -> int:
            slot = 0
            while slot in entries:
                slot += 1
            return slot

        # simple text wrapping
        wrap_width = 34
        wrapped_text = textwrap.fill(text, width=wrap_width)
        wrapped_text = (
            wrapped_text[:text_limit] 
            + '...' if len(wrapped_text) > text_limit
            else wrapped_text
        )
        truncated_name = (
            name[:name_limit]
            + '...' if len(name) > name_limit
            else name
        )
            
        slot = _get_free_slot(bs.app.steam_msgs)
        bs.app.steam_msgs[slot] = True

        base_x = 481
        base_y = -321

        # account for resized notifications
        for i in range(slot):
            base_y += 76

        front = True

        # play a sound based on importance
        bs.getsound(sound).play(volume=1.2)
        texnum = min(slot + 1, 4)
        tex = bs.gettexture(
            'steamNotif' + str(texnum)
        )

        # background
        bg = bs.newnode(
            'image',
            attrs={
                'texture': tex,
                'position': (base_x, -600),
                'scale': (512 * scale, 128 * scale),
                'front': front,
            },
        )
        namenode = bs.newnode(
            'text',
            owner=bg,
            attrs={
                'text': truncated_name,
                'scale': scale - 0.23,
                'maxwidth': 340,
                'h_align': 'left',
                'v_align': 'top',
                'flatness': 0.7,
                'shadow': 0.6,
                'front': front,
            },
        )
        textnode = bs.newnode(
            'text',
            owner=bg,
            attrs={
                'text': wrapped_text,
                'scale': scale - 0.27,
                'maxwidth': 350,
                'h_align': 'left',
                'v_align': 'top',
                'flatness': 0.7,
                'shadow': 0.6,
                'color': (0.8, 0.8, 0.8),
                'front': front,
            },
        )
        if isinstance(avatar, dict):
            avatar_tex = bs.gettexture(
                avatar.get('texture')
            )
            avatar_tinttex = bs.gettexture(
                avatar.get('tint_texture')
            )
            avatar_tint1 = avatar.get('tint_color')
            avatar_tint2 = avatar.get('tint2_color')
            if not avatar_tint1:
                avatar_tint1 = (1, 1, 1)
            if not avatar_tint2:
                avatar_tint2 = (1, 1, 1)
        else:
            avatar_tex = bs.gettexture(avatar)
            avatar_tinttex = None
            avatar_tint1 = (1, 1, 1)
            avatar_tint2 = (1, 1, 1)
            
        avatarnode = bs.newnode(
            'image',
            owner=bg,
            attrs={
                'texture': avatar_tex,
                'tint_texture': avatar_tinttex,
                'scale': (65 * scale, 65 * scale),
                'tint_color': avatar_tint1,
                'tint2_color': avatar_tint2,
                'front': front,
            },
        )
        barnode = bs.newnode(
            'image',
            owner=bg,
            attrs={
                'texture': bs.gettexture('white'),
                'color': bar_color,
                'scale': (4 * scale, 65 * scale),
                'front': front,
            },
        )
        # bar mathnode
        mathnode = bs.newnode(
            'math',
            owner=bg,
            attrs={'input1': (-90, 0, 0), 'operation': 'add'},
        )
        bg.connectattr('position', mathnode, 'input2')
        mathnode.connectattr('output', barnode, 'position')
        # avatar mathnode
        mathnode = bs.newnode(
            'math',
            owner=bg,
            attrs={'input1': (-120, 0, 0), 'operation': 'add'},
        )
        bg.connectattr('position', mathnode, 'input2')
        mathnode.connectattr('output', avatarnode, 'position')
        # text mathnode
        mathnode = bs.newnode(
            'math',
            owner=bg,
            attrs={'input1': (-79.5, 10, 0), 'operation': 'add'},
        )
        bg.connectattr('position', mathnode, 'input2')
        mathnode.connectattr('output', textnode, 'position')
        # name mathnode
        mathnode = bs.newnode(
            'math',
            owner=bg,
            attrs={'input1': (-80, 30, 0), 'operation': 'add'},
        )
        bg.connectattr('position', mathnode, 'input2')
        mathnode.connectattr('output', namenode, 'position')
        # animate
        bs.animate_array(
            bg, 
            'position', 
            2,
            {
                0: (base_x, -600),
                0.6: (base_x, base_y),
                4: (base_x, base_y),
                4.6: (base_x, -600),
            }
        )
        def delete():
            bg.delete()
            bs.app.steam_msgs.pop(slot, None)
        bs.timer(4.6, delete)
    

def rename_window(text: str):
    import ctypes
    import babase as ba
    try:
        user32 = ctypes.windll.user32
    except:
        user32 = None
    hwnd = ba.app.window_hwnd
    if not hwnd:
        return False
    user32.SetWindowTextW(hwnd, text)
    return True

def windows_msg_box(
    callback,
    title: str,
    text: str,
    style: str = "ok",
    position: tuple[int, int] = (0, 0),
) -> None:
    import ctypes
    import threading
    import babase as ba
    from ctypes import wintypes

    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
    except Exception:
        return

    # Proper signatures
    user32.CallNextHookEx.argtypes = (
        wintypes.HHOOK,
        ctypes.c_int,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )
    user32.CallNextHookEx.restype = ctypes.c_ssize_t

    user32.SetWindowPos.argtypes = (
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint,
    )

    HOOKPROC = ctypes.WINFUNCTYPE(
        ctypes.c_ssize_t,
        ctypes.c_int,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )

    styles = {
        "ok": 0x0,
        "ok_cancel": 0x1,
        "yes_no": 0x4,
        "yes_no_cancel": 0x3,
        "retry_cancel": 0x5,
        "cancel_try_continue": 0x6,
        "error": 0x10,
    }

    if style not in styles:
        raise TypeError(
            f"{style!r} is not a valid style. "
            f"Available styles: {list(styles)}"
        )

    raw_style = styles[style]

    def thread():
        hook = None

        @HOOKPROC
        def cbt_hook_proc(code, wparam, lparam):
            if code == 5:  # HCBT_ACTIVATE
                hwnd = int(wparam)

                user32.SetWindowPos(
                    hwnd,
                    None,
                    int(position[0]),
                    int(position[1]),
                    0,
                    0,
                    0x0001 | 0x0004,  # SWP_NOSIZE | SWP_NOZORDER
                )

            return 0

        hook = user32.SetWindowsHookExW(
            5,  # WH_CBT
            cbt_hook_proc,
            None,
            kernel32.GetCurrentThreadId(),
        )

        try:
            result = user32.MessageBoxW(
                None,
                text,
                title,
                raw_style,
            )
        finally:
            if hook:
                user32.UnhookWindowsHookEx(hook)

        result = {
            1: "ok",
            2: "cancel",
            3: "abort",
            4: "retry",
            5: "ignore",
            6: "yes",
            7: "no",
            10: "retry",
            11: "continue",
        }.get(result, "unknown")

        if callback:
            callback(result)

    threading.Thread(
        target=thread,
        daemon=False,
    ).start()

def shake_window(
    hwnd: int | None = None,
    intensity: float = 10,
    duration: float = 0.5,
    frequency: int = 120,
):
    import ctypes
    import random
    import time
    import threading
    import babase as ba
    # we use bombsquad's window per default,
    # but allow replacing it
    hwnd = hwnd or ba.app.window_hwnd
    if not hwnd:
        return
    # window shake gets *FUNKY* on fullscreen,
    # and it also should be toggleable,
    # so disable it in such cases
    if (
        ba.app.config.get('Fullscreen')
        or ba.app.config.get('squda_nowindowshake')
    ):
        return

    # user32
    user32 = ctypes.windll.user32

    # idk what a rect is
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    # shake (on thread)
    def _shake():
        # get rect
        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))

        # base x...
        base_x = rect.left
        base_y = rect.top
        w = rect.right - rect.left
        h = rect.bottom - rect.top

        # get start and end
        start = time.perf_counter()
        end = start + duration
        frame_time = 1 / frequency
        
        # last direction x and y
        last_dx = 0
        last_dy = 0

        while True:
            now = time.perf_counter()
            if now >= end:
                break

            # progress 1 to 0
            t = (end - now) / duration

            current_intensity = intensity * t

            # direction is random
            dx = random.uniform(-current_intensity, current_intensity)
            dy = random.uniform(-current_intensity, current_intensity)

            # apply relative to base position
            user32.MoveWindow(
                hwnd,
                int(base_x + dx),
                int(base_y + dy),
                w,
                h,
                True,
            )
            # save last direction
            last_dx, last_dy = dx, dy
            time.sleep(frame_time)

        # return goes to center
        steps = 10
        for i in range(steps):
            t = 1 - (i / steps)

            user32.MoveWindow(
                hwnd,
                int(base_x + last_dx * t),
                int(base_y + last_dy * t),
                w,
                h,
                True,
            )
            time.sleep(frame_time)

        # finally, snap to the center
        user32.MoveWindow(hwnd, base_x, base_y, w, h, True)
    threading.Thread(target=_shake, daemon=True).start()

def set_trans_key(
    hwnd: int | None = None, 
    color: int = 0x00FF00
):
    # look. i already know what you're gonna say.
    # yes i didn't make this. does it LOOK like
    # i have the mental capability to do so???
    import babase as ba
    import ctypes
    import threading 
    # use default hwnd or other one
    hwnd = hwnd or ba.app.window_hwnd
    if not hwnd:
        return
    
    user32 = ctypes.windll.user32
    
    LWA_COLORKEY = 0x1
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x80000
    LWA_ALPHA = 0x2
    def _trans_thread():
        # green = 0x00FF00 in BGR format
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
        user32.SetLayeredWindowAttributes(hwnd, color, 0, LWA_COLORKEY)
    # this shouldn't lag the main thread,
    # but probably safer to do it in another
    # just incase (and so the effect isn't noticeable)
    threading.Thread(target=_trans_thread, daemon=False).start()

# ---------------------------------- NETWORKING -------------------------------------------

def get_clean_account_name() -> str:
    import bauiv1 as bui
    display = bui.app.plus.get_v1_account_display_string()
    name = "".join(c for c in display if not (0xE000 <= ord(c) <= 0xF8FF))
    return name

def _request(endpoint: str, payload: dict):
    try:
        import json
        import urllib.request

        payload.setdefault('user', get_clean_account_name())

        req = urllib.request.Request(
            url=f"{server}/{endpoint}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=2) as response:
            thefuckingjson = json.loads(response.read().decode('utf-8'))
            squdalog.debug(f'Requested: {thefuckingjson}')
            return thefuckingjson

    except Exception as exc:
        return {'status': 'fail', 'message': str(exc)}


def send_friend_request(name: str):
    return _request('friends/request', {
        'from': get_clean_account_name(),
        'to': name
    })


def respond_friend_request(name: str, accept: bool):
    return _request('friends/respond', {
        'from': name,
        'accept': accept
    })

def send_message(name: str, message: str):
    return _request('friends/message', {
        'from': get_clean_account_name(),
        'to': name,
        'message': message
    })

def set_all_seen(name: str):
    return _request('friends/set_all_seen', {
        'with': name,
    })

def remove_friend(name: str):
    return _request('friends/remove', {
        'target': name
    })

def get_messages(name: str):
    return _request('friends/messages', {
        'with': name,
    })

def get_friends():
    return _request('friends/list', {})

def get_info_from_id(id: str):
    return _request('api/get_info', {
        'id': id,
    })

def get_status_from_id(id: str):
    return _request('api/get_status', {
        'id': id,
    })

def set_profile_data(data: dict):
    return _request('api/set_profile_data', data)

def submit_score(data: dict):
    import bascenev1 as bs
    call = data.pop('done_call')
    request = _request('api/submit_score', data)
    bs.pushcall(
        bs.Call(call, request), 
        from_other_thread=True
    )
    return request

def get_online():
    try:
        import json
        import urllib.request
        endpoint = '/online'
        req = urllib.request.Request(
            url=f"{server}/{endpoint}",
            method="GET"
        )
        response = urllib.request.urlopen(req, timeout=2)
        return json.loads(response.read().decode('utf-8'))

    except Exception as e:
        return {'status': 'fail', 'message': str(e)}
