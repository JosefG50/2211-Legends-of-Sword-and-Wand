from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Party:
    """
    Immutable snapshot of a player's party imported from the PvE campaign.
    Once stored in the PvP service, this party cannot change.
    """

    party_id: str
    owner_username: str
    hero_ids: Tuple[str, ...]

    def hero_count(self) -> int:
        return len(self.hero_ids)