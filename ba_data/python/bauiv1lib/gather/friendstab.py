# pylint: disable=too-many-lines
"""Defines the Friends tab in the """

from __future__ import annotations

import copy
import time
import logging

from threading import Thread
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast, override

from bauiv1lib.gather import GatherTab
from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.gather.friendschat import FriendChatWindow
from bauiv1lib.gather.friendsadd import AddFriendsWindow

import mellboii.mell_resources as mell
import bauiv1 as bui
import bascenev1 as bs
import importlib

if TYPE_CHECKING:
    from typing import Callable, Any
    from bauiv1lib.gather import GatherWindow

class FriendsTab(GatherTab):
    """A tab that gets all the user's friends and formats
    them into a nice interactable UI."""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)

        self._r = 'friendsTab'

        self.friends_list = None

        self._subcontainer = None
        self._scrollwidget = None

        self._loading = False
        self._closed = False

    @override
    def on_activate(
        self,
        parent_widget: bui.Widget,
        tab_button: bui.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> bui.Widget:

        self.c_width = c_width = region_width
        self.c_height = c_height = region_height - 20
        self._closed = False

        self._container = bui.containerwidget(
            parent=parent_widget,
            position=(
                region_left,
                region_bottom + (region_height - c_height) * 0.5,
            ),
            size=(c_width, c_height),
            background=False,
            selection_loops_to_parent=True,
        )

        s_width = c_width - 100
        s_height = c_height - 50

        sub_width = min(500, s_width * 0.95)

        self._scrollwidget = bui.scrollwidget(
            parent=self._container,
            size=(s_width, s_height),
            position=(50, 20),
            simple_culling_v=20.0,
            highlight=False,
            center_small_content_horizontally=True,
            selection_loops_to_parent=True,
            border_opacity=0.4,
        )

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(sub_width, 0),
            background=False,
            selection_loops_to_parent=True,
        )

        self._status_text = bui.textwidget(
            parent=self._container,
            text='',
            size=(0, 0),
            scale=0.9,
            flatness=1.0,
            shadow=0.0,
            h_align='center',
            v_align='center',
            maxwidth=c_width,
            color=(0.6, 0.6, 0.6),
            position=(c_width * 0.5, c_height * 0.5),
        )
        
        self._spinner = bui.spinnerwidget(
            parent=self._container,
            position=(c_width * 0.5, c_height * 0.5),
        )

        if bui.app.config.get('squda_noonline'):
            full_error = bui.Lstr(r='noOnlineError')

            bui.textwidget(
                edit=self._status_text,
                text=bui.Lstr(
                    resource=f'{self._r}.errorText',
                    subs=[('${ERROR}', full_error)],
                ),
            )
            bui.spinnerwidget(
                edit=self._spinner,
                visible=False,
            )

            return self._container

        bui.buttonwidget(
            parent=self._container,
            position=(s_width * 0.92, s_height * 0.88),
            size=(60, 60),
            scale=1.2,
            label='',
            icon=bui.gettexture('addFriendIcon'),
            on_activate_call=bui.Call(self.add_friends_ui),
        )

        self.recreate_async()

        return self._container

    @override
    def on_deactivate(self) -> None:
        self._closed = True

    def recreate_async(self) -> None:
        """Recreate in background thread."""

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

        Thread(
            target=self._recreate_thread,
            daemon=True,
        ).start()

    def _recreate_thread(self) -> None:
        """Background loading."""

        try:
            flist = mell.get_friends()

            if (
                flist.get('status') in ['error', 'fail']
                or flist.get('error')
            ):
                bs.pushcall(
                    bui.Call(
                        self._show_error,
                        flist,
                    ),
                    from_other_thread=True,
                )
                return

            online = mell.get_online()

            info_cache = {}

            all_ids = (
                flist.get('friends', [])
                + flist.get('requests', [])
            )

            for account_id in all_ids:
                try:
                    info_cache[account_id] = (
                        mell.get_info_from_id(account_id)
                    )
                except Exception:
                    info_cache[account_id] = {}

            bs.pushcall(
                bui.Call(
                    self._finish_recreate,
                    flist,
                    online,
                    info_cache,
                ),
                from_other_thread=True,
            )

        except Exception as exc:
            bs.pushcall(
                bui.Call(
                    self._show_error,
                    {'error': str(exc)},
                ),
                from_other_thread=True,
            )

    def _show_error(self, data: dict):
        """Show loading error."""

        self._loading = False

        if self._closed:
            return

        full_error = (
            f"{data.get('status', '')}"
            f"{chr(10) if data.get('status') else ''}"
            f"{data.get('error', '')}"
            f"{chr(10) if data.get('error') else ''}"
            f"{data.get('message', '')}"
        )

        bui.textwidget(
            edit=self._status_text,
            text=bui.Lstr(
                resource=f'{self._r}.errorGettingFriendsText',
                subs=[('${ERROR}', full_error)],
            ),
        )
        bui.spinnerwidget(
            edit=self._spinner,
            visible=False,
        )

    def _finish_recreate(
        self,
        flist: dict,
        online_list: list,
        info_cache: dict,
    ):
        """Finish recreate on main thread."""

        self._loading = False

        if self._closed:
            return

        bui.textwidget(
            edit=self._status_text,
            text='',
        )
        
        bui.spinnerwidget(
            edit=self._spinner,
            visible=False,
        )

        self.recreate(
            flist,
            online_list,
            info_cache,
        )

    def respond_request(self, id: str, accept: bool):

        if accept:
            bui.getsound('powerup01').play()
        else:
            bui.getsound('powerdown01').play()

        Thread(
            target=self._respond_request_thread,
            args=(id, accept),
            daemon=True,
        ).start()

    def _respond_request_thread(
        self,
        id: str,
        accept: bool,
    ):

        mell.respond_friend_request(id, accept)

        bs.pushcall(
            bui.Call(self.recreate_async),
            from_other_thread=True,
        )

    def remove_friend(self, id: str, name: str):

        def do_it():

            bui.getsound('shieldDown').play()

            Thread(
                target=self._remove_friend_thread,
                args=(id,),
                daemon=True,
            ).start()

        ConfirmWindow(
            text=bui.Lstr(
                r=f'{self._r}.confirmRemoveFriend',
                subs=[('${NAME}', name)],
            ),
            action=bui.Call(do_it),
            origin_widget=self._container,
        )

    def _remove_friend_thread(
        self,
        id: str,
    ):

        mell.remove_friend(id)

        bs.pushcall(
            bui.Call(self.recreate_async),
            from_other_thread=True,
        )

    def add_friends_ui(self):
        AddFriendsWindow()

    def chat_with(self, id: str):
        FriendChatWindow(id)

    def recreate(
        self,
        flist: dict,
        online_list: list,
        info_cache: dict,
    ) -> None:

        if not self._subcontainer or not self._subcontainer.exists():
            return

        self._subcontainer.delete()

        sub_width = self._scrollwidget.get_screen_space_center()[0]
        sub_width = min(500, (self.c_width - 100) * 0.95)

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(sub_width, 0),
            background=False,
            selection_loops_to_parent=True,
        )

        self.friends_list = flist
        self.online_list = online_list

        self.friend_requests = flist.get('requests', [])
        self.friend_list = flist.get('friends', [])

        friend_height = 170
        scale = 1.2
        spacing = 40 * scale

        tdelay_inc = 0.1
        tdelay = 0.5

        total_height = (
            len(self.friend_list) * (friend_height + spacing)
        ) + spacing

        bui.containerwidget(
            edit=self._subcontainer,
            size=(sub_width, total_height),
        )

        current_y = total_height - friend_height - spacing

        for friend in self.friend_list:

            info = info_cache.get(friend, {})

            name = info.get(
                'username',
                info.get('account_name', 'Unknown'),
            )

            online = friend in self.online_list

            otext = (
                bui.Lstr(r=f'{self._r}.onlineText')
                if online else
                bui.Lstr(r=f'{self._r}.offlineText')
            )

            ocolor = (
                (0.8, 1, 0.8)
                if online else
                (0.5, 0.5, 0.5)
            )

            avatar = info.get('avatar', 'null')
            cm_avatar = info.get('cm_avatar', 'white')

            color = tuple(info.get('color', (1, 1, 1)))
            highlight = tuple(info.get('highlight', (1, 1, 1)))
            
            user_status = info.get('status', '')

            friend_width = sub_width + 10

            container = bui.containerwidget(
                parent=self._subcontainer,
                size=(friend_width, friend_height),
                position=(-40, current_y),
                scale=scale,
                background=False,
                selection_loops_to_parent=True,
            )

            d = 0.8

            bui.imagewidget(
                parent=container,
                size=(friend_width, friend_height),
                position=(0, 0),
                color=(
                    color[0] * d,
                    color[1] * d,
                    color[2] * d,
                ),
                texture=bui.gettexture('buttonSquareWide'),
                transition_delay=tdelay,
            )

            bui.textwidget(
                parent=container,
                text=str(name),
                size=(0, 0),
                scale=1.1,
                h_align='left',
                v_align='center',
                maxwidth=friend_width * 0.7,
                position=(105, friend_height - 45),
                transition_delay=tdelay,
            )
            
            if online:
                status = self.format_status(
                    mell.get_status_from_id(friend)
                )
                bui.textwidget(
                    parent=container,
                    text=status,
                    size=(0, 0),
                    scale=0.9,
                    color=(0.8, 0.8, 0.8),
                    h_align='left',
                    v_align='center',
                    maxwidth=friend_width * 0.8,
                    position=(105, friend_height - 70),
                    transition_delay=tdelay,
                )
                
            if user_status and online:
                # overall bubble scale
                bub_scale = 0.8

                # base bubble dimensions (unscaled)
                padding_x = 30
                bubble_h = 64
                cap_w = 16

                # text measurements
                text_scale = bub_scale + 0.1
                text_width = (
                    bui.get_string_width(user_status, suppress_warning=True)
                    * text_scale
                )

                # final bubble width
                bubble_w = text_width + (padding_x * 2)

                # position
                x = 60
                y = friend_height - 40

                # center/stretch section
                bui.imagewidget(
                    parent=container,
                    size=(bubble_w, bubble_h * bub_scale),
                    position=(x, y),
                    texture=bui.gettexture('bubbleMid'),
                    transition_delay=tdelay,
                )

                # left cap
                bui.imagewidget(
                    parent=container,
                    size=(cap_w * bub_scale, bubble_h * bub_scale),
                    position=(x - (cap_w * bub_scale) + 1, y),
                    texture=bui.gettexture('bubbleStart'),
                    transition_delay=tdelay,
                )

                # right cap
                bui.imagewidget(
                    parent=container,
                    size=(cap_w * bub_scale, bubble_h * bub_scale),
                    position=(x + bubble_w - 1, y),
                    texture=bui.gettexture('bubbleEnd'),
                    transition_delay=tdelay,
                )

                # text
                bui.textwidget(
                    parent=container,
                    text=user_status,
                    size=(0, 0),
                    scale=text_scale,
                    color=(0, 0, 0),
                    shadow=0,
                    h_align='left',
                    v_align='center',
                    position=(
                        x + padding_x * 0.5,
                        y + (bubble_h * bub_scale * 0.5),
                    ),
                    transition_delay=tdelay,
                )

            bui.textwidget(
                parent=container,
                text=otext,
                size=(0, 0),
                scale=0.9,
                shadow=0.2,
                color=ocolor,
                h_align='left',
                v_align='center',
                maxwidth=friend_width * 0.7,
                position=(friend_width * 0.8, friend_height - 45),
                transition_delay=tdelay,
            )

            bui.imagewidget(
                parent=container,
                size=(80, 80),
                position=(10, friend_height * 0.28),
                texture=bui.gettexture(avatar),
                mask_texture=bui.gettexture('characterIconMask'),
                tint_texture=bui.gettexture(cm_avatar),
                tint_color=color,
                tint2_color=highlight,
                transition_delay=tdelay,
            )

            d -= 0.2
            # buttons
            b_spacing = 65
            bx = 100
            bui.buttonwidget(
                parent=container,
                position=(bx, friend_height * 0.13),
                size=(60, 60),
                label='',
                color=(
                    color[0] * d,
                    color[1] * d,
                    color[2] * d,
                ),
                texture=bui.gettexture('buttonSquare'),
                icon=bui.gettexture('trashIcon'),
                on_activate_call=bui.Call(
                    self.remove_friend,
                    friend,
                    name,
                ),
                transition_delay=tdelay,
            )

            bui.buttonwidget(
                parent=container,
                position=(bx + b_spacing, friend_height * 0.13),
                size=(60, 60),
                label='',
                color=(
                    color[0] * d,
                    color[1] * d,
                    color[2] * d,
                ),
                texture=bui.gettexture('buttonSquare'),
                icon=bui.gettexture('chatIcon'),
                on_activate_call=bui.Call(
                    self.chat_with,
                    friend,
                ),
                transition_delay=tdelay,
            )
            
            # bui.buttonwidget(
                # parent=container,
                # position=(bx + (b_spacing * 2), friend_height * 0.13),
                # size=(60, 60),
                # label='',
                # color=(
                    # color[0] * d,
                    # color[1] * d,
                    # color[2] * d,
                # ),
                # texture=bui.gettexture('buttonSquare'),
                # icon=bui.gettexture('infoIcon'),
                # on_activate_call=bui.Call(
                    # self.chat_with,
                    # friend,
                # ),
                # transition_delay=tdelay,
            # )

            current_y -= friend_height + spacing
            tdelay += tdelay_inc

        for request in self.friend_requests:

            info = info_cache.get(request, {})

            name = info.get(
                'username',
                info.get('account_name', 'Unknown'),
            )

            avatar = info.get('avatar', 'null')
            cm_avatar = info.get('cm_avatar', 'white')

            color = tuple(info.get('color', (1, 1, 1)))
            highlight = tuple(info.get('highlight', (1, 1, 1)))

            friend_width = sub_width - 20

            container = bui.containerwidget(
                parent=self._subcontainer,
                size=(friend_width, friend_height),
                position=(20, current_y),
                background=False,
                selection_loops_to_parent=True,
            )

            bui.imagewidget(
                parent=container,
                size=(friend_width, friend_height),
                position=(0, 0),
                color=(0.3, 0.6, 0.3),
                texture=bui.gettexture('buttonSquareWide'),
                transition_delay=tdelay,
            )

            bui.textwidget(
                parent=container,
                text=bui.Lstr(
                    r=f'{self._r}.friendRequestFromUser',
                    subs=[('${NAME}', name)],
                ),
                size=(0, 0),
                scale=1.1,
                flatness=1.0,
                shadow=0.0,
                h_align='left',
                v_align='center',
                maxwidth=friend_width * 0.7,
                position=(110, friend_height - 40),
                transition_delay=tdelay,
            )

            bui.imagewidget(
                parent=container,
                size=(80, 80),
                position=(5, 35),
                texture=bui.gettexture(avatar),
                mask_texture=bui.gettexture('characterIconMask'),
                tint_texture=bui.gettexture(cm_avatar),
                tint_color=color,
                tint2_color=highlight,
                transition_delay=tdelay,
            )

            bui.buttonwidget(
                parent=container,
                position=(friend_width * 0.8, friend_height * 0.1),
                size=(60, 60),
                label='',
                color=(0.4, 0.7, 0.4),
                texture=bui.gettexture('buttonSquare'),
                icon=bui.gettexture('crossOut'),
                on_activate_call=bui.Call(
                    self.respond_request,
                    request,
                    False,
                ),
                transition_delay=tdelay,
            )

            bui.buttonwidget(
                parent=container,
                position=(friend_width * 0.65, friend_height * 0.1),
                size=(60, 60),
                label='',
                color=(0.4, 0.7, 0.4),
                texture=bui.gettexture('buttonSquare'),
                icon=bui.gettexture('acceptIcon'),
                on_activate_call=bui.Call(
                    self.respond_request,
                    request,
                    True,
                ),
                transition_delay=tdelay,
            )

            current_y -= friend_height + spacing
            tdelay += tdelay_inc
    
    def format_status(self, status: dict):
        hidden = status.get('hidden')
        if hidden:
            return ''
        # AAAGGHHHHHHHHHHHH
        activity = status.get('activity_full')
        amodn = status.get('activity_module')
        aclassn = status.get('activity_class')
        session = status.get('session_full')
        smodn = status.get('session_module')
        sclassn = status.get('session_class')
        online = status.get('online')
        try:
            amod = importlib.import_module(amodn)
            smod = importlib.import_module(smodn)
            acls = getattr(amod, aclassn)
            scls = getattr(smod, sclassn)
        except:
            acls = None
            scls = None
        # ok actually handle everything nicely
        if sclassn == 'MainMenuSession':
            return 'in main menu'
        if online:
            return 'playing online'
        name = getattr(acls, 'name', '???')
        score = status.get('score')
        rank = status.get('rank')
        if sclassn == 'CoopSession':
            return f'playing {name} score: {score}, rank: {rank}'
        return f'playing {name}'