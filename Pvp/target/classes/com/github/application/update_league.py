from domain.entities.league_record import LeagueRecord
from domain.entities.battle_match import BattleMatch

class UpdateLeagueService:

    def update(self, match: BattleMatch, league_records: dict):
        """
        league_records: dict[str, LeagueRecord]
        Updates league standings after a match.
        """

        if not match.is_finished():
            raise ValueError("Cannot update league: match not finished")

        winner = match.winner_username
        loser = match.loser_username

        if winner not in league_records or loser not in league_records:
            raise ValueError("Both players must have LeagueRecords")

        league_records[winner].record_win()
        league_records[loser].record_loss()