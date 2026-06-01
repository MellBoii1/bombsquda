""" Activity and session for the online menu. """
# :knowing:

from __future__ import annotations
import bascenev1 as bs
import bauiv1 as bui
import babase as ba
from typing import TYPE_CHECKING, override, Callable
from bascenev1lib.actor.text import Text
import threading
import time
import socket
import weakref

MENU_MOVE = 'tap'
MENU_OK = 'deek2'
MENU_BACK = 'back'

class VirtualKeyboard(bs.Actor):
    """Generic, non-ui, controller friendly keyboard"""

    def __init__(
        self,
        position: tuple[float, float] = (15, -30),
        rows: list[str] | None = None,
        initial_text: str = "",
        title: str = "",
        on_submit: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.position = position
        self.text = initial_text
        self.on_submit = on_submit
        self.on_cancel = on_cancel

        self.rows = rows or [
            "1234567890",
            "qwertyuiop",
            "asdfghjkl.",
            "zxcvbnm:/",
            f"{ba.charstr(ba.SpecialChar.DELETE)}{ba.charstr(ba.SpecialChar.PLAY_BUTTON)}",
        ]

        self.key_nodes = []
        self.cur_row = 0
        self.cur_col = 0

        px, py = position

        self.bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('windowHSmallVMed'),
                'position': (px + 15, py + 25),
                'scale': (700, 100 * len(self.rows)),
                'opacity': 0.8,
                'color': (0.2, 0.2, 0.2),
            },
        )

        # title
        self.title_node = bs.newnode(
            'text',
            attrs={
                'text': title,
                'position': (px, py + 200),
                'scale': 1.2,
                'h_align': 'center',
                'v_align': 'center',
            },
        )

        # input field bg
        self.field_bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('buttonSquareWide'),
                'position': (px - 15, py + 150),
                'scale': (500, 70),
                'opacity': 0.5,
            },
        )

        # input text
        self.field_text = bs.newnode(
            'text',
            attrs={
                'text': self.text,
                'position': (px, py + 150),
                'scale': 1.2,
                'h_align': 'center',
                'v_align': 'center',
            },
        )

        start_y = py + 70

        for r, row in enumerate(self.rows):
            chars = row.split(" ") if " " in row else list(row)

            start_x = px - (len(chars) * 22)

            for c, char in enumerate(chars):
                bg = bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture('buttonSquare'),
                        'position': (
                            start_x + c * 44 + 4,
                            start_y - r * 50 + 15
                        ),
                        'scale': (45, 45),
                        'color': (0.2, 0.2, 0.2),
                        'opacity': 0.9,
                    },
                )

                txt = bs.newnode(
                    'text',
                    attrs={
                        'text': char,
                        'position': (
                            start_x + c * 44,
                            start_y - r * 50
                        ),
                        'scale': 1.0,
                        'h_align': 'center',
                    },
                )

                self.key_nodes.append((r, c, char, txt, bg))

        self._update_cursor()


    def _refresh(self):
        self.field_text.text = self.text

    def _get_char(self):
        for r, c, ch, _, _2 in self.key_nodes:
            if r == self.cur_row and c == self.cur_col:
                return ch
        return ""

    def _row_length(self, row: int):
        count = 0
        for r, _, _, _, _ in self.key_nodes:
            if r == row:
                count += 1
        return count

    def select(self):
        ch = self._get_char()

        if ch == ba.charstr(ba.SpecialChar.DELETE):
            self.text = self.text[:-1]
            self._refresh()
            bs.getsound('key_back').play()

        elif ch == ba.charstr(ba.SpecialChar.PLAY_BUTTON):
            if self.on_submit:
                self.on_submit(self.text)
            self._refresh()
            bs.getsound('survey_ok2').play()
            return

        else:
            self.text += ch
            bs.getsound('key_type').play()

        self._refresh()
    
    def delete(self):
        for _, _, _, node, node2 in self.key_nodes:
            node.delete()
            node2.delete()
        self.title_node.delete()
        self.field_bg.delete()
        self.field_text.delete()

    def back(self):
        bs.getsound('key_back').play()
        if self.text:
            self.text = self.text[:-1]
            self._refresh()
        else:
            if self.on_cancel:
                self.on_cancel()

    def move(self, dx: int, dy: int):
        self.cur_row = (self.cur_row + round(dy)) % len(self.rows)

        row_len = self._row_length(self.cur_row)
        self.cur_col = (self.cur_col + round(dx)) % row_len
        if abs(dx) > 0:
            bs.getsound('key_horizontal').play()
        if abs(dy) > 0:
            bs.getsound('key_vertical').play()

        self._update_cursor()
    
    def left_right(self, value: int):
        self.move(dx=value, dy=0)
    
    def up_down(self, value: int):
        self.move(dx=0, dy=-value)
        
    def _update_cursor(self):
        for r, c, _, txt, bg in self.key_nodes:
            txt.color = (0.8, 0.8, 0.8)
            bg.color = (0.2, 0.2, 0.2)

            if r == self.cur_row and c == self.cur_col:
                txt.color = (1, 1, 1)
                bg.color = (0.4, 0.4, 0.4)



