from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import create_tables
from app.routers import auth, campaign, map, inn, battle, score

app = FastAPI(
    title="Legends of Sword and Wand — PvE Service",
    description=(
        "Handles the PvE campaign: map progression, inn interactions, "
        "enemy party generation, battle outcome processing, and scoring."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    import os
    if os.environ.get("TESTING") != "1":
        create_tables()


app.include_router(campaign.router)
app.include_router(auth.router)
app.include_router(map.router)
app.include_router(inn.router)
app.include_router(battle.router)
app.include_router(score.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "pve-service"}
