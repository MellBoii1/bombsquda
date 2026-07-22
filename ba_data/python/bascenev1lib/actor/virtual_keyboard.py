import bascenev1 as bs
import babase as ba
from typing import Optional, Callable

class VirtualKeyboard(bs.Actor):
    """Generic, non-ui, controller friendly keyboard"""

    def __init__(
        self,
        position: tuple[float, float] = (15, -30),
        width: float = 700,
        height: Optional[float] = None,
        rows: list[str] | None = None,
        initial_text: str = "",
        title: str = "",
        max_length: Optional[int] = None,
        password: bool = False,
        password_char: str = "*",
        bg_color: tuple[float, float, float] = (0.2, 0.2, 0.2),
        key_color: tuple[float, float, float] = (0.2, 0.2, 0.2),
        selected_key_color: tuple[float, float, float] = (0.4, 0.4, 0.4),
        text_color: tuple[float, float, float] = (0.8, 0.8, 0.8),
        selected_text_color: tuple[float, float, float] = (1, 1, 1),
        on_submit: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        on_change: Optional[Callable[[str], None]] = None,
        key_callbacks: Optional[dict] = None,
    ):
        super().__init__()
        self.position = position
        self.text = initial_text
        self.max_length = max_length
        self.password = password
        self.password_char = password_char
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.on_change = on_change
        self.key_callbacks = key_callbacks

        self.bg_color = bg_color
        self.key_color = key_color
        self.selected_key_color = selected_key_color
        self.text_color = text_color
        self.selected_text_color = selected_text_color

        self.rows = rows or [
            "1234567890",
            "qwertyuiop",
            "asdfghjkl.",
            "zxcvbnm:/",
            f"{ba.charstr(ba.SpecialChar.SHIFT)}{ba.charstr(ba.SpecialChar.DELETE)}_{ba.charstr(ba.SpecialChar.PLAY_BUTTON)}",
        ]

        self.width = width
        self.height = height if height is not None else 100 * len(self.rows)

        # figure out spacing from width/height so longer/shorter
        # keyboards still lay out sensibly
        max_row_len = max(
            (len(row.split(" ") if " " in row else list(row)) for row in self.rows),
            default=1,
        )
        self.col_spacing = self.width / max(max_row_len, 1)
        self.row_spacing = self.height / max(len(self.rows), 1)
        self.key_size = min(self.col_spacing, self.row_spacing) * 0.95

        self.key_nodes = []
        self.cur_row = 0
        self.cur_col = 0

        px, py = position

        self.bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('softRect2'),
                'position': (px - 30, py - 57),
                'scale': (self.width, self.height + 15),
                'opacity': 1,
                'color': self.bg_color,
            },
        )

        # title
        self.title_node = bs.newnode(
            'text',
            attrs={
                'text': title,
                'position': (px, py + self.height / 2 + 30),
                'scale': 1.2,
                'h_align': 'center',
                'v_align': 'center',
            },
        )

        # input field bg
        self.field_bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('softRectVertical'),
                'position': (px - 20, py + self.height / 2 - 20),
                'scale': (self.width * 0.71, 70),
                'opacity': 0.5,
            },
        )

        # input text
        self.field_text = bs.newnode(
            'text',
            attrs={
                'text': self._display_text(),
                'position': (px - 20, py + self.height / 2 - 20),
                'shadow': 0.6,
                'flatness': 0.8,
                'scale': 1.2,
                'h_align': 'center',
                'v_align': 'center',
            },
        )

        start_y = py + self.height / 2 - 100

        for r, row in enumerate(self.rows):
            chars = row.split(" ") if " " in row else list(row)

            start_x = px - (len(chars) * self.col_spacing / 2)

            for c, char in enumerate(chars):
                bg = bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture('buttonSquare'),
                        'position': (
                            start_x + c * self.col_spacing + self.col_spacing / 10,
                            start_y - r * self.row_spacing + 15
                        ),
                        'scale': (self.key_size, self.key_size),
                        'color': self.key_color,
                        'opacity': 1,
                    },
                )
                text = char
                txt = bs.newnode(
                    'text',
                    attrs={
                        'text': text,
                        'position': (
                            (start_x + c * self.col_spacing) + 5,
                            start_y - r * self.row_spacing
                        ),
                        'scale': 1.0,
                        'h_align': 'center',
                        'flatness': 0.7,
                        'shadow': 0.5,
                    },
                )

                self.key_nodes.append((r, c, char, txt, bg))

        self._update_cursor()

    def _display_text(self) -> str:
        if self.password:
            return f'{self.password_char * len(self.text)}|'
        return f'{self.text}|'

    def _refresh(self):
        if not self.bg:
            return
        self.field_text.text = self._display_text()
        if self.on_change:
            self.on_change(self.text)

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
            self.back()

        elif ch == ba.charstr(ba.SpecialChar.PLAY_BUTTON):
            if self.on_submit:
                self.on_submit(self.text)
            self._refresh()
            bs.getsound('survey_ok2').play()
            return
        
        # should fix this
        elif ch == '_':
            self.text += ' '
            bs.getsound('key_type').play()
        
        elif ch == ba.charstr(ba.SpecialChar.SHIFT):
            for seq in self.key_nodes:
                _, _2, char, node, _4 = seq
                index = self.key_nodes.index(seq)
                char = char.lower() if char.isupper() else char.upper()
                node.text = char
                self.key_nodes[index] = (_, _2, char, node, _4)
            bs.getsound('key_type').play()
        
        elif ch in self.key_callbacks.keys():
            self.key_callbacks.get(ch)()
            bs.getsound('key_type').play()

        else:
            if ch.isupper():
                for seq in self.key_nodes:
                    _, _2, char, node, _4 = seq
                    index = self.key_nodes.index(seq)
                    char = char.lower()
                    node.text = char
                    self.key_nodes[index] = (_, _2, char, node, _4)
            if self.max_length is None or len(self.text) < self.max_length:
                self.text += ch
                bs.getsound('key_type').play()
            else:
                bs.getsound('error').play()

        self._refresh()

    def delete(self):
        for _, _, _, node, node2 in self.key_nodes:
            node.delete()
            node2.delete()
        self.title_node.delete()
        self.field_bg.delete()
        self.field_text.delete()
        self.bg.delete()

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
            txt.color = self.text_color
            bg.color = self.key_color

            if r == self.cur_row and c == self.cur_col:
                txt.color = self.selected_text_color
                bg.color = self.selected_key_color