from fastapi import FastAPI

from infrastructure.database import SessionLocal, init_db
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.party_repository import PartyRepository
from infrastructure.repositories.league_repository import LeagueRepository

from application.invite_player import InvitePlayerService
from application.accept_invite import AcceptInviteService
from application.decline_invite import DeclineInviteService
from application.start_battle import StartBattleService
from application.update_league import UpdateLeagueService

from api.controllers.player_controller import PlayerController
from api.controllers.invite_controller import InviteController
from api.controllers.battle_controller import BattleController

from api.routes import player_routes, invite_routes, battle_routes

from domain.entities import user

app = FastAPI(title="PvP System API")


# -----------------------
# GLOBALS (set on startup)
# -----------------------
db = None
user_repo = None
party_repo = None
league_repo = None


invite_service = InvitePlayerService()
accept_service = AcceptInviteService()
decline_service = DeclineInviteService()
start_battle_service = StartBattleService()
update_league_service = UpdateLeagueService()


player_controller = None
invite_controller = None
battle_controller = None


# -----------------------
# STARTUP
# -----------------------
@app.on_event("startup")
def startup():
    global db, user_repo, party_repo, league_repo
    global player_controller, invite_controller, battle_controller

    print("Initializing database...")
    init_db()

    db = SessionLocal()

    user_repo = UserRepository(db)
    party_repo = PartyRepository(db)
    league_repo = LeagueRepository(db)

    player_controller = PlayerController(user_repo, party_repo)

    invite_controller = InviteController(
        invite_service,
        accept_service,
        decline_service
    )

    battle_controller = BattleController(
        start_battle_service,
        update_league_service
    )

    player_routes.init(player_controller)
    invite_routes.init(invite_controller)
    battle_routes.init(battle_controller)

    app.include_router(player_routes.router)
    app.include_router(invite_routes.router)
    app.include_router(battle_routes.router)

    print("Seeding database...")
    seed_data(user_repo)


# -----------------------
# SEED DATA
# -----------------------
def seed_data(user_repo):
    if not user_repo.exists("alice"):
        user_repo.save(user(username="alice"))

    if not user_repo.exists("bob"):
        user_repo.save(user(username="bob"))

    print("Seed complete ✔")