# player..
class Player(bs.Player):
    """Our player type for this game."""
    
# party fetcher...
class PartyFetcher:
    def __init__(self):
        self.parties: list[dict] = []
        self.refreshing = False

    def refresh(self):
        if self.refreshing:
            return
        self.refreshing = True

        plus = bui.app.plus
        plus.add_v1_account_transaction(
            {
                'type': 'PUBLIC_PARTY_QUERY',
                'proto': bs.protocol_version(),
                'lang': bui.app.lang.language,
            },
            callback=self._on_result,
        )
        plus.run_v1_account_transactions()

    def _on_result(self, result):
        self.refreshing = False
        if not result:
            self.parties = []
            return
        self.parties = result['l']

# session..
class OnlineMenuSession(bs.Session):
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.lobby_autojoin = True
        self.setactivity(bs.newactivity(OnlineSelection))
        
class OnlineSelection(bs.GameActivity[bs.Player, bs.Team]):
    name = ''
    description = ''
    suppress_zoomtext = True
    show_controls_guide = False
    allow_pausing = False
    
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Nothing']
        
    def __init__(self, settings: dict):
        super().__init__(settings)
        # make a background!
        self.allow_emeralds = False
        self.bg = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('DSspace'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('DSspace'),
                },
            )
        )
        self.earth = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('spaceEarth'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('spaceLevel'),
                },
            )
        )
                
    def on_transition_in(self) -> None:
        super().on_transition_in()
        
        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'
        bs.setmusic(bs.MusicType.ONLINE, continuous=True)
        self.join_text = None
        self.menu_items = [
            {"id": "browse", "label": "Browse"},
            {"id": "host", "label": "Host Game"},
            {"id": "direct", "label": "Direct Connect"},
            {"id": "back", "label": "Back"},
        ]
        self.menu_nodes = []
        self.selected_index = 0

        x = -50
        start_y = 100
        spacing = 100
        button_offset = 550
        # background to make
        # it look nice
        self.background = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('windowHSmallVMed'),
                'position': (x + button_offset - 30, -15),
                'scale': (700, 1000),
                'color': (0.2, 0.2, 0.2),
                'opacity': 0.6,
            },
        )
        
        for i, item in enumerate(self.menu_items):
            y = start_y - i * spacing

            # bg button
            bg = bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('buttonSquareWide'),
                    'position': (x + button_offset, y),
                    'scale': (500, 100),
                    'color': (0.2, 0.2, 0.2),
                    'opacity': 0.6,
                },
            )

            # le text
            text = bs.newnode(
                'text',
                attrs={
                    'text': item["label"],
                    'position': (x, y),
                    'scale': 1.4,
                    'color': (1, 1, 1),
                    'h_align': 'right',
                    'v_align': 'center',
                    'h_attach': 'right',
                    'shadow': 0.5,
                    'flatness': 0.3,
                },
            )
            # append to our menu nodes!
            self.menu_nodes.append({"bg": bg, "text": text})
        self.xpos = x
        self.button_offset = button_offset
        self._update_selection()
        # throw some controller info
        # on how to use the menu
        infoy = 30
        infox = 10
        self.backinfo = bs.newnode(
            'text',
            attrs={
                'text': (
                    f"{ba.charstr(ba.SpecialChar.RIGHT_BUTTON)} = "
                    f"{ba.charstr(ba.SpecialChar.BACK)}"
                ),
                'position': (infox, infoy),
                'scale': 2.0,
                'color': (1, 1, 1),
                'v_align': 'center',
                'h_align': 'left',
                'v_attach': 'bottom',
                'h_attach': 'left',
                'shadow': 0.5,
                'flatness': 0.3,
            },
        )
        if len(self.players) < 1:
            self.join_text = Text(
                bs.Lstr(resource='pressToContinueActivity'),
                h_align=Text.HAlign.CENTER,
                v_attach=Text.VAttach.TOP,
                scale=1.5,
            )
    
    def _update_selection(self):
        select_offset = -70
        button_offset = self.button_offset
        
        for i, item in enumerate(self.menu_nodes):
            y = 130 - i * 100
            offset = select_offset if i == self.selected_index else 0

            item["text"].position = (self.xpos + offset, y)
            item["bg"].position   = (self.xpos + button_offset + offset, y)

            if i == self.selected_index:
                item["bg"].opacity = 1.0
            else:
                item["bg"].opacity = 0.6

    def up(self):
        self.selected_index = (self.selected_index - 1) % len(self.menu_nodes)
        bs.getsound(MENU_MOVE).play()
        self._update_selection()

    def down(self):
        self.selected_index = (self.selected_index + 1) % len(self.menu_nodes)
        bs.getsound(MENU_MOVE).play()
        self._update_selection()
    
    def back(self):
        bs.getsound(MENU_BACK).play()
        bs.app.classic.return_to_main_menu_session_gracefully()
        
    def select(self):
        item_id = self.menu_items[self.selected_index]["id"]
        bs.getsound(MENU_OK).play()

        if item_id == "browse":
            self.session.setactivity(bs.newactivity(ServerListActivity))
        elif item_id == "host":
            pass  # hosting menu
        elif item_id == "direct":
            self.session.setactivity(bs.newactivity(DirectConnectActivity))
        elif item_id == "back":
            self.back()
            
        
    @override
    def on_player_join(self, player: PlayerT) -> None:
        if self.join_text:
            self.join_text.node.delete()
        player.assigninput(
            (
                ba.InputType.JUMP_PRESS,
                ba.InputType.PUNCH_PRESS,
                ba.InputType.PICK_UP_PRESS,
            ),
            self.select,
        )
        player.assigninput(ba.InputType.UP_PRESS, self.up)
        player.assigninput(ba.InputType.DOWN_PRESS, self.down)
        player.assigninput(ba.InputType.BOMB_PRESS, self.back)
        
    def on_begin(self) -> None:
        super().on_begin()
        
