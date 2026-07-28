from __future__ import annotations

from typing import Sequence
import threading

import bauiv1 as bui
import bascenev1 as bs
import mellboii.mell_resources as mell


class FriendChatWindow(bui.Window):
    """Simple DM window."""

    def __init__(
        self,
        friend: str,
        origin: Sequence[float] = (0, 0),
    ):
        self._friend = friend
        self._friend_info = info = mell.get_info_from_id(self._friend)
        self._friend_name = info.get(
            'account_name',
            info.get('username', 'Unknown'),
        )

        self._messages: list[dict] = []

        self._loading = False
        self._closed = False

        self._r = 'friendsTab'

        self._width = 540
        self._height = 420
        self._msg_v = 30

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_right',
                scale_origin_stack_offset=origin,
                scale=(
                    1.8
                    if uiscale is bui.UIScale.SMALL
                    else 1.3
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
            )
        )

        # Close button.
        self._back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(35, self._height - 50),
            size=(50, 50),
            scale=0.9,
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.close,
        )

        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=btn,
        )

        # Title.
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.52, self._height - 30),
            size=(0, 0),
            text=self._friend_name,
            scale=1.0,
            color=(0.9, 0.9, 0.9),
            h_align='center',
            v_align='center',
            maxwidth=260,
        )

        # Loading spinner.
        self._spinner = bui.spinnerwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
        )
        
        self._status_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            text='',
            scale=0.8,
            color=(0.5, 0.5, 0.5),
            h_align='center',
            v_align='center',
            maxwidth=self._width * 0.7,
        )

        # Scroll widget.
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(25, 85),
            size=(self._width - 50, self._height - 155),
            border_opacity=0.4,
        )

        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget,
            border=10,
            margin=0,
        )

        # Text field.
        self._text_field = bui.textwidget(
            parent=self._root_widget,
            editable=True,
            position=(50, 35),
            size=(540, 40),
            text='',
            flatness=1.0,
            shadow=0.3,
            maxwidth=530,
            v_align='center',
            corner_scale=0.7,
            autoselect=True,
        )

        # Send button.
        self._send_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(450, 30),
            size=(40, 40),
            label='>',
            on_activate_call=self._send_message,
        )

        bui.textwidget(
            edit=self._text_field,
            on_return_press_call=self._send_button.activate,
        )

        # Auto update timer.
        self._update_timer = bui.AppTimer(
            3,
            bui.WeakCall(self._update),
            repeat=True,
        )

        self._update()

    def _send_message(self) -> None:
        """Send message in background."""

        text = bui.textwidget(query=self._text_field).strip()

        if not text:
            return

        # Disable button while sending.
        bui.buttonwidget(
            edit=self._send_button,
            label='...',
        )

        threading.Thread(
            target=self._send_message_thread,
            args=(text,),
            daemon=True,
        ).start()

    def _send_message_thread(self, text: str) -> None:
        """Background send."""

        try:
            result = mell.send_message(self._friend, text)

            bs.pushcall(
                bui.Call(
                    self._finish_send,
                    result,
                    text,
                ),
                from_other_thread=True,
            )

        except Exception as exc:
            bs.pushcall(
                bui.Call(
                    self._send_error,
                    str(exc),
                ),
                from_other_thread=True,
            )

    def _finish_send(
        self,
        result: dict,
        text: str,
    ) -> None:
        """Finish send on main thread."""

        if self._closed:
            return

        bui.buttonwidget(
            edit=self._send_button,
            label='>',
        )

        if result.get('status') == 'sent':
            bui.textwidget(
                edit=self._text_field,
                text='',
            )

            self._update()

        else:
            self._send_error(
                result.get(
                    'error',
                    result.get(
                        'message',
                        bui.Lstr(r=f'{self._r}.unknownError'),
                    ),
                )
            )

    def _send_error(self, error: str) -> None:
        """Show send error."""

        if self._closed:
            return

        bui.buttonwidget(
            edit=self._send_button,
            label='>',
        )

        bui.screenmessage(
            error,
            color=(1, 0, 0),
        )

        bui.getsound('error').play()

    def _update(self) -> None:
        """Threaded refresh."""

        if self._loading or self._closed:
            return

        self._loading = True

        bui.spinnerwidget(
            edit=self._spinner,
            visible=True,
        )
        bui.textwidget(
            edit=self._status_text,
            text='',
        )

        threading.Thread(
            target=self._update_thread,
            daemon=True,
        ).start()

    def _update_thread(self) -> None:
        """Background fetch."""

        response = mell.get_messages(self._friend)
        messages = response.get('messages', [])
        if (
            response.get('status', '') 
            in ['error', 'fail'] 
            or response.get('error')
        ):
            bs.pushcall(
                bui.Call(
                    self._update_failed,
                    response.get(
                        'error',
                        response.get(
                            'message',
                            bui.Lstr(r=f'{self._r}.unknownError'),
                        ),
                    ),
                ),
                from_other_thread=True,
            )
            return

        bs.pushcall(
            bui.Call(
                self._apply_messages,
                messages,
            ),
            from_other_thread=True,
        )
        mell.set_all_seen(self._friend)

    def _update_failed(self, error: str) -> None:
        """Handle update failure."""

        self._loading = False

        if self._closed:
            return

        bui.textwidget(
            edit=self._status_text,
            text=bui.Lstr(
                r=f'{self._r}.errorGenericDescriptive',
                s=[('${ERROR}', error)]
            ),
        )
        bui.spinnerwidget(
            edit=self._spinner,
            visible=False,
        )

    def _apply_messages(
        self,
        messages: list[dict],
    ) -> None:
        """Apply messages on main thread."""

        self._loading = False

        if self._closed:
            return

        bui.spinnerwidget(
            edit=self._spinner,
            visible=False,
        )
        bui.textwidget(
            edit=self._status_text,
            text=''
        )

        # Skip rebuilding if unchanged.
        if messages == self._messages:
            return

        self._messages = messages

        # Clear old widgets.
        for child in self._columnwidget.get_children():
            child.delete()

        me = mell.get_unique_bs_id()

        for msg in messages:
            sender = msg.get('from', '???')
            text = msg.get('message', '')
            time = msg.get('time', '')

            mine = sender == me

            color = (
                (0.5, 1.0, 0.5)
                if mine
                else (1.0, 1.0, 1.0)
            )

            prefix = (
                'You'
                if mine
                else self._friend_name
            )

            widget = bui.textwidget(
                parent=self._columnwidget,
                size=(0, 0),
                scale=0.6,
                flatness=1.0,
                position=(self._width * 0.5, self._msg_v),
                shadow=0.2,
                h_align='left',
                v_align='center',
                text=f'[{time}] {prefix}: {text}',
                color=color,
                maxwidth=430,
            )

            bui.containerwidget(
                edit=self._columnwidget,
                visible_child=widget,
            )

    def close(self) -> None:
        """Close window."""

        self._closed = True

        if not self._root_widget:
            return

        if self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget,
            transition='out_scale',
        )