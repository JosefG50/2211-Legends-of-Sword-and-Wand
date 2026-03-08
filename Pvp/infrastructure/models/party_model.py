from sqlalchemy import Column, String, JSON
from infrastructure.database import Base


class PartyModel(Base):
    __tablename__ = "parties"

    party_id = Column(String, primary_key=True)
    owner_username = Column(String)
    hero_ids = Column(JSON)