class DirectConnectActivity(bs.GameActivity[bs.Player, bs.Team]):
    """activity for directly connecting to servers."""
    suppress_zoomtext = True
    show_controls_guide = False
    allow_pausing = False
    name=''

    @classmethod
    def get_supported_maps(cls, sessiontype):
        return ['Nothing']

    def __init__(self, settings: dict):
        super().__init__(settings)
        # make a background!
        self.allow_emeralds = False
        self.bg = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('DSspace'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('DSspace'),
                },
            )
        )
        self.earth = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('spaceEarth'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('spaceLevel'),
                },
            )
        )

        self.keyboard = VirtualKeyboard(
            title="Enter Address (IP:PORT)",
            initial_text="",
            on_submit=bs.WeakCall(self._connect),
            on_cancel=bs.WeakCall(self._go_back),
        )

    # ------------------------------------------------------

    def _parse_address(self, text: str):
        text = text.strip()

        if ":" not in text:
            raise ValueError("Use the format: 'IP:PORT'.")

        ip, port = text.split(":", 1)

        if not port.isdigit():
            raise ValueError("Port must be number")

        port = int(port)

        if not 1 <= port <= 65535:
            raise ValueError("Port out of range")

        return ip, port

    def _connect(self, text: str):
        try:
            ip, port = self._parse_address(text)
            print(ip)
            print(port)
            bs.connect_to_party(ip, port=port)
        except Exception as exc:
            bs.screenmessage(str(exc), color=(1, 0, 0))

    def _go_back(self):
        import efro.debug
        self.session.setactivity(bs.newactivity(OnlineSelection))

    # ------------------------------------------------------

    def on_player_join(self, player):
        player.assigninput(bs.InputType.JUMP_PRESS, self.keyboard.select)
        player.assigninput(bs.InputType.BOMB_PRESS, self.keyboard.back)
        player.assigninput(bs.InputType.LEFT_RIGHT, self.keyboard.left_right)
        player.assigninput(bs.InputType.UP_DOWN, self.keyboard.up_down)

    def on_transition_in(self):
        super().on_transition_in()
        self.globalsnode.camera_mode = 'rotate'
        bs.setmusic(bs.MusicType.ONLINE, continuous=True)
        
