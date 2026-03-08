from dataclasses import dataclass
from typing import Optional

from domain.entities.party import Party


@dataclass
class BattleMatch:
    """
    Represents a PvP match between two players.
    The battle itself is resolved by the external battle service.
    """

    player1_username: str
    player2_username: str

    player1_party: Party
    player2_party: Party

    winner_username: Optional[str] = None
    loser_username: Optional[str] = None

    def record_result(self, winner_username: str) -> None:
        """
        Record the result returned by the battle service.
        """

        if winner_username not in (self.player1_username, self.player2_username):
            raise ValueError("Winner must be one of the match players.")

        self.winner_username = winner_username

        if winner_username == self.player1_username:
            self.loser_username = self.player2_username
        else:
            self.loser_username = self.player1_username

    def is_finished(self) -> bool:
        """
        Returns True if the match result has been recorded.
        """
        return self.winner_username is not None