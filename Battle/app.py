"""
PvP Service - Legends of Sword and Wand
----------------------------------------
This service handles everything PvP related:
  - Sending and accepting battle invitations
  - Running the battle between two parties
  - Tracking wins/losses in the league standings
"""

from flask import Flask, request, jsonify
import sqlite3
import os
from battle import run_battle

app = Flask(__name__)
DB = "pvp.db"


# -------------------------------------------------------
# Database setup
# -------------------------------------------------------

def get_db():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def init_db():
    """Create the tables if they don't exist yet."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invitations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter     TEXT NOT NULL,
            invitee     TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS league (
            username    TEXT PRIMARY KEY,
            wins        INTEGER NOT NULL DEFAULT 0,
            losses      INTEGER NOT NULL DEFAULT 0,
            draws       INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS battle_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter     TEXT NOT NULL,
            invitee     TEXT NOT NULL,
            winner      TEXT NOT NULL,
            log         TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


# -------------------------------------------------------
# Helper: update league record for a player
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
# Routes: Invitations
# -------------------------------------------------------

@app.route("/pvp/invite", methods=["POST"])
def send_invite():
    """
    Send a PvP invitation to another player.

    Input  (JSON): { "inviter": "alice", "invitee": "bob" }
    Output (JSON): { "invitation_id": 1, "status": "pending" }
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

    cursor = conn.execute(
        "INSERT INTO invitations (inviter, invitee) VALUES (?, ?)",
        (inviter, invitee)
    )
    conn.commit()
    inv_id = cursor.lastrowid
    conn.close()

    return jsonify({"invitation_id": inv_id, "status": "pending"}), 201


@app.route("/pvp/invite/<int:inv_id>/respond", methods=["POST"])
def respond_to_invite(inv_id):
    """
    Accept or decline an invitation.

    Input  (JSON): { "action": "accept" }  or  { "action": "decline" }
    Output (JSON): { "invitation_id": 1, "status": "accepted" }
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
    """
    Get the details of an invitation.

    Output (JSON): { "invitation_id": 1, "inviter": "alice", "invitee": "bob", "status": "pending" }
    """
    conn = get_db()
    invite = conn.execute("SELECT * FROM invitations WHERE id=?", (inv_id,)).fetchone()
    conn.close()

    if not invite:
        return jsonify({"error": "Invitation not found"}), 404

    return jsonify({
        "invitation_id": invite["id"],
        "inviter": invite["inviter"],
        "invitee": invite["invitee"],
        "status": invite["status"]
    }), 200


@app.route("/pvp/invitations", methods=["GET"])
def list_invites():
    """
    List all invitations for a given player (sent or received).

    Query param: ?username=alice
    Output (JSON): { "invitations": [ ... ] }
    """
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"error": "username query param is required"}), 400

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM invitations WHERE inviter=? OR invitee=?",
        (username, username)
    ).fetchall()
    conn.close()

    invitations = [
        {"invitation_id": r["id"], "inviter": r["inviter"],
         "invitee": r["invitee"], "status": r["status"]}
        for r in rows
    ]
    return jsonify({"invitations": invitations}), 200


# -------------------------------------------------------
# Routes: Battle
# -------------------------------------------------------

@app.route("/pvp/battle/start", methods=["POST"])
def start_battle():
    """
    Start a PvP battle between two parties.
    The invitation must be in 'accepted' state first.

    Input (JSON):
    {
        "invitation_id": 1,
        "inviter_party": [ { hero data }, ... ],
        "invitee_party": [ { hero data }, ... ]
    }

    Hero data fields:
        name, level, attack, defense, hp, max_hp, mana, max_mana, class_name

    Output (JSON):
    {
        "result": "inviter_wins",
        "winner": "alice",
        "battle_log": [ "Round 1 ...", ... ],
        "inviter_party": [ ... ],
        "invitee_party": [ ... ]
    }
    """
    data = request.get_json()
    inv_id = data.get("invitation_id")
    inviter_party = data.get("inviter_party")
    invitee_party = data.get("invitee_party")

    if not inv_id or not inviter_party or not invitee_party:
        return jsonify({"error": "invitation_id, inviter_party, and invitee_party are required"}), 400

    conn = get_db()
    invite = conn.execute("SELECT * FROM invitations WHERE id=?", (inv_id,)).fetchone()

    if not invite:
        conn.close()
        return jsonify({"error": "Invitation not found"}), 404

    if invite["status"] != "accepted":
        conn.close()
        return jsonify({"error": f"Invitation must be accepted first (currently: {invite['status']})"}), 409

    result = run_battle(inviter_party, invitee_party, invite["inviter"], invite["invitee"])

    if result["winner"] == "inviter":
        winner_name = invite["inviter"]
        update_league(conn, invite["inviter"], "win")
        update_league(conn, invite["invitee"], "loss")
        result_label = "inviter_wins"
    elif result["winner"] == "invitee":
        winner_name = invite["invitee"]
        update_league(conn, invite["inviter"], "loss")
        update_league(conn, invite["invitee"], "win")
        result_label = "invitee_wins"
    else:
        winner_name = "draw"
        update_league(conn, invite["inviter"], "draw")
        update_league(conn, invite["invitee"], "draw")
        result_label = "draw"

    log_text = "\n".join(result["log"])
    conn.execute(
        "INSERT INTO battle_logs (inviter, invitee, winner, log) VALUES (?, ?, ?, ?)",
        (invite["inviter"], invite["invitee"], winner_name, log_text)
    )

    conn.execute("UPDATE invitations SET status='completed' WHERE id=?", (inv_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "result": result_label,
        "winner": winner_name,
        "battle_log": result["log"],
        "inviter_party": result["inviter_party"],
        "invitee_party": result["invitee_party"]
    }), 200


# -------------------------------------------------------
# Routes: League
# -------------------------------------------------------

@app.route("/pvp/league", methods=["GET"])
def get_standings():
    """
    Get the full league standings, sorted by wins.

    Output (JSON): { "standings": [ { "username": "alice", "wins": 3, "losses": 1, "draws": 0 }, ... ] }
    """
    conn = get_db()
    rows = conn.execute("SELECT * FROM league ORDER BY wins DESC").fetchall()
    conn.close()

    standings = [
        {"username": r["username"], "wins": r["wins"], "losses": r["losses"], "draws": r["draws"]}
        for r in rows
    ]
    return jsonify({"standings": standings}), 200


@app.route("/pvp/league/<username>", methods=["GET"])
def get_player_stats(username):
    """
    Get league stats for one player.

    Output (JSON): { "username": "alice", "wins": 3, "losses": 1, "draws": 0 }
    """
    conn = get_db()
    row = conn.execute("SELECT * FROM league WHERE username=?", (username,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Player not found"}), 404

    return jsonify({
        "username": row["username"],
        "wins": row["wins"],
        "losses": row["losses"],
        "draws": row["draws"]
    }), 200


# -------------------------------------------------------
# Health check
# -------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# -------------------------------------------------------
# Run the app
# -------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