class ServerListActivity(bs.GameActivity[bs.Player, bs.Team]):
    """Activity for showing online servers."""

    name = ''
    description = ''
    suppress_zoomtext = True
    show_controls_guide = False
    allow_pausing = False
    
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Nothing']
        
    def __init__(self, settings: dict):
        super().__init__(settings)
        self.allow_emeralds = False
        # make a background!
        self.bg = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('DSspace'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('DSspace'),
                },
            )
        )
        self.earth = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('spaceEarth'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('spaceLevel'),
                },
            )
        )
        self.join_text = None
        if len(self.players) < 1:
            self.join_text = Text(
                bs.Lstr(resource='pressToContinueActivity'),
                h_align=Text.HAlign.CENTER,
                v_attach=Text.VAttach.TOP,
                scale=1.5,
            )
        self.fetcher = PartyFetcher()
        self.fetcher.refresh()
        self.selected_index = 0
        self.scroll_offset = 0
        self.VISIBLE_ROWS = 14   # tweak for your screen
        self.party_text_nodes: list[Text] = []
        self.pings = {}
        self.pinging = set()
        self.ping_state = {}
        self.MAX_PING_THREADS = 10

                
    def rebuild_list(self):
        for n in self.party_text_nodes:
            n.delete()
        self.party_text_nodes.clear()

        start_y = 320.0
        spacing = 50.0

        visible_parties = self.fetcher.parties[
            self.scroll_offset : self.scroll_offset + self.VISIBLE_ROWS
        ]

        for row, p in enumerate(visible_parties):
            index = self.scroll_offset + row
            y = start_y - row * spacing

            color = (1, 1, 1, 1) if index == self.selected_index else (0.5, 0.5, 0.5, 1)

            node = bs.newnode(
                'text',
                attrs={
                    'text': f"{p['n']}  {p['s']}/{p['sm']}, {p['pd']}ms",
                    'position': (0, y),
                    'scale': 1.4,
                    'color': color,
                    'h_align': 'center',
                    'v_align': 'center',
                    'shadow': 0.5,
                    'flatness': 0.3,
                    'maxwidth': 500,
                },
            )

            self.party_text_nodes.append(node)

    def _ping_party(self, addr: str, port: int):
        import socket, time, threading

        key = (addr, port)
        if key in self.pinging:
            return

        if len(self.pinging) >= self.MAX_PING_THREADS:
            return

        self.pinging.add(key)
        self.ping_state[key] = "measuring"

        def do_ping():
            ping = None
            sock = None
            try:
                socket_type = socket.AF_INET6 if ":" in addr else socket.AF_INET
                sock = socket.socket(socket_type, socket.SOCK_DGRAM)
                sock.connect((addr, port))
                sock.settimeout(1)

                start = time.time()
                accessible = False

                for _ in range(3):
                    sock.send(b'\x0b')
                    try:
                        if sock.recv(10) == b'\x0c':
                            accessible = True
                            break
                    except Exception:
                        pass
                    time.sleep(0.1)

                if accessible:
                    ping = int((time.time() - start) * 1000)

            except Exception:
                pass
            finally:
                if sock:
                    sock.close()

            self.pings[key] = ping
            self.ping_state[key] = "done"
            self.pinging.discard(key)

        threading.Thread(target=do_ping, daemon=True).start()



    def refresh_parties(self):
        self.fetcher.refresh()
        for p in self.fetcher.parties:
            key = (p['a'], p['p'])

            if key not in self.ping_state:
                self._ping_party(p['a'], p['p'])

            if self.ping_state.get(key) != "done":
                p['pd'] = "…"
            else:
                val = self.pings.get(key)
                p['pd'] = val if val is not None else "N/A"
        bs.timer(0.3, self.rebuild_list)
        
    def on_transition_in(self) -> None:
        super().on_transition_in()
        
        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'
        bs.setmusic(bs.MusicType.ONLINE, continuous=True)
        if self.players == 0:
            self.join_text = Text(
                bs.Lstr(resource='pressToContinueActivity'),
                h_align=Text.HAlign.CENTER,
                v_attach=Text.VAttach.TOP,
                scale=1.5,
            )
        else:
            self.refresh_timer = bs.Timer(3.0, self.refresh_parties, repeat=True)
            self.refresh_parties()
        # background to make
        # it look nice
        self.background = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('windowHSmallVMed'),
                'position': (50, 0),
                'scale': (1000, 2000),
                'color': (0.2, 0.2, 0.2),
                'opacity': 0.8,
            },
        )
        infoy = 30
        infox = 10
        # throw some controller info
        # on how to use the menu
        self.backinfo = bs.newnode(
                'text',
                attrs={
                    'text': (
                        f"{ba.charstr(ba.SpecialChar.RIGHT_BUTTON)} = "
                        f"{ba.charstr(ba.SpecialChar.BACK)}"
                    ),
                    'position': (infox, infoy + 50),
                    'scale': 1.6,
                    'color': (1, 1, 1),
                    'v_align': 'center',
                    'h_align': 'left',
                    'v_attach': 'bottom',
                    'h_attach': 'left',
                    'shadow': 0.5,
                    'flatness': 0.3,
                },
            )
        self.playinfo = bs.newnode(
                'text',
                attrs={
                    'text': (
                        f"{ba.charstr(ba.SpecialChar.LEFT_BUTTON)}, "
                        f"{ba.charstr(ba.SpecialChar.TOP_BUTTON)}, "
                        f"{ba.charstr(ba.SpecialChar.BOTTOM_BUTTON)} = "
                        f"{ba.charstr(ba.SpecialChar.PLAY_BUTTON)}"
                    ),
                    'position': (infox, infoy),
                    'scale': 1.3,
                    'color': (1, 1, 1),
                    'v_align': 'center',
                    'h_align': 'left',
                    'v_attach': 'bottom',
                    'h_attach': 'left',
                    'shadow': 0.5,
                    'flatness': 0.3,
                },
            )

    def move(self, value: int):
        if round(value) > 0:
            if self.selected_index > 0:
                self.selected_index -= 1

            if self.selected_index < self.scroll_offset:
                self.scroll_offset -= 1

            self.rebuild_list()
        elif round(value) < 0:
            if self.selected_index < len(self.fetcher.parties) - 1:
                self.selected_index += 1

            if self.selected_index >= self.scroll_offset + self.VISIBLE_ROWS:
                self.scroll_offset += 1

            self.rebuild_list()
        else:
            return
        bs.getsound(MENU_MOVE).play()

    def back(self):
        bs.getsound(MENU_BACK).play()
        self.session.setactivity(bs.newactivity(OnlineSelection))

    def select(self):
        if not self.fetcher.parties:
            return
        p = self.fetcher.parties[self.selected_index]
        bs.connect_to_party(p['a'], port=p['p'])
        bs.getsound(MENU_OK).play()
        
    @override
    def on_player_join(self, player: PlayerT) -> None:
        if self.join_text:
            self.join_text.node.delete()
        player.assigninput(
            (
                ba.InputType.JUMP_PRESS,
                ba.InputType.PUNCH_PRESS,
                ba.InputType.PICK_UP_PRESS,
            ),
            self.select,
        )
        player.assigninput(ba.InputType.UP_DOWN, self.move)
        player.assigninput(ba.InputType.BOMB_PRESS, self.back)
        self.refresh_timer = bs.Timer(3.0, self.refresh_parties, repeat=True)
        self.refresh_parties()
        
    def on_begin(self) -> None:
        super().on_begin()
