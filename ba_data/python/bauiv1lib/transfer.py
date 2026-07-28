# Released under the MIT License. See LICENSE for details.
#
"""UI related to transferring currencies like Spaz Tickets and Tokens."""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence, override, cast

import bauiv1 as bui
import babase as ba
import bascenev1 as bs
import mellboii.mell_resources as mell

class TransferWindow(bui.MainWindow):
    """Allows transferring currency through a server."""

    def __init__(
        self,
        transition: str | None = 'in_scale',
        origin_widget: bui.Widget | None = None,
    ):

        bui.set_analytics_screen('Help Window')

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 1400 if uiscale is bui.UIScale.SMALL else 600
        self._height = (
            1200
            if uiscale is bui.UIScale.SMALL else 400
        )
        # xoffs = 70 if uiscale is bui.UIScale.SMALL else 0
        # yoffs = -45 if uiscale is bui.UIScale.SMALL else 0

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.55
            if uiscale is bui.UIScale.SMALL
            else 1.15 if uiscale is bui.UIScale.MEDIUM else 1.0
        )

        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(self._width - 60, screensize[0] / scale)
        target_height = min(self._height - 100, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 100.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_full' if uiscale is bui.UIScale.SMALL else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                yoffs - (140 if uiscale is bui.UIScale.SMALL else 80),
            ),
            size=(0, 0),
            text=bui.Lstr(resource='transferText'),
            color=bui.app.ui_v1.title_color,
            scale=0.9 if uiscale is bui.UIScale.SMALL else 0.8,
            maxwidth=(130 if uiscale is bui.UIScale.SMALL else 200),
            h_align='center',
            v_align='center',
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(50, yoffs - 100),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        xoffs = 20
        yoffs -= 140
        # move our buttons a bit down and nudge right if small scale
        if uiscale is bui.UIScale.SMALL:
            yoffs -= 70
            xoffs += 40
        self._current_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.45 + xoffs, yoffs),
            text='',
            h_align='center',
            scale=0.8,
            color=(1, 1, 1, 0.6)
        )
        self._update_current()
        xoffs = 0
        yoffs -= 130
        # create a longer text field if on a small ui scale.
        textfieldxoffs = 0 if uiscale is not bui.UIScale.SMALL else 150
        # text that says 'send...' to signalify what it does
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.4 + xoffs, yoffs + 50),
            text=bui.Lstr(resource='transferSend'),
            color=(1, 1, 1, 0.6),
            scale=0.8,
            h_align='center',
        )
        # text field
        self._sendtext = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.2 + xoffs + textfieldxoffs, yoffs),
            size=(200 + textfieldxoffs, 40),
            editable=True,
            autoselect=True,
            text='',
            v_align='center',
            maxwidth=200 + textfieldxoffs,
        )
        # 2 buttons for sending tickets and tokens
        self._sendticketsbtn = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.58 + xoffs, yoffs + 2),
            autoselect=True,
            size=(40, 40),
            label=ba.charstr(ba.SpecialChar.OUYA_BUTTON_Y),
            on_activate_call=lambda: self._send_currency(type='tickets'),
        )
        self._sendtokensbtn = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.58 + xoffs + 70, yoffs + 2),
            autoselect=True,
            size=(40, 40),
            label=ba.charstr(ba.SpecialChar.OUYA_BUTTON_A),
            on_activate_call=lambda: self._send_currency(type='tokens'),
        )
        yoffs -= 80
        # text that says 'withdraw...' to signalify what it does
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.4 + xoffs, yoffs + 50),
            text=bui.Lstr(resource='transferWithdraw'),
            color=(1, 1, 1, 0.6),
            scale=0.8,
            h_align='center',
        )
        # text field
        self._taketext = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.2 + xoffs + textfieldxoffs, yoffs),
            size=(200 + textfieldxoffs, 40),
            editable=True,
            autoselect=True,
            text='',
            v_align='center',
            maxwidth=200 + textfieldxoffs,
        )
        # 2 buttons for taking tickets and tokens
        self._taketicketsbtn = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.58 + xoffs, yoffs + 2),
            autoselect=True,
            size=(40, 40),
            label=ba.charstr(ba.SpecialChar.OUYA_BUTTON_Y),
            on_activate_call=lambda: self._take_currency(type='tickets'),
        )
        self._taketokensbtn = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.58 + xoffs + 70, yoffs + 2),
            autoselect=True,
            size=(40, 40),
            label=ba.charstr(ba.SpecialChar.OUYA_BUTTON_A),
            on_activate_call=lambda: self._take_currency(type='tokens'),
        )
        
    def _send_currency(self, type: str):
        # get some important values...
        val = cast(str, bui.textwidget(query=self._sendtext)).strip()
        key = 'squda_spaztix' if type == 'tickets' else 'squda_spaztokens'
        balance = bui.app.config.get(key)
        glyph = (
            ba.charstr(ba.SpecialChar.OUYA_BUTTON_Y) if type == 'tickets'
            else ba.charstr(ba.SpecialChar.OUYA_BUTTON_A)
        )
        # value is a string, so check if its a digit
        if not val.isdigit():
            bui.screenmessage(
                bui.Lstr(resource='transferIncorrect'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        # convert to a integer then check if over 0
        val = int(val)
        if val <= 0:
            bui.screenmessage(
                bui.Lstr(resource='transferIncorrect'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        # check if the value is over the amount we have
        if val > balance:
            bui.screenmessage(
                bui.Lstr(
                    resource='transferInsufficient',
                    subs=[
                        ('${CURRENCY}', glyph),
                        ('${AMOUNT}', str(val)),
                    ]
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        # send_currency returns a result (None if error)
        result = mell.send_currency(val, type)
        # if no result, don't continue
        if not result:
            bui.screenmessage(bui.Lstr(resource='transferError'), color=(1, 0, 0))
            bui.getsound('error').play()
            return
        # get new balance and amount from the server
        amount = result.get('amount')
        new = result.get('new_bal')
        bui.screenmessage(
            bui.Lstr(
                resource='transferSuccess',
                subs=[
                    ('${AMOUNT}', str(amount)),
                    ('${NEW}', str(new)),
                ]
            ),
            color=(0, 1, 0),
        )
        # remove the same amount from us
        bui.app.config[key] = balance - amount
        bui.getsound('cashRegister').play()
        # update current text
        self._update_current()
    
    def _take_currency(self, type: str):
        # get some important values
        val = cast(str, bui.textwidget(query=self._taketext)).strip()
        key = 'squda_spaztix' if type == 'tickets' else 'squda_spaztokens'
        # we can use the amount we already gathered from updating text
        sbalance = (
            self._server_tickets if type == 'tickets'
            else self._server_tokens
        )
        balance = bui.app.config.get(key)
        glyph = (
            ba.charstr(ba.SpecialChar.OUYA_BUTTON_Y) if type == 'tickets'
            else ba.charstr(ba.SpecialChar.OUYA_BUTTON_A)
        )
        # check if value is digit
        if not val.isdigit():
            bui.screenmessage(
                bui.Lstr(resource='transferIncorrect'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        # convert to integer then check if below 0
        val = int(val)
        if val <= 0:
            bui.screenmessage(
                bui.Lstr(resource='transferIncorrect'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        # check if value over how much server has
        if val > sbalance:
            bui.screenmessage(
                bui.Lstr(
                    resource='transferInsufficient',
                    subs=[
                        ('${CURRENCY}', glyph),
                        ('${AMOUNT}', str(val)),
                    ]
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        # withdraw_currency returns a result (None if error)
        result = mell.withdraw_currency(val, type)
        if not result:
            bui.screenmessage(bui.Lstr(resource='transferError'), color=(1, 0, 0))
            bui.getsound('error').play()
            return
        # get new balance and amount from server
        amount = result.get('amount')
        new = result.get('new_bal')
        bui.screenmessage(
            bui.Lstr(
                resource='transferSuccess',
                subs=[
                    ('${AMOUNT}', str(amount)),
                    ('${NEW}', str(new)),
                ]
            ),
            color=(0, 1, 0),
        )
        # update text and our current count
        bui.app.config[key] = balance + amount
        bui.getsound('cashRegister').play()
        self._update_current()
    
    def _update_current(self):
        # we get our balance with the config...
        key1 = 'squda_spaztix'
        key2 = 'squda_spaztokens'
        balance1 = bui.app.config.get(key1)
        balance2 = bui.app.config.get(key2)
        # and get the server's through a helper in mell_resources
        self._server_tokens = toks = mell.get_currency('tokens').get('amount')
        self._server_tickets = tix = mell.get_currency('tickets').get('amount')
        # format some nice looking text with those values
        server_amount_str = f'{ba.charstr(ba.SpecialChar.OUYA_BUTTON_Y)}{tix}, {ba.charstr(ba.SpecialChar.OUYA_BUTTON_A)}{toks}'
        user_amount_str = f'{ba.charstr(ba.SpecialChar.OUYA_BUTTON_Y)}{balance1}, {ba.charstr(ba.SpecialChar.OUYA_BUTTON_A)}{balance2}'
        # edit the current text to use that
        bui.textwidget(edit=self._current_text, text=bui.Lstr(
                resource='transferCurrent', 
                subs=[
                    ('${AMOUNT}', server_amount_str),
                    ('${USERAMOUNT}', user_amount_str),
                ]
            ),
        )
        
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
