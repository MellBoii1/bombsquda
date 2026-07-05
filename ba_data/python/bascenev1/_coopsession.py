# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to coop-mode sessions."""
from __future__ import annotations

from typing import TYPE_CHECKING, override

import babase

import _bascenev1
from bascenev1._session import Session
from bascenev1lib.actor.background import Background
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Callable, Sequence

    import bascenev1

TEAM_COLORS = [(0.2, 0.4, 1.6)]
TEAM_NAMES = ['Good Guys']


class CoopSession(Session):
    """A session which runs cooperative-mode games.

    These generally consist of 1-4 players against the computer and
    include functionality such as high score lists.
    """

    use_teams = True
    use_team_colors = False

    # Note: even though these are instance vars, we annotate them at the
    # class level so that docs generation can access their types.

    campaign: bascenev1.Campaign | None
    """The baclassic.Campaign instance this Session represents, or None if
       there is no associated Campaign."""

    def __init__(self) -> None:
        """Instantiate a co-op mode session."""
        # pylint: disable=cyclic-import
        from bascenev1lib.activity.coopjoin import CoopJoinActivity

        babase.increment_analytics_count('Co-op session start')
        app = babase.app
        classic = app.classic
        assert classic is not None

        # If they passed in explicit min/max, honor that.
        # Otherwise defer to user overrides or defaults.
        if 'min_players' in classic.coop_session_args:
            min_players = classic.coop_session_args['min_players']
        else:
            min_players = 1
        if 'max_players' in classic.coop_session_args:
            max_players = classic.coop_session_args['max_players']
        else:
            max_players = app.config.get('Coop Game Max Players', 4)
        if 'submit_score' in classic.coop_session_args:
            submit_score = classic.coop_session_args['submit_score']
        else:
            submit_score = True

        # print('FIXME: COOP SESSION WOULD CALC DEPS.')
        depsets: Sequence[bascenev1.DependencySet] = []

        super().__init__(
            depsets,
            team_names=TEAM_NAMES,
            team_colors=TEAM_COLORS,
            min_players=min_players,
            max_players=max_players,
            submit_score=submit_score,
        )

        # Tournament-ID if we correspond to a co-op tournament (otherwise None)
        self.tournament_id: str | None = classic.coop_session_args.get(
            'tournament_id'
        )

        self.campaign = classic.getcampaign(
            classic.coop_session_args['campaign']
        )
        self.campaign_level_name: str = classic.coop_session_args['level']
        self._arcade_mode = False
        self._arcade_lives = 3
        self._total_score = 0
        if self._arcade_mode:
            self._arcade_lives_text = bs.newnode(
                'text',
                attrs={
                    'v_attach': 'bottom',
                    'h_align': 'center',
                    'position': (0, 80),
                    'scale': 0.8,
                    'color': (0.9, 0.9, 0.9),
                    'opacity': 0.6,
                    'front': True,
                }
            )
            self._arcade_score_text = bs.newnode(
                'text',
                attrs={
                    'v_attach': 'bottom',
                    'h_align': 'center',
                    'position': (0, 10),
                    'scale': 1.2,
                    'front': True,
                }
            )
            self._arcade_score_info_text = bs.newnode(
                'text',
                attrs={
                    'v_attach': 'bottom',
                    'h_align': 'center',
                    'position': (0, 50),
                    'color': (0.6, 0.7, 0.9),
                    'scale': 0.9,
                    'opacity': 0.8,
                    'front': True,
                }
            )
            self._update_for_arcade()

        self._ran_tutorial_activity = False
        self._tutorial_activity: bascenev1.Activity | None = None
        self._custom_menu_ui: list[dict[str, Any]] = []
        self.amaj_players = 0
        self.endTimer = None

        # Start our joining screen.
        self.setactivity(_bascenev1.newactivity(CoopJoinActivity))

        self._next_game_instance: bascenev1.GameActivity | None = None
        self._next_game_level_name: str | None = None
        self._update_on_deck_game_instances()
    
    def _update_for_arcade(self):
        if not self._arcade_mode:
            return
        self._arcade_lives_text.text = bs.Lstr(
            value='${A}: ${B}',
            subs=[
                ('${A}', bs.Lstr(r='livesText')),
                ('${B}', str(self._arcade_lives)),
            ],
        )
        self._arcade_score_info_text.text = bs.Lstr(
            value='- ${A} -',
            subs=[
                ('${A}', bs.Lstr(r='totalScoreText')),
            ],
        )
        self._arcade_score_text.text = str(self._total_score)
    
    def _show_gameover_text(self):
        time = 1.5
        def text(h_align: str):
            return bs.newnode(
                'text',
                attrs={
                    'h_align': h_align,
                    'position': (-600, 0),
                    'scale': 2.5,
                    'opacity': 1,
                    'flatness': 0.6,
                    'shadow': 0.1,
                    'front': True,
                }
            )
        game_text = text(h_align='right')
        over_text = text(h_align='left')
        game_text.text = bs.Lstr(r='gameoverGameText')
        over_text.text = bs.Lstr(r='gameoverOverText')
        xoffnum = 800
        xnum = 20
        xoffs = 15
        v = -30
        bs.animate_array(
            game_text,
            'position',
            2,
            {
                0: (-xoffnum, v),
                time: (-xnum + xoffs, v),
                9: (-xnum + xoffs, v),
                9.5: (-xnum + xoffs, 600),
            }
        )
        bs.animate_array(
            over_text,
            'position',
            2,
            {
                0: (xoffnum, v),
                time: (xnum + xoffs, v),
                9: (xnum + xoffs, v),
                9.5: (xnum + xoffs, 600),
            }
        )

    def get_current_game_instance(self) -> bascenev1.GameActivity:
        """Get the game instance currently being played."""
        return self._current_game_instance

    def _update_on_deck_game_instances(self) -> None:
        # pylint: disable=cyclic-import
        from bascenev1._gameactivity import GameActivity

        classic = babase.app.classic
        assert classic is not None

        # Instantiate levels we may be running soon to let them load in the bg.

        # Build an instance for the current level.
        assert self.campaign is not None
        level = self.campaign.getlevel(self.campaign_level_name)
        gametype = level.gametype
        settings = level.get_settings()

        # Make sure all settings the game expects are present.
        neededsettings = gametype.get_available_settings(type(self))
        for setting in neededsettings:
            if setting.name not in settings:
                settings[setting.name] = setting.default

        newactivity = _bascenev1.newactivity(gametype, settings)
        assert isinstance(newactivity, GameActivity)
        self._current_game_instance: GameActivity = newactivity

        # Find the next level and build an instance for it too.
        levels = self.campaign.levels
        level = self.campaign.getlevel(self.campaign_level_name)

        nextlevel: bascenev1.Level | None
        if level.index < len(levels) - 1:
            nextlevel = levels[level.index + 1]
        else:
            nextlevel = None
        if nextlevel:
            gametype = nextlevel.gametype
            settings = nextlevel.get_settings()

            # Make sure all settings the game expects are present.
            neededsettings = gametype.get_available_settings(type(self))
            for setting in neededsettings:
                if setting.name not in settings:
                    settings[setting.name] = setting.default

            # We wanna be in the activity's context while taking it down.
            newactivity = _bascenev1.newactivity(gametype, settings)
            assert isinstance(newactivity, GameActivity)
            self._next_game_instance = newactivity
            self._next_game_level_name = nextlevel.name
        else:
            self._next_game_instance = None
            self._next_game_level_name = None

        # Special case:
        # If our current level is 'onslaught training', instantiate
        # our tutorial so its ready to go. (if we haven't run it yet).
        if (
            self.campaign_level_name == 'Onslaught Training'
            and self._tutorial_activity is None
            and not self._ran_tutorial_activity
        ):
            from bascenev1lib.tutorial import TutorialActivity

            self._tutorial_activity = _bascenev1.newactivity(TutorialActivity)

    @override
    def get_custom_menu_entries(self) -> list[dict[str, Any]]:
        return self._custom_menu_ui

    @override
    def on_player_leave(self, sessionplayer: bascenev1.SessionPlayer) -> None:
        # Save the sessionplayer's activityplayer.
        player = sessionplayer.activityplayer
        if player:
            if player.actor:
                # If within reasonable hitpoints or
                # alive, allow mid activity rejoining.
                if player.actor.hitpoints >= 410 and not self._arcade_mode:
                    self.amaj_players += 1
                    bs.broadcastmessage(
                        bs.Lstr(
                            r='playerLeftCoopSpotText',
                            s=[('${NAME}', player.getname())]
                        )
                    )
        super().on_player_leave(sessionplayer)
        self._handle_empty_activity()
        
    @override
    def _add_chosen_player(
        self, chooser: bascenev1.Chooser
    ) -> bascenev1.SessionPlayer:
        from bascenev1._team import SessionTeam

        sessionplayer = chooser.getplayer()
        assert sessionplayer in self.sessionplayers, (
            'SessionPlayer not found in session '
            'player-list after chooser selection.'
        )

        activity = self._activity_weak()
        assert activity is not None

        # Reset the player's input here, as it is probably
        # referencing the chooser which could inadvertently keep it alive.
        sessionplayer.resetinput()

        # We can pass it to the current activity if it has already begun
        # (otherwise it'll get passed once begin is called).
        pass_to_activity = (
            activity.has_begun() and not activity.is_joining_activity
        )

        # However, if we're not allowing mid-game joins, don't actually pass;
        # just announce the arrival and say they'll partake next round.
        if pass_to_activity:
            if self.amaj_players <= 0:
                pass_to_activity = False
                with self.context:
                    _bascenev1.broadcastmessage(
                        babase.Lstr(
                            resource='playerDelayedJoinText',
                            subs=[
                                ('${PLAYER}', sessionplayer.getname(full=True))
                            ],
                        ),
                        color=(0, 1, 0),
                    )
        if self.amaj_players > 0:
            self.amaj_players -= 1

        # If we're a non-team session, each player gets their own team.
        # (keeps mini-game coding simpler if we can always deal with teams).
        if self.use_teams:
            sessionteam = chooser.sessionteam
        else:
            our_team_id = self._next_team_id
            self._next_team_id += 1
            sessionteam = SessionTeam(
                team_id=our_team_id,
                color=chooser.get_color(),
                name=chooser.getplayer().getname(full=True, icon=False),
            )

            # Add player's team to the Session.
            self.sessionteams.append(sessionteam)

            with self.context:
                try:
                    self.on_team_join(sessionteam)
                except Exception:
                    logging.exception('Error in on_team_join for %s.', self)

            # Add player's team to the Activity.
            if pass_to_activity:
                activity.add_team(sessionteam)

        assert sessionplayer not in sessionteam.players
        sessionteam.players.append(sessionplayer)
        sessionplayer.setdata(
            team=sessionteam,
            character=chooser.get_character_name(),
            color=chooser.get_color(),
            highlight=chooser.get_highlight(),
        )

        self.stats.register_sessionplayer(sessionplayer)
        if pass_to_activity:
            activity.add_player(sessionplayer)
            if getattr(self, 'scheduling_end', False):
                self.unschedule_end_game()
        return sessionplayer
    
    def schedule_end_game(self) -> None:
        from bascenev1lib.actor.overhead_text import OverheadText
        activity = self.getactivity()
        self.scheduling_end = True
        with activity.context:
            def try_end():
                if not activity.players and self.sessionplayers:
                    self.restart()
                else:
                    activity.end()
            self.endTimer = bs.Timer(20.0, try_end)
            OverheadText(babase.Lstr(resource='endingSoonCoop'))
    
    def unschedule_end_game(self) -> None:
        self.scheduling_end = False
        bs.getsound('dingSmallHigh').play()
        activity = self.getactivity()
        with activity.context:
            self.endTimer = None

    def _handle_empty_activity(self) -> None:
        """Handle cases where all players have left the current activity."""

        from bascenev1._gameactivity import GameActivity

        activity = self.getactivity()
        if activity is None:
            return  # Hmm what should we do in this case?

        # If there are still players in the current activity, we're good.
        if activity.players:
            return

        # If there are *not* players in the current activity but there
        # *are* in the session:
        if not activity.players and self.sessionplayers:
            # If we're in a game, we should restart to pull in players
            # currently waiting in the session.
            if isinstance(activity, GameActivity):
                # Never restart tourney games however; just end the session
                # if all players are gone.
                if self.tournament_id is not None:
                    self.end()
                else:
                    self.restart()

        # Hmm; no players anywhere. Let's end the entire session if we're
        # running a GUI (or just the current game if we're running headless).
        else:
            if babase.app.env.gui:
                self.schedule_end_game()
            else:
                if isinstance(activity, GameActivity):
                    with activity.context:
                        activity.end_game()

    def _on_tournament_restart_menu_press(
        self, resume_callback: Callable[[], Any]
    ) -> None:
        # pylint: disable=cyclic-import
        from bascenev1._gameactivity import GameActivity

        assert babase.app.classic is not None
        activity = self.getactivity()
        if activity is not None and not activity.expired:
            assert self.tournament_id is not None
            assert isinstance(activity, GameActivity)
            babase.app.classic.tournament_entry_window(
                tournament_id=self.tournament_id,
                tournament_activity=activity,
                on_close_call=resume_callback,
            )

    def restart(self) -> None:
        """Restart the current game activity."""

        # Tell the current activity to end with a 'restart' outcome.
        # We use 'force' so that we apply even if end has already been called
        # (but is in its delay period).

        # Make an exception if there's no players left. Otherwise this
        # can override the default session end that occurs in that case.
        if not self.sessionplayers:
            return

        # This method may get called from the UI context so make sure we
        # explicitly run in the activity's context.
        activity = self.getactivity()
        if activity is not None and not activity.expired:
            activity.can_show_ad_on_death = True
            if self._arcade_mode:
                if self._arcade_lives > 0:
                    self._arcade_lives -= 1
                else:
                    with self.getactivity().context:
                        bs.broadcastmessage(
                            bs.Lstr(r='noLivesRestartArcadeMode'),
                            color=(1, 0.1, 0.1),
                        )
                        bs.getsound('error').play()
                    return
            with activity.context:
                activity.end(results={'outcome': 'restart'}, force=True)

    # noinspection PyUnresolvedReferences
    @override
    def on_activity_end(
        self, activity: bascenev1.Activity, results: Any
    ) -> None:
        """Method override for co-op sessions.

        Jumps between co-op games and score screens.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=cyclic-import
        from bascenev1lib.activity.coopscore import CoopScoreScreen
        from bascenev1lib.tutorial import TutorialActivity

        from bascenev1._gameresults import GameResults
        from bascenev1._player import PlayerInfo
        from bascenev1._activitytypes import JoinActivity, TransitionActivity
        from bascenev1._coopgame import CoopGameActivity
        from bascenev1._score import ScoreType

        app = babase.app
        env = app.env
        classic = app.classic
        assert classic is not None
        win_music_override = None
        lose_music_override = None
        if getattr(activity, 'win_music_override', None):
            win_music_override = activity.win_music_override
        if getattr(activity, 'lose_music_override', None):
            lose_music_override = activity.lose_music_override

        # If we're running a TeamGameActivity we'll have a GameResults
        # as results. Otherwise its an old CoopGameActivity so its giving
        # us a dict of random stuff.
        if isinstance(results, GameResults):
            outcome = 'defeat'  # This can't be 'beaten'.
        else:
            outcome = '' if results is None else results.get('outcome', '')

        # If we're running with a gui and at any point we have no
        # in-game players, quit out of the session (this can happen if
        # someone leaves in the tutorial for instance).
        if env.gui:
            active_players = [p for p in self.sessionplayers if p.in_game]
            if not active_players:
                self.end()
                return

        # If we're in a between-round activity or a restart-activity,
        # hop into a round.
        if isinstance(
            activity, (JoinActivity, CoopScoreScreen, TransitionActivity)
        ):
            if outcome == 'next_level':
                if self._next_game_instance is None:
                    raise RuntimeError()
                assert self._next_game_level_name is not None
                self.campaign_level_name = self._next_game_level_name
                next_game = self._next_game_instance
            else:
                next_game = self._current_game_instance

            variant = babase.app.env.variant
            vart = type(variant)
            arcade_or_demo = variant is vart.ARCADE or variant is vart.DEMO

            # Special case: if we're coming from a joining-activity
            # and will be going into onslaught-training, show the
            # tutorial first.
            if (
                isinstance(activity, JoinActivity)
                and self.campaign_level_name == 'Onslaught Training'
                and not arcade_or_demo
            ):
                if self._tutorial_activity is None:
                    raise RuntimeError('Tutorial not preloaded properly.')
                self.setactivity(self._tutorial_activity)
                self._tutorial_activity = None
                self._ran_tutorial_activity = True
                self._custom_menu_ui = []

            # Normal case; launch the next round.
            else:
                # Reset stats for the new activity.
                self.stats.reset()
                for player in self.sessionplayers:
                    # Skip players that are still choosing a team.
                    if player.in_game:
                        self.stats.register_sessionplayer(player)
                self.stats.setactivity(next_game)

                # Now flip the current activity..
                self.setactivity(next_game)

                if not arcade_or_demo:
                    if (
                        self.tournament_id is not None
                        and classic.coop_session_args['submit_score']
                    ):
                        self._custom_menu_ui = [
                            {
                                'label': babase.Lstr(resource='restartText'),
                                'resume_on_call': False,
                                'call': babase.WeakCall(
                                    self._on_tournament_restart_menu_press
                                ),
                            }
                        ]
                    else:
                        self._custom_menu_ui = [
                            {
                                'label': babase.Lstr(resource='restartText'),
                                'call': babase.WeakCall(self.restart),
                            }
                        ]

        # If we were in a tutorial, just pop a transition to get to the
        # actual round.
        elif isinstance(activity, TutorialActivity):
            self.setactivity(_bascenev1.newactivity(TransitionActivity))
        else:
            playerinfos: list[bascenev1.PlayerInfo]

            # Generic team games.
            if isinstance(results, GameResults):
                playerinfos = results.playerinfos
                score = results.get_sessionteam_score(results.sessionteams[0])
                fail_message = None
                score_order = (
                    'decreasing' if results.lower_is_better else 'increasing'
                )
                if results.scoretype in (
                    ScoreType.SECONDS,
                    ScoreType.MILLISECONDS,
                ):
                    scoretype = 'time'

                    # ScoreScreen wants hundredths of a second.
                    if score is not None:
                        if results.scoretype is ScoreType.SECONDS:
                            score *= 100
                        elif results.scoretype is ScoreType.MILLISECONDS:
                            score //= 10
                        else:
                            raise RuntimeError('FIXME')
                else:
                    if results.scoretype is not ScoreType.POINTS:
                        print(f'Unknown ScoreType:' f' "{results.scoretype}"')
                    scoretype = 'points'

            # Old coop-game-specific results; should migrate away from these.
            else:
                playerinfos = results.get('playerinfos')
                score = results['score'] if 'score' in results else None
                fail_message = (
                    results['fail_message']
                    if 'fail_message' in results
                    else None
                )
                score_order = (
                    results['score_order']
                    if 'score_order' in results
                    else 'increasing'
                )
                activity_score_type = (
                    activity.get_score_type()
                    if isinstance(activity, CoopGameActivity)
                    else None
                )
                assert activity_score_type is not None
                scoretype = activity_score_type

            # Validate types.
            if playerinfos is not None:
                assert isinstance(playerinfos, list)
                assert all(isinstance(i, PlayerInfo) for i in playerinfos)

            # Looks like we were in a round - check the outcome and
            # go from there.
            if outcome == 'restart':
                # This will pop up back in the same round.
                # THIS IS WHAT RESTARTS THE LEVEL
                self.setactivity(_bascenev1.newactivity(TransitionActivity))
            else:
                arcade = self._arcade_mode
                if arcade:
                    if outcome == 'victory':
                        def nextgame():
                            next_game = self._next_game_instance
                            self.setactivity(next_game)
                        Background(fade_time=0.6).autoretain()
                        bs.timer(0.9, nextgame)
                    else:
                        if self._arcade_lives > 0:
                            self.setactivity(_bascenev1.newactivity(TransitionActivity))
                            self._arcade_lives -= 1
                        else:
                            self._show_gameover_text()
                            bs.setmusic(bs.MusicType.COOP_GAMEOVER)
                            bs.timer(10, self._do_arcade_results)
                else:
                    self.setactivity(
                        _bascenev1.newactivity(
                            CoopScoreScreen,
                            {
                                'playerinfos': playerinfos,
                                'score': score,
                                'fail_message': fail_message,
                                'score_order': score_order,
                                'score_type': scoretype,
                                'outcome': outcome,
                                'campaign': self.campaign,
                                'level': self.campaign_level_name,
                                'win_music_override': win_music_override,
                                'lose_music_override': lose_music_override,
                            },
                        )
                    )
        # Only IF we're on arcade,
        # update the lives text (doesn't matter the condition)
        if self._arcade_mode:
            bs.timer(0.01, self._update_for_arcade)
        # No matter what, get the next 2 levels ready to go.
        self._update_on_deck_game_instances()
