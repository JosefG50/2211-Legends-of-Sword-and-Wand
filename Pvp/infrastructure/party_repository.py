from typing import Dict, Optional
from domain.entities.party import Party

class PartyRepository:
    """
    In-memory repository for Parties.
    """

    def __init__(self):
        self._parties: Dict[str, Party] = {}

    def save(self, party: Party) -> None:
        self._parties[party.party_id] = party

    def get(self, party_id: str) -> Optional[Party]:
        return self._parties.get(party_id)

    def all(self):
        return list(self._parties.values())