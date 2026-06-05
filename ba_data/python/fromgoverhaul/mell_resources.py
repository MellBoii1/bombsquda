""" 
Resources that should be easier to edit in a shared code,
like lists, dicts, server address, game version, and some useful functions.
"""

screams = ['screams/scream' + str(i + 1) + '' for i in range(15)]
server = "http://104.196.199.18:5000"
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
    'characters.taobaomascot': 800,
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
    'characters.taobaomascot': 'Taobao Mascot',
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
    'characters.kookoo': 'Kookoo',
    'characters.fancypants': 'Fancy Pants',
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
        'Taobao Mascot': gs('taobao'),
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
            'tint_texture': mask,
            'position': (x, initial_y), 
            'scale': scale2,
            'opacity': 1.0,
            'absolute_scale': True,
            'attach': 'bottomCenter',
            'front': front,
        }
    )
    # we can assume it's a character icon
    # if we have a mask...
    node3 = None
    if mask:
        node3 = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('iconBorder'),
                'tint_texture': bs.gettexture('characterIconMask'),
                'position': (x, initial_y), 
                'scale': (scale2[0] + 20, scale2[1] + 20),
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': 'bottomCenter',
                'front': front,
            }
        )
    if tint1:
        node2.tint_color = tint1
        node3.tint2_color = tint1
    if tint2:
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
    if node3:
        node.connectattr('position', node3, 'position')
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
    if node3:
        bs.timer(6.1, node3.delete)
    bs.timer(6.1, textnode.delete)
    bs.getsound('unlockable').play()
    

def get_texture_for_powerup(factory, ptype: str):
    """Get a texture from a powerup string from a factory.
    Doesn't specifically have to be PowerupBoxFactory, 
    but you should use that."""
    import babase as ba
    import bascenev1 as bs
    import bauiv1 as bui
    texture_map = {
        'triple_bombs': factory.tex_bomb,
        'punch': factory.tex_punch,
        'ice_bombs': factory.tex_ice_bombs,
        'sticky_bombs': factory.tex_sticky_bombs,
        'shield': factory.tex_shield,
        'impact_bombs': factory.tex_impact_bombs,
        'health': factory.tex_health,
        'land_mines': factory.tex_land_mines,
        'curse': factory.tex_curse,
        'metal': factory.tex_metal,
        'deton': factory.tex_deton,
        'hook': factory.tex_hook,
        'fireball': factory.tex_fireball,
        'bloxy': factory.tex_bloxy,
        'strong': factory.tex_strong,
        'spongebob': factory.tex_spongebob,
        'shotgun': factory.tex_shotgun,
        'star': factory.tex_star,
        'random': factory.tex_random,
        'kookoo': factory.tex_kookoo,
        'dozer': factory.tex_dozer,
        'ire': factory.tex_ire,
        'sorrow': factory.tex_sorrow,
        'mime': factory.tex_mime,
        'rue': factory.tex_rue,
        'litany': factory.tex_litany
    }
    if ptype not in texture_map:
        print(f'ERROR: {ptype} is not in the texture map. Please add it to mell_resources.\ndumbass')
        # get whether we should use ui with..
        # ..a context error. okay.
        try:
            return bs.gettexture('white')
        except ba.ContextError:
            return bui.gettexture('white')
    return texture_map.get(ptype)

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
    important: bool = True,
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
        if important:
            bs.getsound('notification').play(volume=1.5)
        else:
            bs.getsound('notification2').play()

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
    request = _request('api/submit_score', data)
    call = data['done_call']
    call(request)
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
