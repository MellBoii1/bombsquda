import bascenev1 as bs
from bascenev1lib.game.creditsroll import CreditsActivity

from typing import TYPE_CHECKING, override

class CreditsSession(bs.Session):
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.setactivity(bs.newactivity(CreditsActivity))
    @override
    def on_player_request(self, player: bs.SessionPlayer) -> bool:
        # Reject all player requests.
        return False