# Released under the MIT License. See LICENSE for details.
#
"""Provides help related ui."""

from __future__ import annotations

from typing import override

import random

import bauiv1 as bui
import babase as ba


class HelpWindow(bui.MainWindow):
    """A window providing help on how to play."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('Help Window')

        self._r = 'helpWindow'

        getres = bui.app.lang.get_resource

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1050 if uiscale is bui.UIScale.SMALL else 750

        height = (
            700
            if uiscale is bui.UIScale.SMALL
            else 530 if uiscale is bui.UIScale.MEDIUM else 600
        )

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.8
            if uiscale is bui.UIScale.SMALL
            else 1.15 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(width - 90, screensize[0] / scale)
        target_height = min(height - 90, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        scroll_width = target_width
        scroll_height = target_height - 36
        scroll_bottom = yoffs - 64 - scroll_height

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(50, yoffs - 45),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(
                width * 0.5,
                yoffs - (47 if uiscale is bui.UIScale.SMALL else 25),
            ),
            size=(0, 0),
            text=bui.Lstr(
                resource=f'{self._r}.titleText',
                subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
            ),
            scale=0.9,
            maxwidth=scroll_width * 0.7,
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(scroll_width, scroll_height),
            position=(width * 0.5 - scroll_width * 0.5, scroll_bottom),
            simple_culling_v=120.0,
            capture_arrows=True,
            border_opacity=0.4,
            center_small_content_horizontally=True,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.widget(
                edit=self._scrollwidget,
                left_widget=bui.get_special_widget('back_button'),
            )

        bui.widget(
            edit=self._scrollwidget,
            right_widget=bui.get_special_widget('squad_button'),
        )
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )

        # self._sub_width = 810 if uiscale is bui.UIScale.SMALL else 660
        self._sub_width = 660
        self._sub_height = (
            4060
            + bui.app.lang.get_resource(f'{self._r}.someDaysExtraSpace')
            + bui.app.lang.get_resource(
                f'{self._r}.orPunchingSomethingExtraSpace'
            )
        )

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            claims_left_right=False,
        )

        spacing = 1.0
        h = self._sub_width * 0.5
        v = self._sub_height - 55
        logo_tex = bui.gettexture('logo')
        icon_buffer = 1.1
        header = (0.7, 1.0, 0.7, 1.0)
        header2 = (0.7, 0.9, 0.8, 1.0)
        paragraph = (0.8, 0.8, 1.0, 1.0)

        txt = bui.Lstr(
            resource=f'{self._r}.welcomeText',
            subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
        ).evaluate()
        txt_scale = 1.4
        txt_maxwidth = 480
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            res_scale=1.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            maxwidth=txt_maxwidth,
        )
        txt_width = min(
            txt_maxwidth,
            bui.get_string_width(txt, suppress_warning=True) * txt_scale,
        )

        icon_size = 70
        hval2 = h - (txt_width * 0.5 + icon_size * 0.5 * icon_buffer)

        app = bui.app
        assert app.classic is not None

        v -= spacing * 50.0
        txt = bui.Lstr(resource=f'{self._r}.someDaysText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=1.2,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )
        v -= spacing * 25.0 + getres(f'{self._r}.someDaysExtraSpace')
        txt_scale = 0.66
        txt = bui.Lstr(resource=f'{self._r}.orPunchingSomethingText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )
        v -= spacing * 27.0 + getres(f'{self._r}.orPunchingSomethingExtraSpace')
        txt_scale = 1.0
        txt = bui.Lstr(
            resource=f'{self._r}.canHelpText',
            subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
        ).evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=1.0,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
        )

        v -= spacing * 70.0
        txt_scale = 1.0
        txt = bui.Lstr(resource=f'{self._r}.toGetTheMostText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            flatness=1.0,
        )

        v -= spacing * 40.0
        txt_scale = 0.74
        txt = bui.Lstr(resource=f'{self._r}.friendsText').evaluate()
        hval2 = h - 220
        bui.textwidget(
            parent=self._subcontainer,
            position=(hval2, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=100,
            text=txt,
            h_align='right',
            color=header,
            v_align='center',
            flatness=1.0,
        )

        txt = bui.Lstr(
            resource=f'{self._r}.friendsGoodText',
            subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
        ).evaluate()
        txt_scale = 0.7
        bui.textwidget(
            parent=self._subcontainer,
            position=(hval2 + 10, v + 8),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=500,
            text=txt,
            h_align='left',
            color=paragraph,
            flatness=1.0,
        )

        app = bui.app

        v -= spacing * 45.0
        txt = (
            bui.Lstr(resource=f'{self._r}.devicesText').evaluate()
            if app.env.vr
            else bui.Lstr(resource=f'{self._r}.controllersText').evaluate()
        )
        txt_scale = 0.74
        hval2 = h - 220
        bui.textwidget(
            parent=self._subcontainer,
            position=(hval2, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=100,
            text=txt,
            h_align='right',
            v_align='center',
            color=header,
            flatness=1.0,
        )

        txt_scale = 0.7
        if not app.env.vr:
            infotxt = '.controllersInfoText'
            txt = bui.Lstr(
                resource=self._r + infotxt,
                fallback_resource=f'{self._r}.controllersInfoText',
                subs=[
                    ('${APP_NAME}', bui.Lstr(resource='titleText')),
                    ('${REMOTE_APP_NAME}', bui.get_remote_app_name()),
                ],
            ).evaluate()
        else:
            txt = bui.Lstr(
                resource=f'{self._r}.devicesInfoText',
                subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
            ).evaluate()

        bui.textwidget(
            parent=self._subcontainer,
            position=(hval2 + 10, v + 8),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=500,
            max_height=105,
            text=txt,
            h_align='left',
            color=paragraph,
            flatness=1.0,
        )

        v -= spacing * 150.0

        txt = bui.Lstr(resource=f'{self._r}.controlsText').evaluate()
        txt_scale = 1.4
        txt_maxwidth = 480
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            res_scale=1.5,
            maxwidth=txt_maxwidth,
        )
        txt_width = min(
            txt_maxwidth,
            bui.get_string_width(txt, suppress_warning=True) * txt_scale,
        )
        icon_size = 70

        hval2 = h - (txt_width * 0.5 + icon_size * 0.5 * icon_buffer)

        v -= spacing * 45.0
        
        cfgget = ba.app.config.get
        c1name = cfgget('squda_ch1name')
        txt_scale = 0.7
        txt = bui.Lstr(
            resource=f'{self._r}.controlsSubtitleText',
            subs=[('${SPAZ}', c1name)],
        ).evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            flatness=1.0,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
        )
        v -= spacing * 160.0

        sep = 70
        icon_size = 100
        # icon_size_2 = 30
        hval2 = h - sep
        vval2 = v
        bui.buttonwidget(
            parent=self._subcontainer,
            label='',
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonPunch'),
            color=(1, 0.7, 0.3),
            selectable=False,
            enable_sound=False,
            on_activate_call=bui.getsound('punchSFX/generic').play,
        )

        txt_scale = getres(f'{self._r}.punchInfoTextScale')
        txt = bui.Lstr(resource=f'{self._r}.punchInfoText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h - sep - 185 + 70, v + 120),
            size=(0, 0),
            scale=txt_scale,
            flatness=1.0,
            text=txt,
            h_align='center',
            color=(1, 0.7, 0.3, 1.0),
            v_align='top',
        )

        hval2 = h + sep
        vval2 = v
        bui.buttonwidget(
            parent=self._subcontainer,
            label='',
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonBomb'),
            color=(1, 0.3, 0.3),
            selectable=False,
            enable_sound=False,
            on_activate_call=bui.getsound('explosion01').play,
        )

        txt = bui.Lstr(resource=f'{self._r}.bombInfoText').evaluate()
        txt_scale = getres(f'{self._r}.bombInfoTextScale')
        bui.textwidget(
            parent=self._subcontainer,
            position=(h + sep + 50 + 60, v - 35),
            size=(0, 0),
            scale=txt_scale,
            flatness=1.0,
            maxwidth=270,
            text=txt,
            h_align='center',
            color=(1, 0.3, 0.3, 1.0),
            v_align='top',
        )

        hval2 = h
        vval2 = v + sep
        bui.buttonwidget(
            parent=self._subcontainer,
            label='',
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonPickUp'),
            color=(0.5, 0.5, 1),
            selectable=False,
            enable_sound=False,
            on_activate_call=bui.getsound('voicelines/kris/pickup').play,
        )

        txtl = bui.Lstr(resource=f'{self._r}.pickUpInfoText')
        txt_scale = getres(f'{self._r}.pickUpInfoTextScale')
        bui.textwidget(
            parent=self._subcontainer,
            position=(h + 60 + 120, v + sep + 50),
            size=(0, 0),
            scale=txt_scale,
            flatness=1.0,
            text=txtl,
            h_align='center',
            color=(0.5, 0.5, 1, 1.0),
            v_align='top',
        )

        hval2 = h
        vval2 = v - sep
        bui.buttonwidget(
            parent=self._subcontainer,
            label='',
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonJump'),
            color=(0.4, 1, 0.4),
            selectable=False,
            enable_sound=False,
            on_activate_call=bui.getsound('smb1_jump').play,
        )

        txt = bui.Lstr(resource=f'{self._r}.jumpInfoText').evaluate()
        txt_scale = getres(f'{self._r}.jumpInfoTextScale')
        bui.textwidget(
            parent=self._subcontainer,
            position=(h - 250 + 75, v - sep - 15 + 30),
            size=(0, 0),
            scale=txt_scale,
            flatness=1.0,
            text=txt,
            h_align='center',
            color=(0.4, 1, 0.4, 1.0),
            v_align='top',
        )

        txt = bui.Lstr(resource=f'{self._r}.runInfoText').evaluate()
        txt_scale = getres(f'{self._r}.runInfoTextScale')
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v - sep - 100),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.93,
            flatness=1.0,
            text=txt,
            h_align='center',
            color=(0.7, 0.7, 1.0, 1.0),
            v_align='center',
        )

        v -= spacing * 280.0

        txt = bui.Lstr(resource=f'{self._r}.powerupsText').evaluate()
        txt_scale = 1.4
        txt_maxwidth = 480
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            maxwidth=txt_maxwidth,
        )
        txt_width = min(
            txt_maxwidth,
            bui.get_string_width(txt, suppress_warning=True) * txt_scale,
        )
        icon_size = 70
        hval2 = h - (txt_width * 0.5 + icon_size * 0.5 * icon_buffer)

        v -= spacing * 50.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale')
        txt = bui.Lstr(resource=f'{self._r}.powerupsSubtitleText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )

        v -= spacing * 1.0

        mm1 = -250
        mm2 = -205
        mm3 = 0
        icon_size = 50
        shadow_size = 80
        shadow_offs_x = 3
        shadow_offs_y = -4
        t_big = 1.1
        t_small = 0.65

        shadow_tex = bui.gettexture('shadowSharp')

        for tex in [
            'powerupPunch',
            'powerupShield',
            'powerupBomb',
            'powerupHealth',
            'powerupIceBombs',
            'powerupImpactBombs',
            'powerupStickyBombs',
            'powerupLandMines',
            'powerupCurse',
            'powerupMetal',
            'powerupStrong',
            'powerupSponge',
            'powerupRandom',
            'powerupDeton',
            'powerupShotgun',
            'powerupFireball',
            'powerupBloxy',
            'powerupHook',
            'curseGrace',
            'curseDozer',
            'curseKookoo',
            'curseIre',
            'curseSorrow',
            'curseLitany',
        ]:
            name = bui.Lstr(resource=f'{self._r}.' + tex + 'NameText')
            desc = bui.Lstr(resource=f'{self._r}.' + tex + 'DescriptionText')

            v -= spacing * 60.0

            bui.imagewidget(
                parent=self._subcontainer,
                size=(shadow_size, shadow_size),
                position=(
                    h + mm1 + shadow_offs_x - 0.5 * shadow_size,
                    v + shadow_offs_y - 0.5 * shadow_size,
                ),
                texture=shadow_tex,
                color=(0, 0, 0),
                opacity=0.5,
            )
            bui.buttonwidget(
                parent=self._subcontainer,
                size=(icon_size, icon_size),
                position=(h + mm1 - 0.5 * icon_size, v - 0.5 * icon_size),
                texture=bui.gettexture(tex),
                label='',
                selectable=False,
                color=(1.5, 1.5, 1.5),
                enable_sound=False,
                on_activate_call=bui.WeakCall(self.plpwpsound, tex),
            )

            txt_scale = t_big
            txtl = name
            bui.textwidget(
                parent=self._subcontainer,
                position=(h + mm2, v + 3),
                size=(0, 0),
                scale=txt_scale,
                maxwidth=200,
                flatness=1.0,
                text=txtl,
                h_align='left',
                color=header2,
                v_align='center',
            )
            txt_scale = t_small
            txtl = desc
            bui.textwidget(
                parent=self._subcontainer,
                position=(h + mm3, v),
                size=(0, 0),
                scale=txt_scale,
                maxwidth=300,
                flatness=1.0,
                text=txtl,
                h_align='left',
                color=paragraph,
                v_align='center',
                res_scale=0.5,
            ) 
        v -= spacing * 80

        txt = bui.Lstr(resource=f'{self._r}.mechanicsText').evaluate()
        txt_scale = 1.4
        txt_maxwidth = 480
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            maxwidth=txt_maxwidth,
        )   
        v -= spacing * 40.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale')
        txt = bui.Lstr(resource=f'{self._r}.mechanicsSubtitleText').evaluate()
        tex = bui.gettexture('circleZigZag')
        scale = 40
        yfuckoffs = 20
        txt_width = min(
            txt_maxwidth,
            bui.get_string_width(txt, suppress_warning=True) * txt_scale,
        )     
        hval2 = h - (txt_width * 0.4)
        hval3 = h - (txt_width)
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )
        
        v -= spacing * 40.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale') + 0.2
        txt = bui.Lstr(resource=f'{self._r}.mechanicsChargeTitle').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            maxwidth=txt_maxwidth,
        )
        
        v -= spacing * 120.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale') 
        txt = bui.Lstr(resource=f'{self._r}.mechanicsChargeText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )
        
        v -= spacing * 122.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale') + 0.2
        txt = bui.Lstr(resource=f'{self._r}.mechanicsSuperTitle').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            maxwidth=txt_maxwidth,
        )
        
        v -= spacing * 110.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale') 
        txt = bui.Lstr(resource=f'{self._r}.mechanicsSuperText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )
        
        v -= spacing * 110.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale') + 0.2
        txt = bui.Lstr(resource=f'{self._r}.mechanicsParryTitle').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            maxwidth=txt_maxwidth,
        )
        
        v -= spacing * 70.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale') 
        txt = bui.Lstr(resource=f'{self._r}.mechanicsParryText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )
        
        v -= spacing * 70.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale') + 0.2
        txt = bui.Lstr(resource=f'{self._r}.mechanicsHexplodeTitle').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            maxwidth=txt_maxwidth,
        )
        
        v -= spacing * 55.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale') 
        txt = bui.Lstr(resource=f'{self._r}.mechanicsHexplodeText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )
        
        v -= spacing * 100.0
        txt = getres(f'{self._r}.gimmicksText')
        txt_scale = 1.4
        txt_maxwidth = 480
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            maxwidth=txt_maxwidth,
        )   
        
        v -= spacing * 50.0
        txt_scale = 1
        txt = bui.Lstr(resource=f'{self._r}.gimmicksSubtitleText').evaluate()
        scale = 40
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            maxwidth=txt_maxwidth,
        )   
        v -= spacing * 50.0
        txt_scale = 0.9
        txt = bui.Lstr(resource=f'{self._r}.gimmicksIsaacTitle').evaluate()
        scale = 40
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header2,
            v_align='center',
            maxwidth=txt_maxwidth,
        )   
        v -= spacing * 40.0
        txt_scale = 0.8
        txt = bui.Lstr(resource=f'{self._r}.gimmicksIsaacText').evaluate()
        scale = 40
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='top',
            maxwidth=txt_maxwidth,
        )   
        v -= spacing * 350.0
        txt_scale = 1.1
        txt = bui.Lstr(resource=f'{self._r}.gimmicksBallerTitle').evaluate()
        scale = 40
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header2,
            v_align='center',
            maxwidth=txt_maxwidth,
        )   
        v -= spacing * 50.0
        txt_scale = 1.2
        txt = bui.Lstr(resource=f'{self._r}.gimmicksBallerText').evaluate()
        scale = 40
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='top',
            maxwidth=txt_maxwidth + 60,
        )   
        
        
        
    def _play_sound(self, text: str, num: int) -> None:
        bui.getsound(text + str(random.randint(1, num))).play()
        
    def plpwpsound(self, text: str) -> None:
        if text == 'powerupPunch':
            bui.getsound('punchSFX/super').play()
        elif text == 'powerupShield':
            bui.getsound('shieldUp').play()
        elif text == 'powerupBomb':
            bui.getsound('fuse01').play()
        elif text == 'powerupHealth':
            bui.getsound('healthPowerup').play()
        elif text == 'powerupIceBombs':
            bui.getsound('freeze').play()
        elif text == 'powerupImpactBombs':
            bui.getsound('warnBeep').play()
        elif text == 'powerupStickyBombs':
            bui.getsound('stickyImpact').play()
        elif text == 'powerupLandMines':
            bui.getsound('activateBeep').play()
        elif text == 'powerupCurse':
            bui.getsound('crazyOver').play()
        elif text == 'powerupMetal':
            bui.getsound('metalcap').play()
        elif text == 'powerupStrong':
            bui.getsound('punchSFX/weak1').play()
        elif text == 'powerupSponge':
            bui.getsound('spongebob').play()
        elif text == 'powerupRandom':
            bui.getsound('okitem').play()
        elif text == 'powerupShotgun':
            bui.getsound('shotgunload').play()
        elif text == 'powerupDeton':
            bui.getsound('menu_sel').play()
        elif text == 'powerupBloxy':
            bui.getsound('cola').play()
        elif text == 'powerupHook':
            bui.getsound('hook_throw').play()
        elif text == 'powerupFireball':
            bui.getsound('smb1_fireball').play()
        elif text == 'curseGrace':
            bui.getsound('blank').play()
        elif text == 'curseDozer':
            bui.getsound('entities/dozer/default/ticking').play()
        elif text == 'curseKookoo':
            bui.getsound('kwarnin').play()
        elif text == 'curseIre':
            bui.getsound('entities/ire/default/ready').play()
        elif text == 'curseSorrow':
            bui.getsound('safter').play()
        elif text == 'curseLitany':
            bui.getsound('entities/litany/default/ticking').play()
        else:
            print(f'HelpWindow error: {text} not in plpwpsound')
            bui.getsound('error').play()


    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
