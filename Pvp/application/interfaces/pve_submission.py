# application/interfaces/pve_submission.py

from domain.entities.party import Party

class PVEPartySubmissionAPI:
    """
    Accepts party snapshots from PvE campaigns.
    """

    def __init__(self, party_repo):
        self.party_repo = party_repo

    def submit_party(self, party_id, owner_username, hero_ids):
        party = Party(
            party_id=party_id,
            owner_username=owner_username,
            hero_ids=tuple(hero_ids)
        )
        self.party_repo.save(party)
        return party