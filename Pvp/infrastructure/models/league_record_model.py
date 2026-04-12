from sqlalchemy import Column, String, Integer
from infrastructure.database import Base


class LeagueRecordModel(Base):
    __tablename__ = "league_records"

    username = Column(String, primary_key=True)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)