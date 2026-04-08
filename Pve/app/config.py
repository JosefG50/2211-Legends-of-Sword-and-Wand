from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://pve_user:pve_pass@db:5432/pve_db"
    BATTLE_SERVICE_URL: str = "http://battle-service:8001"
    PARTY_SERVICE_URL: str = "http://party-service:8002"
    SECRET_KEY: str = "change-me-in-production"

    # Campaign constants
    TOTAL_ROOMS: int = 30
    BASE_BATTLE_CHANCE: float = 0.60
    CHANCE_SHIFT_PER_10_LEVELS: float = 0.03
    MAX_BATTLE_CHANCE: float = 0.90
    MAX_PARTY_SIZE: int = 5
    MAX_SAVED_PARTIES: int = 5
    INN_HERO_RECRUITMENT_ROOMS: int = 10

    # Scoring
    SCORE_PER_HERO_LEVEL: int = 100
    SCORE_PER_GOLD: int = 10
    SCORE_ITEM_MULTIPLIER: int = 10

    # Experience & Gold
    EXP_PER_LEVEL: int = 50         # Exp(L) = 50 * L per enemy unit
    GOLD_PER_LEVEL: int = 75        # G(L) = 75 * L per enemy unit
    LOSS_GOLD_PENALTY: float = 0.10
    LOSS_EXP_PENALTY: float = 0.30

    class Config:
        env_file = ".env"


settings = Settings()
