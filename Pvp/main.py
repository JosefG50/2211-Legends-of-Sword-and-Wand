from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Database & Infrastructure
from infrastructure.database import SessionLocal, init_db
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.party_repository import PartyRepository
from infrastructure.repositories.league_repository import LeagueRepository
from infrastructure.models.user_model import UserModel  # Added this
from infrastructure.models.party_model import PartyModel

# Application Services
from application.invite_player import InvitePlayerService
from application.accept_invite import AcceptInviteService
from application.decline_invite import DeclineInviteService
from application.start_battle import StartBattleService
from application.update_league import UpdateLeagueService

# Controllers & Routes
from api.controllers.player_controller import PlayerController
from api.controllers.invite_controller import InviteController
from api.controllers.battle_controller import BattleController
from api.routes import player_routes, invite_routes, battle_routes

app = FastAPI(title="PvP System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporarily allow everything to rule out port issues
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# GLOBALS
# -----------------------
# Note: Controllers and Services are initialized once
invite_service = InvitePlayerService()
accept_service = AcceptInviteService()
decline_service = DeclineInviteService()
start_battle_service = StartBattleService()
update_league_service = UpdateLeagueService()

# -----------------------
# HELPERS
# -----------------------
def ensure_pvp_ready(username, db_session):
    """Ensures a user has at least one party saved in the DB."""
    user = db_session.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        print(f"User {username} not found in DB. Skipping preload.")
        return

    # Check if they have any parties. 
    # This works because of the relationship we added to UserModel.
    if not user.parties:
        print(f"Preloading PvP party for {username}...")
        new_party = PartyModel(
            user_id=user.id,
            name="Starter PvP Squad"
            # If your PartyModel requires hero IDs or stats, add them here
        )
        db_session.add(new_party)
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            print(f"Failed to preload party: {e}")

# -----------------------
# STARTUP
# -----------------------
@app.on_event("startup")
def startup():
    print("Initializing PvP Database...")
    init_db()  # Creates league_records and ensures tables exist

    db_session = SessionLocal()

    global player_controller
    # Initialize Repositories with the session
    party_repo = PartyRepository(db_session)
    user_repo = UserRepository(db_session)
    league_repo = LeagueRepository(db_session)

    # Initialize Controllers
    player_controller = PlayerController(user_repo, party_repo)
    invite_cont = InviteController(invite_service, accept_service, decline_service)
    battle_cont = BattleController(start_battle_service, update_league_service)

    # Initialize Routes
    player_routes.init(player_controller)
    invite_routes.init(invite_cont)
    battle_routes.init(battle_cont)

    app.include_router(player_routes.router)
    app.include_router(invite_routes.router)
    app.include_router(battle_routes.router)

    # PRELOAD TEST ACCOUNT
    # This checks the shared Postgres 'users' table for 'tester'
    ensure_pvp_ready("tester", db_session) 
    
    db_session.close()
    print("PvP Startup Complete.")