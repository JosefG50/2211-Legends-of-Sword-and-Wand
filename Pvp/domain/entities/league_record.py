from dataclasses import dataclass


@dataclass
class LeagueRecord:
    """
    Stores a player's PvP league statistics.
    """

    username: str
    wins: int = 0
    losses: int = 0

    def record_win(self) -> None:
        self.wins += 1

    def record_loss(self) -> None:
        self.losses += 1

    def record_match(self, winner_username: str) -> None:
        """
        Update record after a match.
        """
        if winner_username == self.username:
            self.record_win()
        else:
            self.record_loss()