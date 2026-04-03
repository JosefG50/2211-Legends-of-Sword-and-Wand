"""
Battle Service - Legends of Sword and Wand
-------------------------------------------
This service handles all battle logic for both PvP and PvE game modes.

Other microservices can use this service in two ways:

  1. TURN-BASED (PvP and PvE with player input):
       POST /battle/start   -> start a battle, get back the game state
       POST /battle/action  -> submit a player action each turn
       GET  /battle/state/<id> -> get current state at any time

  2. AUTO-BATTLE (PvE without player input):
       POST /battle/run     -> run a full battle in one call, get back the result

  Plus PvP invitation management and league standings:
       POST /pvp/invite
       POST /pvp/invite/<id>/respond
       GET  /pvp/invite/<id>
       GET  /pvp/invitations
       GET  /pvp/league
       GET  /pvp/league/<username>
"""

from flask import Flask, request, jsonify
import sqlite3
import json
import os
from battle import run_battle, ABILITY_MANA_COST, DEFAULT_ABILITY

app = Flask(__name__)
DB = "pvp.db"


# -------------------------------------------------------
# Database setup
# -------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invitations (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter  TEXT NOT NULL,
            invitee  TEXT NOT NULL,
            status   TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS league (
            username TEXT PRIMARY KEY,
            wins     INTEGER NOT NULL DEFAULT 0,
            losses   INTEGER NOT NULL DEFAULT 0,
            draws    INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS battle_logs (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name_a  TEXT NOT NULL,
            name_b  TEXT NOT NULL,
            winner  TEXT NOT NULL,
            mode    TEXT NOT NULL DEFAULT 'pvp',
            log     TEXT NOT NULL
        )
    """)
    # Stores the state of ongoing turn-based battles
    conn.execute("""
        CREATE TABLE IF NOT EXISTS active_battles (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            state TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


# -------------------------------------------------------
# League helper
# -------------------------------------------------------

def update_league(conn, username, outcome):
    """Add a win, loss, or draw to a player's league record."""
    conn.execute(
        "INSERT OR IGNORE INTO league (username, wins, losses, draws) VALUES (?, 0, 0, 0)",
        (username,)
    )
    if outcome == "win":
        conn.execute("UPDATE league SET wins = wins + 1 WHERE username = ?", (username,))
    elif outcome == "loss":
        conn.execute("UPDATE league SET losses = losses + 1 WHERE username = ?", (username,))
    else:
        conn.execute("UPDATE league SET draws = draws + 1 WHERE username = ?", (username,))


# -------------------------------------------------------
# Turn-based battle helpers
# -------------------------------------------------------

def get_active_hero(team_a, team_b, turn_index):
    """
    Returns the hero whose turn it is and which team they are on.
    Turn order: teams alternate, highest level unit on each team goes first.
    """
    alive_a = [h for h in team_a if h["hp"] > 0]
    alive_b = [h for h in team_b if h["hp"] > 0]

    # Build interleaved turn order for this round
    order = []
    for i in range(max(len(alive_a), len(alive_b))):
        if i < len(alive_a):
            order.append(("a", alive_a[i]))
        if i < len(alive_b):
            order.append(("b", alive_b[i]))

    if not order:
        return None, None

    team, hero = order[turn_index % len(order)]
    return hero, team


def get_available_actions(hero):
    """
    Returns the list of actions the hero can take this turn.
    If they have enough mana, their special ability is included.
    """
    actions = ["attack", "defend", "wait"]
    ability = DEFAULT_ABILITY.get(hero["class_name"], "berserker_attack")
    cost = ABILITY_MANA_COST.get(ability, 999)
    if hero["mana"] >= cost:
        actions.append(f"cast:{ability}")
    return actions


def build_state(battle_id, team_a, team_b, name_a, name_b, log, turn_index, mode="pvp"):
    """
    Build the full game state dictionary returned after every action.
    This is what the frontend or other services read to know what happened.
    """
    a_alive = any(h["hp"] > 0 for h in team_a)
    b_alive = any(h["hp"] > 0 for h in team_b)
    battle_over = not a_alive or not b_alive

    winner = None
    if battle_over:
        if a_alive and not b_alive:
            winner = name_a
        elif b_alive and not a_alive:
            winner = name_b
        else:
            winner = "draw"

    state = {
        "battle_id": battle_id,
        "mode": mode,           # "pvp" or "pve" — set by whoever starts the battle
        "battle_over": battle_over,
        "winner": winner,
        "name_a": name_a,
        "name_b": name_b,
        "team_a": team_a,
        "team_b": team_b,
        "log": log,
        "turn_index": turn_index,
    }

    if not battle_over:
        active_hero, active_team = get_active_hero(team_a, team_b, turn_index)
        if active_hero:
            # Tell the frontend/client exactly who is acting and what they can do
            enemies = [h for h in (team_b if active_team == "a" else team_a) if h["hp"] > 0]
            state["current_turn"] = {
                "team": active_team,         # "a" or "b"
                "hero_name": active_hero["name"],
                "hero_index": active_hero.get("index", 0),
                "available_actions": get_available_actions(active_hero),
                # List of valid targets the player can choose from
                "valid_targets": [
                    {"name": e["name"], "index": e.get("index", 0), "hp": e["hp"], "max_hp": e["max_hp"]}
                    for e in enemies
                ],
            }
        else:
            state["current_turn"] = None
    else:
        state["current_turn"] = None

    return state


def apply_attack(attacker, target, log):
    """Apply a basic attack from attacker to target."""
    dmg = max(0, attacker["attack"] - target["defense"])
    if target.get("shield", 0) > 0:
        absorbed = min(target["shield"], dmg)
        target["shield"] -= absorbed
        dmg -= absorbed
    actual = min(dmg, target["hp"])
    target["hp"] -= actual
    log.append(f"  {attacker['name']} attacks {target['name']} for {actual} damage. "
               f"(HP: {target['hp']}/{target['max_hp']})")
    if target["hp"] <= 0:
        log.append(f"  {target['name']} is defeated!")


def apply_cast(hero, ability, allies, enemies, target_index, log):
    """Apply a special ability cast."""
    import random
    cost = ABILITY_MANA_COST.get(ability, 999)
    if hero["mana"] < cost:
        log.append(f"  {hero['name']} doesn't have enough mana! Skipping.")
        return
    hero["mana"] -= cost
    log.append(f"  {hero['name']} casts {ability}!")

    if ability == "protect":
        for ally in allies:
            ally["shield"] = max(1, int(ally["max_hp"] * 0.10))
            log.append(f"    {ally['name']} gets a shield of {ally['shield']}.")

    elif ability == "heal":
        target = min(allies, key=lambda h: h["hp"])
        amount = max(1, int(target["max_hp"] * 0.25))
        target["hp"] = min(target["max_hp"], target["hp"] + amount)
        log.append(f"    {target['name']} healed for {amount} HP. ({target['hp']}/{target['max_hp']})")

    elif ability == "fireball":
        targets = random.sample(enemies, min(3, len(enemies)))
        for t in targets:
            dmg = max(0, hero["attack"] - t["defense"])
            t["hp"] = max(0, t["hp"] - dmg)
            log.append(f"    Fireball hits {t['name']} for {dmg}. (HP: {t['hp']}/{t['max_hp']})")
            if t["hp"] <= 0:
                log.append(f"    {t['name']} is defeated!")

    elif ability == "chain_lightning":
        first = next((e for e in enemies if e.get("index", 0) == target_index), enemies[0])
        rest = [e for e in enemies if e is not first]
        random.shuffle(rest)
        dmg = max(0, hero["attack"] - first["defense"])
        for i, t in enumerate([first] + rest):
            if i > 0:
                dmg = max(0, int(dmg * 0.25))
            if dmg == 0:
                break
            t["hp"] = max(0, t["hp"] - dmg)
            log.append(f"    Chain Lightning hits {t['name']} for {dmg}. (HP: {t['hp']}/{t['max_hp']})")
            if t["hp"] <= 0:
                log.append(f"    {t['name']} is defeated!")

    elif ability == "berserker_attack":
        main = next((e for e in enemies if e.get("index", 0) == target_index), enemies[0])
        dmg = max(0, hero["attack"] - main["defense"])
        main["hp"] = max(0, main["hp"] - dmg)
        log.append(f"    Berserker Attack hits {main['name']} for {dmg}. (HP: {main['hp']}/{main['max_hp']})")
        if main["hp"] <= 0:
            log.append(f"    {main['name']} is defeated!")
        for t in random.sample([e for e in enemies if e is not main and e["hp"] > 0], min(2, len(enemies) - 1)):
            splash = max(0, int(dmg * 0.25))
            t["hp"] = max(0, t["hp"] - splash)
            log.append(f"    Splash hits {t['name']} for {splash}.")

    elif ability == "replenish":
        for ally in allies:
            amount = 60 if ally["name"] == hero["name"] else 30
            ally["mana"] = min(ally["max_mana"], ally["mana"] + amount)
            log.append(f"    {ally['name']} restores mana. ({ally['mana']}/{ally['max_mana']})")


# -------------------------------------------------------
# TURN-BASED BATTLE ENDPOINTS
# Used by: PvP frontend, PvE frontend
# -------------------------------------------------------

@app.route("/battle/start", methods=["POST"])
def start_turn_battle():
    """
    Start a new turn-based battle.

    This endpoint is used by BOTH PvP and PvE modes.
    Set the "mode" field to "pvp" or "pve" so the response
    can be handled correctly by whichever service calls it.

    Input (JSON):
        team_a      (list)  : List of hero objects for team A.
        team_b      (list)  : List of hero objects for team B.
        name_a      (str)   : Name/username for team A.
        name_b      (str)   : Name/username for team B.
        mode        (str)   : "pvp" or "pve" (default: "pvp").

    Hero object fields:
        name, level, attack, defense, hp, max_hp, mana, max_mana, shield, class_name

    Output (JSON):
        battle_id       (int)  : Use this ID for all future /battle/action calls.
        mode            (str)  : "pvp" or "pve".
        battle_over     (bool) : False at start.
        team_a          (list) : Current state of team A.
        team_b          (list) : Current state of team B.
        current_turn    (dict) : Who is acting, available actions, and valid targets.
        log             (list) : Battle log so far.
    """
    data = request.get_json()
    team_a = data.get("team_a")
    team_b = data.get("team_b")
    name_a = data.get("name_a", "Player A")
    name_b = data.get("name_b", "Player B")
    mode = data.get("mode", "pvp")

    if not team_a or not team_b:
        return jsonify({"error": "team_a and team_b are required"}), 400
    if mode not in ("pvp", "pve"):
        return jsonify({"error": "mode must be 'pvp' or 'pve'"}), 400

    # Add index so heroes can be targeted by index
    for i, h in enumerate(team_a):
        h["index"] = i
    for i, h in enumerate(team_b):
        h["index"] = i

    # Sort by level descending — highest level acts first
    team_a = sorted(team_a, key=lambda h: h["level"], reverse=True)
    team_b = sorted(team_b, key=lambda h: h["level"], reverse=True)

    log = [f"=== {name_a} vs {name_b} ({mode.upper()}) ==="]
    state = build_state(None, team_a, team_b, name_a, name_b, log, 0, mode)

    conn = get_db()
    cursor = conn.execute("INSERT INTO active_battles (state) VALUES (?)", (json.dumps(state),))
    battle_id = cursor.lastrowid
    state["battle_id"] = battle_id
    conn.execute("UPDATE active_battles SET state=? WHERE id=?", (json.dumps(state), battle_id))
    conn.commit()
    conn.close()

    return jsonify(state), 200


@app.route("/battle/action", methods=["POST"])
def submit_action():
    """
    Submit the current player's chosen action for their turn.

    This endpoint is used by BOTH PvP and PvE modes.
    Call this after /battle/start, then keep calling it each turn
    until battle_over is true in the response.

    Input (JSON):
        battle_id    (int) : The ID returned from /battle/start.
        action       (str) : One of:
                               "attack"           - basic attack
                               "defend"           - skip turn, restore +10 HP +5 mana
                               "wait"             - skip turn, act at end of round
                               "cast:<ability>"   - use special ability
                                 e.g. "cast:fireball", "cast:heal", "cast:berserker_attack"
        target_index (int) : Index of the enemy to target (required for attack and cast).
                             Use the index values from current_turn.valid_targets.

    Output (JSON):
        Same format as /battle/start.
        Check battle_over — if true, the winner field contains the result.
    """
    data = request.get_json()
    battle_id = data.get("battle_id")
    action = data.get("action", "").strip().lower()
    target_index = data.get("target_index", 0)

    if not battle_id or not action:
        return jsonify({"error": "battle_id and action are required"}), 400

    conn = get_db()
    row = conn.execute("SELECT state FROM active_battles WHERE id=?", (battle_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Battle not found"}), 404

    state = json.loads(row["state"])
    if state["battle_over"]:
        conn.close()
        return jsonify({"error": "Battle is already over", "state": state}), 400

    team_a = state["team_a"]
    team_b = state["team_b"]
    log = state["log"]
    turn_index = state["turn_index"]
    mode = state.get("mode", "pvp")

    active_hero, active_team = get_active_hero(team_a, team_b, turn_index)
    if not active_hero:
        conn.close()
        return jsonify({"error": "No active hero found"}), 400

    enemies = [h for h in (team_b if active_team == "a" else team_a) if h["hp"] > 0]
    allies  = [h for h in (team_a if active_team == "a" else team_b) if h["hp"] > 0]

    if not enemies:
        state["battle_over"] = True
        conn.execute("UPDATE active_battles SET state=? WHERE id=?", (json.dumps(state), battle_id))
        conn.commit()
        conn.close()
        return jsonify(state), 200

    # Handle stun
    if active_hero.get("stunned"):
        log.append(f"  {active_hero['name']} is stunned and loses their turn!")
        active_hero["stunned"] = False
        turn_index += 1
    elif action == "attack":
        target = next((e for e in enemies if e.get("index", 0) == target_index), enemies[0])
        apply_attack(active_hero, target, log)
        turn_index += 1
    elif action == "defend":
        active_hero["hp"] = min(active_hero["max_hp"], active_hero["hp"] + 10)
        active_hero["mana"] = min(active_hero["max_mana"], active_hero["mana"] + 5)
        log.append(f"  {active_hero['name']} defends! (+10 HP, +5 mana)")
        turn_index += 1
    elif action == "wait":
        log.append(f"  {active_hero['name']} waits.")
        turn_index += 1
    elif action.startswith("cast:"):
        ability = action.split(":", 1)[1]
        apply_cast(active_hero, ability, allies, enemies, target_index, log)
        turn_index += 1
    else:
        conn.close()
        return jsonify({"error": f"Unknown action '{action}'. Valid: attack, defend, wait, cast:<ability>"}), 400

    # Build new state
    state = build_state(battle_id, team_a, team_b, state["name_a"], state["name_b"], log, turn_index, mode)

    # If battle ended, update league (PvP only) and save log
    if state["battle_over"]:
        winner = state["winner"]
        if mode == "pvp" and winner and winner != "draw":
            loser = state["name_b"] if winner == state["name_a"] else state["name_a"]
            update_league(conn, winner, "win")
            update_league(conn, loser, "loss")
        elif mode == "pvp" and winner == "draw":
            update_league(conn, state["name_a"], "draw")
            update_league(conn, state["name_b"], "draw")

        conn.execute(
            "INSERT INTO battle_logs (name_a, name_b, winner, mode, log) VALUES (?, ?, ?, ?, ?)",
            (state["name_a"], state["name_b"], winner or "draw", mode, "\n".join(log))
        )

    conn.execute("UPDATE active_battles SET state=? WHERE id=?", (json.dumps(state), battle_id))
    conn.commit()
    conn.close()

    return jsonify(state), 200


@app.route("/battle/state/<int:battle_id>", methods=["GET"])
def get_battle_state(battle_id):
    """
    Get the current state of an ongoing or completed turn-based battle.

    Used by: PvP frontend, PvE frontend, or any service that needs
    to check the current state of a battle without submitting an action.

    Output (JSON): Full game state (same format as /battle/start).
    """
    conn = get_db()
    row = conn.execute("SELECT state FROM active_battles WHERE id=?", (battle_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Battle not found"}), 404
    return jsonify(json.loads(row["state"])), 200


# -------------------------------------------------------
# AUTO-BATTLE ENDPOINT
# Used by: PvE service (no player input needed)
# -------------------------------------------------------

@app.route("/battle/run", methods=["POST"])
def auto_battle():
    """
    Run a complete battle automatically in a single API call.

    This is intended for the PvE service (or any service) that
    does not need turn-by-turn player input — the AI plays both sides.

    Input (JSON):
        team_a      (list) : List of hero objects for team A (the player's party).
        team_b      (list) : List of hero objects for team B (the enemies).
        name_a      (str)  : Name/label for team A.
        name_b      (str)  : Name/label for team B.

    Output (JSON):
        winner      (str)  : "inviter", "invitee", or "draw".
        battle_log  (list) : Full step-by-step log of the battle.
        team_a      (list) : Final state of team A after battle.
        team_b      (list) : Final state of team B after battle.

    Example call from PvE service (Python):
        import requests
        result = requests.post("http://battle-service:5003/battle/run", json={
            "team_a": player_party,
            "team_b": enemy_party,
            "name_a": "Player",
            "name_b": "Enemies"
        }).json()
        if result["winner"] == "inviter":
            # player won
    """
    data = request.get_json()
    team_a = data.get("team_a")
    team_b = data.get("team_b")
    name_a = data.get("name_a", "Team A")
    name_b = data.get("name_b", "Team B")

    if not team_a or not team_b:
        return jsonify({"error": "team_a and team_b are required"}), 400

    result = run_battle(team_a, team_b, name_a, name_b)
    return jsonify({
        "winner": result["winner"],
        "battle_log": result["log"],
        "team_a": result["inviter_party"],
        "team_b": result["invitee_party"],
    }), 200


# -------------------------------------------------------
# PVP INVITATION ENDPOINTS
# Used by: Frontend / API Gateway
# -------------------------------------------------------

@app.route("/pvp/invite", methods=["POST"])
def send_invite():
    """
    Send a PvP invitation.
    Input:  { "inviter": "alice", "invitee": "bob" }
    Output: { "invitation_id": 1, "status": "pending" }
    """
    data = request.get_json()
    inviter = data.get("inviter", "").strip()
    invitee = data.get("invitee", "").strip()
    if not inviter or not invitee:
        return jsonify({"error": "inviter and invitee are required"}), 400
    if inviter == invitee:
        return jsonify({"error": "You cannot invite yourself"}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM invitations WHERE inviter=? AND invitee=? AND status='pending'",
        (inviter, invitee)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "A pending invitation already exists", "invitation_id": existing["id"]}), 409

    cursor = conn.execute("INSERT INTO invitations (inviter, invitee) VALUES (?, ?)", (inviter, invitee))
    conn.commit()
    inv_id = cursor.lastrowid
    conn.close()
    return jsonify({"invitation_id": inv_id, "status": "pending"}), 201


@app.route("/pvp/invite/<int:inv_id>/respond", methods=["POST"])
def respond_to_invite(inv_id):
    """
    Accept or decline an invitation.
    Input:  { "action": "accept" }
    Output: { "invitation_id": 1, "status": "accepted" }
    """
    data = request.get_json()
    action = data.get("action", "").strip().lower()
    if action not in ("accept", "decline"):
        return jsonify({"error": "action must be 'accept' or 'decline'"}), 400

    conn = get_db()
    invite = conn.execute("SELECT * FROM invitations WHERE id=?", (inv_id,)).fetchone()
    if not invite:
        conn.close()
        return jsonify({"error": "Invitation not found"}), 404
    if invite["status"] != "pending":
        conn.close()
        return jsonify({"error": f"Invitation is already {invite['status']}"}), 400

    new_status = "accepted" if action == "accept" else "declined"
    conn.execute("UPDATE invitations SET status=? WHERE id=?", (new_status, inv_id))
    conn.commit()
    conn.close()
    return jsonify({"invitation_id": inv_id, "status": new_status}), 200


@app.route("/pvp/invite/<int:inv_id>", methods=["GET"])
def get_invite(inv_id):
    conn = get_db()
    invite = conn.execute("SELECT * FROM invitations WHERE id=?", (inv_id,)).fetchone()
    conn.close()
    if not invite:
        return jsonify({"error": "Invitation not found"}), 404
    return jsonify({"invitation_id": invite["id"], "inviter": invite["inviter"],
                    "invitee": invite["invitee"], "status": invite["status"]}), 200


@app.route("/pvp/invitations", methods=["GET"])
def list_invites():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"error": "username query param is required"}), 400
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM invitations WHERE inviter=? OR invitee=?", (username, username)
    ).fetchall()
    conn.close()
    return jsonify({"invitations": [
        {"invitation_id": r["id"], "inviter": r["inviter"],
         "invitee": r["invitee"], "status": r["status"]} for r in rows
    ]}), 200


# -------------------------------------------------------
# LEAGUE ENDPOINTS
# -------------------------------------------------------

@app.route("/pvp/league", methods=["GET"])
def get_standings():
    conn = get_db()
    rows = conn.execute("SELECT * FROM league ORDER BY wins DESC").fetchall()
    conn.close()
    return jsonify({"standings": [
        {"username": r["username"], "wins": r["wins"],
         "losses": r["losses"], "draws": r["draws"]} for r in rows
    ]}), 200


@app.route("/pvp/league/<username>", methods=["GET"])
def get_player_stats(username):
    conn = get_db()
    row = conn.execute("SELECT * FROM league WHERE username=?", (username,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Player not found"}), 404
    return jsonify({"username": row["username"], "wins": row["wins"],
                    "losses": row["losses"], "draws": row["draws"]}), 200


# -------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)