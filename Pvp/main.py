from infrastructure.database import SessionLocal
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.party_repository import PartyRepository
from infrastructure.repositories.league_repository import LeagueRepository

from application.services.match_service import MatchService


def main():

    db = SessionLocal()

    user_repo = UserRepository(db)
    party_repo = PartyRepository(db)
    league_repo = LeagueRepository(db)

    match_service = MatchService(
        user_repo,
        party_repo,
        league_repo
    )

    # start CLI / API / simulation
    print("PvP service running")


if __name__ == "__main__":
    main()