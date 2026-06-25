# Released under the MIT License. See LICENSE for details.
#
"""Snippets of code for use by the c++ layer."""
# (most of these are self-explanatory)
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import babase as ba

import _bascenev1
import bascenev1 as bs
import bauiv1 as bui
import shlex
import ast

if TYPE_CHECKING:
    from typing import Any

    import bascenev1

_end_votes: set[str] = set()
_vote_activity_id: int | None = None
reset_timer = None

def servermessage(msg: str):
    bs.chatmessage(msg, sender_override='Server')
    
def parse_tuple(arg, display):
    try:
        return ast.literal_eval(arg)
    except Exception:
        servermessage(f'{display}, invalid format: {arg}')
        return None
commands = {}

class Command:
    def __init__(
        self, 
        func, 
        usage: str ='', 
        desc: str ='', 
        owner_only: bool = False
    ):
        self.func = func
        self.usage = usage
        self.desc = desc

def register(name, usage='', desc=''):
    def decorator(func):
        commands[name] = Command(func, usage, desc)
        return func
    return decorator

class CommandContext:
    def __init__(self, msg, roster_entry, player_index):
        self.msg = msg
        self.parts = shlex.split(msg)
        self.cmd = self.parts[0].lower()
        self.args = self.parts[1:]

        self.display = roster_entry.get('display_string', 'Unknown Player')
        self.account_id = roster_entry.get('account_id')
        self.activity = bs.get_foreground_host_activity()
        self.is_sp = roster_entry.get('singleplayer', False)

        self.player = None

        if self.activity:
            players = self.activity.players
            try:
                if 0 <= player_index < len(players):
                    self.player = players[player_index]
            except TypeError:
                self.player = None

@register('/help', desc='List commands', usage='/help')
def cmd_help(ctx: CommandContext):
    for name, cmd in commands.items():
        servermessage(f' {name} - {cmd.desc} | {cmd.usage}')

@register('/char', usage='/char <name>', desc='Change character')
def cmd_char(ctx: CommandContext):
    if not ctx.args:
        bs.chatmessage(f'{ctx.display}, usage: {commands[ctx.cmd].usage}')
        return

    name = ctx.args[0]

    try:
        character = bs.app.classic.spaz_appearances[name]
    except KeyError:
        servermessage(f'{ctx.display}: character "{name}" doesn\'t exist!')
        return

    ctx.player.character = character.name

    if ctx.player.actor:
        with ctx.activity.context:
            ctx.player.actor.character = character.name
            ctx.player.actor.reset_character()
            if ctx.player.sessionplayer:
                sp = ctx.player.sessionplayer
                ctx.player.sessionplayer.setdata(
                    team=sp.sessionteam,
                    character=character.name,
                    color=sp.color,
                    highlight=sp.highlight,
                )

@register('/color', usage='/color (r, g, b)', desc='Set player color')
def cmd_color(ctx: CommandContext):
    if not ctx.args:
        servermessage(f'{ctx.display}, usage: {commands[ctx.cmd].usage}')
        return

    value = parse_tuple(' '.join(ctx.args), ctx.display)
    if value is None:
        return

    with ctx.activity.context:
        ctx.player.color = value
        if ctx.player.actor and ctx.player.actor.node:
            ctx.player.actor.node.color = value
            ctx.player.actor.node.name_color = value
            if ctx.player.sessionplayer:
                sp = ctx.player.sessionplayer
                ctx.player.sessionplayer.setdata(
                    team=sp.sessionteam,
                    character=sp.character,
                    color=value,
                    highlight=sp.highlight,
                )

@register('/highlight', usage='/highlight (r, g, b)', desc='Set highlight color')
def cmd_highlight(ctx: CommandContext):
    if not ctx.args:
        servermessage(f'{ctx.display}, usage: {commands[ctx.cmd].usage}')
        return

    value = parse_tuple(' '.join(ctx.args), ctx.display)
    if value is None:
        return

    with ctx.activity.context:
        ctx.player.highlight = value
        if ctx.player.actor and ctx.player.actor.node:
            ctx.player.actor.node.highlight = value
            if ctx.player.sessionplayer:
                sp = ctx.player.sessionplayer
                ctx.player.sessionplayer.setdata(
                    team=sp.sessionteam,
                    character=sp.character,
                    color=sp.color,
                    highlight=value,
                )

@register('/end', usage='/end', desc='Vote to, or end the game')
def cmd_end(ctx: CommandContext):
    def reset_end_votes():
        _end_votes.clear()
        with ctx.activity.context:
            bs.getsound('vote_failed').play()
            bs.broadcastmessage("The vote was canceled (not enough votes).")
            
    # In singleplayer, end immediately
    if ctx.is_sp:
        bs.broadcastmessage('Ending activity (/end was sent)')
        if ctx.activity:
            with ctx.activity.context:
                if hasattr(ctx.activity, 'end_game'):
                    ctx.activity.end_game()
                    
    player = ctx.activity.players.index(ctx.player)
    
    # In Multiplayer, do voting
    if player in _end_votes:
        servermessage(f'{player.getname()}, you already voted!')
        return

    global reset_timer
    _end_votes.add(player)
    needed = int(len(bs.get_game_roster()) * 0.5)
    current = len(_end_votes)
    with ctx.activity.context:
        if len(_end_votes) <= 1:
            bs.getsound('vote_started').play()
        else:
            bs.getsound('vote_added').play()
        reset_timer = ba.AppTimer(8, reset_end_votes)
        bs.broadcastmessage(
            f'{ctx.player.getname()} voted to end the game '
            f'({current}/{needed})'
        )
    
    if current >= needed:
        _end_votes.clear()
        with ctx.activity.context:
            bs.broadcastmessage('Vote passed! Ending activity.')
            reset_timer = None
            bs.getsound('vote_passed').play()
            if hasattr(ctx.activity, 'end_game'):
                ctx.activity.end_game()

