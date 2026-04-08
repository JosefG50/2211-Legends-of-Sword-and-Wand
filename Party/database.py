from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import hashlib
from datetime import datetime, timezone

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client['legends_game']
heroes_collection = db['heroes']
users_collection  = db['users']

# Create unique index on username so duplicates are rejected at DB level
users_collection.create_index("username", unique=True)


# ── User model ────────────────────────────────────────────────────────────────
# Equivalent of:
#   class User(Base):
#       __tablename__ = "users"
#       id           = Column(Integer, primary_key=True, index=True)
#       username     = Column(String(100), unique=True, nullable=False, index=True)
#       password_hash = Column(String(128), nullable=False)
#       created_at   = Column(DateTime(timezone=True), server_default=func.now())
#       updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
#
# MongoDB stores this in the 'users' collection with the same fields.
# The MongoDB _id acts as the primary key (equivalent to Integer id).

def _hash_password(password: str) -> str:
    """SHA-256 hash of a password string."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(username: str, password: str):
    """
    Create a new user. Returns the user dict on success.
    Returns None if the username is already taken.
    """
    try:
        now = datetime.now(timezone.utc)
        result = users_collection.insert_one({
            "username":      username,
            "password_hash": _hash_password(password),
            "created_at":    now,
            "updated_at":    now,
        })
        return get_user_by_id(str(result.inserted_id))
    except Exception:
        return None  # duplicate username


def get_user_by_id(user_id: str):
    """Fetch a user by their MongoDB _id string."""
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user["id"] = str(user["_id"])
            user["_id"] = str(user["_id"])
        return user
    except Exception:
        return None


def get_user_by_username(username: str):
    """Fetch a user by username."""
    user = users_collection.find_one({"username": username})
    if user:
        user["id"] = str(user["_id"])
        user["_id"] = str(user["_id"])
    return user


def verify_user(username: str, password: str):
    """
    Check credentials. Returns the user dict if valid, None otherwise.
    """
    user = get_user_by_username(username)
    if not user:
        return None
    if user["password_hash"] != _hash_password(password):
        return None
    return user


def update_user(user_id: str, update_fields: dict):
    """Update user fields (e.g. password_hash). Sets updated_at automatically."""
    update_fields["updated_at"] = datetime.now(timezone.utc)
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )
    return get_user_by_id(user_id)


# ── Hero records ──────────────────────────────────────────────────────────────

def create_hero_record(username, hero_name, initial_class):
    """Creates a new level 1 hero in the database."""
    hero_data = {
        "username": username,
        "hero_name": hero_name,
        "total_level": 1,
        "xp": 0,
        "class_levels": {
            "Order":   1 if initial_class == "Order"   else 0,
            "Chaos":   1 if initial_class == "Chaos"   else 0,
            "Warrior": 1 if initial_class == "Warrior" else 0,
            "Mage":    1 if initial_class == "Mage"    else 0,
        },
        "hybrid_class": None,
        "is_hybrid": False,
    }
    result = heroes_collection.insert_one(hero_data)
    return str(result.inserted_id)


def get_hero_record(hero_id):
    """Fetches a hero by their MongoDB ObjectId."""
    try:
        hero = heroes_collection.find_one({"_id": ObjectId(hero_id)})
        if hero:
            hero['_id'] = str(hero['_id'])
        return hero
    except Exception:
        return None


def update_hero_record(hero_id, update_fields):
    """Updates specific fields for a hero."""
    heroes_collection.update_one(
        {"_id": ObjectId(hero_id)},
        {"$set": update_fields}
    )
    return get_hero_record(hero_id)
