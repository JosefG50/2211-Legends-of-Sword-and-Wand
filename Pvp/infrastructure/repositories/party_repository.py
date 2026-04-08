# Pvp/infrastructure/repositories/party_repository.py

from infrastructure.models.party_model import PartyModel

class PartyRepository:
    def __init__(self, db):
        self.db = db

    def get_by_user(self, username: str):
        # This matches the 'owner_username' column in your DB
        return self.db.query(PartyModel).filter(PartyModel.owner_username == username).all()

    def save(self, party_model: PartyModel):
        self.db.add(party_model)
        self.db.commit()
        self.db.refresh(party_model)