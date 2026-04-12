from typing import Dict, Optional
from domain.entities.league_record import LeagueRecord

class LeagueRepository:
    """
    In-memory repository for LeagueRecords.
    """

    def __init__(self):
        self._records: Dict[str, LeagueRecord] = {}

    def save(self, record: LeagueRecord) -> None:
        self._records[record.username] = record

    def get(self, username: str) -> Optional[LeagueRecord]:
        return self._records.get(username)

    def all(self):
        return list(self._records.values())