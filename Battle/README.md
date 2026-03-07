# PvP Service – Legends of Sword and Wand

This service handles all Player vs Player functionality including sending battle invitations, running battles, and tracking league standings.

---

## How to Run

### Locally
```bash
pip install flask
python app.py
```
The service will be available at `http://localhost:5003`

### With Docker
```bash
docker build -t pvp-service .
docker run -p 5003:5003 pvp-service
```

### Tests
```bash
python tests.py
```

---

## API Documentation

### Base URL
```
http://localhost:5003
```

---

### 1. Send an Invitation

Sends a PvP battle invitation from one player to another.

- **URL:** `/pvp/invite`
- **Method:** `POST`
- **Content-Type:** `application/json`

**Input:**
```json
{
    "inviter": "alice",
    "invitee": "bob"
}
```

**Output (success):**
```json
{
    "invitation_id": 1,
    "status": "pending"
}
```

**Output (error):**
```json
{
    "error": "A pending invitation already exists"
}
```

| Status Code | Meaning |
|---|---|
| 201 | Invitation created successfully |
| 400 | Missing fields or player invited themselves |
| 409 | A pending invitation already exists between these players |

---

### 2. Respond to an Invitation

Accept or decline a pending invitation.

- **URL:** `/pvp/invite/<invitation_id>/respond`
- **Method:** `POST`
- **Content-Type:** `application/json`

**Input:**
```json
{
    "action": "accept"
}
```
or
```json
{
    "action": "decline"
}
```

**Output (success):**
```json
{
    "invitation_id": 1,
    "status": "accepted"
}
```

| Status Code | Meaning |
|---|---|
| 200 | Response recorded |
| 400 | Invalid action, or invitation is not pending |
| 404 | Invitation not found |

---

### 3. Get an Invitation

Retrieve the details and current status of an invitation.

- **URL:** `/pvp/invite/<invitation_id>`
- **Method:** `GET`

**Output (success):**
```json
{
    "invitation_id": 1,
    "inviter": "alice",
    "invitee": "bob",
    "status": "pending"
}
```

| Status Code | Meaning |
|---|---|
| 200 | Invitation found |
| 404 | Invitation not found |

---

### 4. List Invitations for a Player

Get all invitations sent or received by a specific player.

- **URL:** `/pvp/invitations?username=alice`
- **Method:** `GET`

**Output (success):**
```json
{
    "invitations": [
        {
            "invitation_id": 1,
            "inviter": "alice",
            "invitee": "bob",
            "status": "pending"
        }
    ]
}
```

| Status Code | Meaning |
|---|---|
| 200 | Returns list (may be empty) |
| 400 | Missing username query parameter |

---

### 5. Start a Battle

Run a PvP battle between two parties. The invitation must be accepted before calling this.

- **URL:** `/pvp/battle/start`
- **Method:** `POST`
- **Content-Type:** `application/json`

**Input:**
```json
{
    "invitation_id": 1,
    "inviter_party": [
        {
            "name": "Alice",
            "level": 5,
            "attack": 20,
            "defense": 10,
            "hp": 200,
            "max_hp": 200,
            "mana": 80,
            "max_mana": 80,
            "shield": 0,
            "class_name": "Warrior"
        }
    ],
    "invitee_party": [
        {
            "name": "Bob",
            "level": 5,
            "attack": 18,
            "defense": 12,
            "hp": 180,
            "max_hp": 180,
            "mana": 60,
            "max_mana": 60,
            "shield": 0,
            "class_name": "Mage"
        }
    ]
}
```

**Hero fields:**

| Field | Type | Description |
|---|---|---|
| name | string | Hero's name |
| level | int | Hero's current level |
| attack | int | Attack stat |
| defense | int | Defense stat |
| hp | int | Current health points |
| max_hp | int | Maximum health points |
| mana | int | Current mana |
| max_mana | int | Maximum mana |
| shield | int | Current shield value (optional, default 0) |
| class_name | string | One of: `Warrior`, `Mage`, `Order`, `Chaos`, `Priest`, `Knight`, `Warlock`, `Wizard` |

**Output (success):**
```json
{
    "result": "inviter_wins",
    "winner": "alice",
    "battle_log": [
        "=== alice vs bob ===",
        "--- Round 1 ---",
        "  Alice attacks Bob for 8 damage. (HP: 172/180)",
        "=== alice wins! ==="
    ],
    "inviter_party": [ { "name": "Alice", "hp": 150, "..." : "..." } ],
    "invitee_party": [ { "name": "Bob",   "hp": 0,   "..." : "..." } ]
}
```

The `result` field will be one of: `inviter_wins`, `invitee_wins`, or `draw`.

| Status Code | Meaning |
|---|---|
| 200 | Battle completed successfully |
| 400 | Missing required fields |
| 404 | Invitation not found |
| 409 | Invitation is not in accepted state |

---

### 6. Get League Standings

Returns all players sorted by number of wins.

- **URL:** `/pvp/league`
- **Method:** `GET`

**Output (success):**
```json
{
    "standings": [
        { "username": "alice", "wins": 5, "losses": 1, "draws": 0 },
        { "username": "bob",   "wins": 3, "losses": 3, "draws": 1 }
    ]
}
```

| Status Code | Meaning |
|---|---|
| 200 | Returns standings (may be empty) |

---

### 7. Get a Player's Stats

Returns the league record for a specific player.

- **URL:** `/pvp/league/<username>`
- **Method:** `GET`

**Output (success):**
```json
{
    "username": "alice",
    "wins": 5,
    "losses": 1,
    "draws": 0
}
```

| Status Code | Meaning |
|---|---|
| 200 | Player found |
| 404 | Player not found |

---

### 8. Health Check

Check if the service is running.

- **URL:** `/health`
- **Method:** `GET`

**Output:**
```json
{
    "status": "ok"
}
```

---

## Battle System Summary

- Parties can have 1–5 heroes each
- Turn order is determined by level (highest goes first), with teams alternating
- Each turn a hero will **attack**, **defend**, or **cast** their special ability
- **Damage** = attacker's attack − defender's defense
- **Shields** absorb damage before HP is affected
- **Defend** skips the turn but restores +10 HP and +5 mana
- The battle ends when all heroes on one side reach 0 HP
- No experience or gold is gained in PvP

**Special abilities by class:**

| Class | Ability | Mana Cost | Effect |
|---|---|---|---|
| Order | Protect | 25 | Shield all allies for 10% of their max HP |
| Order | Heal | 35 | Heal lowest HP ally for 25% of their max HP |
| Chaos | Fireball | 30 | Hit up to 3 random enemies |
| Chaos | Chain Lightning | 40 | Hit all enemies, each takes 25% of the previous damage |
| Warrior | Berserker Attack | 60 | Hit main target, splash 2 others for 25% damage |
| Mage | Replenish | 80 | Restore 30 mana to all allies, 60 to self |
