from sqlalchemy.orm import Session
from domain.entities.league_record import LeagueRecord
from infrastructure.models.league_record_model import LeagueRecordModel


class LeagueRepository:

    def __init__(self, db: Session):
        self.db = db

    def save(self, record: LeagueRecord) -> None:

        existing = self.db.get(LeagueRecordModel, record.username)

        if existing:
            existing.wins = record.wins
            existing.losses = record.losses
        else:
            model = LeagueRecordModel(
                username=record.username,
                wins=record.wins,
                losses=record.losses
            )
            self.db.add(model)

        self.db.commit()

    def get(self, username: str):

        model = self.db.get(LeagueRecordModel, username)

        if not model:
            return None

        return LeagueRecord(
            username=model.username,
            wins=model.wins,
            losses=model.losses
        )

    def all(self):

        models = self.db.query(LeagueRecordModel).all()

        return [
            LeagueRecord(
                username=m.username,
                wins=m.wins,
                losses=m.losses
            )
            for m in models
        ]