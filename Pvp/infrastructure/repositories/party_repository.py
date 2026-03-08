from sqlalchemy.orm import Session
from domain.entities.party import Party
from infrastructure.models.party_model import PartyModel


class PartyRepository:

    def __init__(self, db: Session):
        self.db = db

    def save(self, party: Party) -> None:

        model = PartyModel(
            party_id=party.party_id,
            owner_username=party.owner_username,
            hero_ids=list(party.hero_ids)
        )

        existing = self.db.get(PartyModel, party.party_id)

        if existing:
            existing.owner_username = party.owner_username
            existing.hero_ids = list(party.hero_ids)
        else:
            self.db.add(model)

        self.db.commit()

    def get(self, party_id: str):

        model = self.db.get(PartyModel, party_id)

        if not model:
            return None

        return Party(
            party_id=model.party_id,
            owner_username=model.owner_username,
            hero_ids=tuple(model.hero_ids)
        )

    def all(self):
        models = self.db.query(PartyModel).all()

        return [
            Party(
                party_id=m.party_id,
                owner_username=m.owner_username,
                hero_ids=tuple(m.hero_ids)
            )
            for m in models
        ]