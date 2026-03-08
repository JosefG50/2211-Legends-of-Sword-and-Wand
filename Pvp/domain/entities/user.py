from dataclasses import dataclass, field
from typing import Tuple, Optional
from domain.entities.party import Party


@dataclass
class User:
    username: str
    parties: Tuple[Party, ...] = field(default_factory=tuple)

    def has_parties(self) -> bool:
        return len(self.parties) > 0

    def get_party(self, party_id: str) -> Optional[Party]:
        for party in self.parties:
            if party.party_id == party_id:
                return party
        return None