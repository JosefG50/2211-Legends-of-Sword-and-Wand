from infrastructure.database import SessionLocal
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.party_repository import PartyRepository
from infrastructure.repositories.league_repository import LeagueRepository

from application.invite_player import InvitePlayerService
from application.accept_invite import AcceptInviteService
from application.decline_invite import DeclineInviteService
from application.select_party import SelectPartyService
from application.start_battle import StartBattleService
from application.update_league import UpdateLeagueService

from application.interfaces.client_api import ClientAPI
from application.interfaces.battle_system import BattleSystemAPI
from application.interfaces.pve_submission import PVEPartySubmissionAPI


def main():
    # Create database session
    db = SessionLocal()

    # Initialize repositories
    user_repo = UserRepository(db)
    party_repo = PartyRepository(db)
    league_repo = LeagueRepository(db)

    # Initialize application services
    invite_service = InvitePlayerService()
    accept_service = AcceptInviteService()
    decline_service = DeclineInviteService()
    select_party_service = SelectPartyService()
    start_battle_service = StartBattleService()
    update_league_service = UpdateLeagueService()

    # Initialize interfaces
    client_api = ClientAPI(
        invite_service,
        accept_service,
        decline_service,
        select_party_service,
        start_battle_service
    )
    battle_api = BattleSystemAPI()
    pve_api = PVEPartySubmissionAPI(party_repo)

    print("PvP service running")
    print("===================")


if __name__ == "__main__":
    main()