@register('/cursor', usage='/cursor', desc='Toggles your cursor (DOES NOT MAKE YOU SAFE)')
def cmd_cur(ctx: CommandContext):
    with ctx.activity.context:
        if not ctx.player.cursor:
            # Make the cursor.
            from bascenev1lib.actor.cursor import Cursor
            cursor = Cursor(ctx.player)
            # Connect the player.
            ctx.player.cursor = cursor
            cursor.connect_controls()
            # Keep em knocked out (just for the funsies)
            def do_knockout(player: bs.Player):
                if not player.actor.node:
                    return
                player.actor.node.handlemessage(
                    'knockout', 100
                )
            ctx.player.knockout_timer = bs.Timer(
                0.1, 
                bs.Call(do_knockout, player=ctx.player),
                repeat=True
            )
        else:
            # Kill the cursor.
            ctx.player.cursor.handlemessage(
                bs.DieMessage()
            )
            ctx.player.cursor = None
            # Give back our player their controls.
            if ctx.player.actor._connected_to_player:
                ctx.player.actor.connect_controls_to_player()
            # Wake em up.
            if getattr(ctx.player, 'knockout_timer', None):
                ctx.player.knockout_timer = None

@register('/modvote', usage='/modvote', desc='Start a modifier vote')
def cmd_modvote(ctx: CommandContext):
    with ctx.activity.context:
        from bascenev1lib.modifiers.vote_ui import ModifierVoteDelegate
        ModifierVoteDelegate().autoretain()

def launch_main_menu_session() -> None:
    if getattr(ba.app, 'intro_done', None) is None:
        disable_intro = ba.app.config.get('squda_skipintro', False)
        ba.app.intro_done = disable_intro
    if not ba.app.intro_done:
        from bascenev1lib.intros.session import IntroSession
        _bascenev1.new_host_session(IntroSession)
        ba.app.intro_done = True
        return
    _bascenev1.new_host_session(babase.app.classic.get_main_menu_session())

def get_player_icon(sessionplayer: bascenev1.SessionPlayer) -> dict[str, Any]:
    info = sessionplayer.get_icon_info()
    return {
        'texture': _bascenev1.gettexture(info['texture']),
        'tint_texture': _bascenev1.gettexture(info['tint_texture']),
        'tint_color': info['tint_color'],
        'tint2_color': info['tint2_color'],
    }

def handle_command(msg: str, roster_entry: dict, player_index: int):
    ctx = CommandContext(msg, roster_entry, player_index)

    if not ctx.activity:
        return msg

    command = commands.get(ctx.cmd)
    if not command:
        return msg

    if not ctx.player:
        servermessage(f'{ctx.display}, you must be in-game!')
        return msg

    command.func(ctx)
    return msg

def filter_chat_message(msg: str, client_id: int) -> str | None:
    roster = bs.get_game_roster()
    activity = bs.get_foreground_host_activity()
    if not activity:
        return msg
    # ── Singleplayer fallback ────────────────────
    if not roster:
        plus = bui.app.plus
        fake_entry = {
            'client_id': 0,
            'display_string': plus.get_v1_account_display_string(),
            'account_id': None,
            'is_admin': True,
            'singleplayer': True
        }

        if msg.startswith('/'):
            return handle_command(
                msg=msg,
                roster_entry=fake_entry,
                player_index=0
            )
        if activity:
            with activity.context:
                try:
                    # We're in singleplayer, so presumably
                    # whoever's sending the message is P1.
                    player = activity.players[0]
                    player.actor.say(msg)
                except Exception as e:
                    pass
        return msg

    # ── Multiplayer ──────────────────────────────
    roster_entry = next(
        (p for p in roster if p.get('client_id') == client_id),
        None
    )

    if roster_entry is None:
        return msg

    display = roster_entry.get('display_string', 'Unknown Player')
    client_id = roster_entry.get('client_id')
    players = roster_entry.get('players')
    player_id = None
    if players:
        name = players[0].get('name')
        player = next(
            (plr for plr in activity.players if plr.getname() == name),
            None
        )
        try:
            player_id = activity.players.index(player)
        except:
            player_id = None

    if msg.startswith('/'):
        return handle_command(
            msg=msg,
            roster_entry=roster_entry,
            player_index=player_id
        )
    if activity:
        with activity.context:
            try:
                player = activity.players[player_id]
                player.actor.say(msg, melblow=False)
            except Exception as e:
                pass
    return msg



def local_chat_message(msg: str) -> None:
    classic = babase.app.classic
    assert classic is not None
    party_window = (
        None if classic.party_window is None else classic.party_window()
    )

    if party_window is not None:
        party_window.on_chat_message(msg)
