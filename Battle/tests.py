"""
tests.py - Unit tests for the PvP Service
------------------------------------------
Run with:  python tests.py

Uses Python's built-in unittest — no extra installs needed.
"""

import unittest
import json
import os
import Battle.app as app_module
from Battle.app import app, init_db
from Battle.battle import Hero, run_battle, do_basic_attack, do_defend, cast_heal, cast_protect


# -------------------------------------------------------
# Helpers shared across all tests
# -------------------------------------------------------

def make_hero(name="Hero", level=1, attack=10, defense=5, hp=100, mana=50, class_name="Warrior"):
    """Create a simple hero dictionary for testing."""
    return {
        "name": name, "level": level, "attack": attack, "defense": defense,
        "hp": hp, "max_hp": hp, "mana": mana, "max_mana": mana,
        "shield": 0, "class_name": class_name
    }


def send_invite(client, inviter="alice", invitee="bob"):
    return client.post("/pvp/invite",
        data=json.dumps({"inviter": inviter, "invitee": invitee}),
        content_type="application/json")


def accept_invite(client, inv_id):
    return client.post(f"/pvp/invite/{inv_id}/respond",
        data=json.dumps({"action": "accept"}),
        content_type="application/json")


def start_battle(client, inv_id, party_a=None, party_b=None):
    if party_a is None:
        party_a = [make_hero("Alice Hero")]
    if party_b is None:
        party_b = [make_hero("Bob Hero")]
    return client.post("/pvp/battle/start",
        data=json.dumps({"invitation_id": inv_id, "inviter_party": party_a, "invitee_party": party_b}),
        content_type="application/json")


# -------------------------------------------------------
# Base test class — sets up a fresh database for each test
# -------------------------------------------------------

class BaseTest(unittest.TestCase):

    def setUp(self):
        """Runs before every test — create a clean test database."""
        app.config["TESTING"] = True
        app_module.DB = "test_pvp.db"
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def tearDown(self):
        """Runs after every test — delete the test database."""
        if os.path.exists("test_pvp.db"):
            os.remove("test_pvp.db")


# -------------------------------------------------------
# Invitation tests
# -------------------------------------------------------

class TestInvitations(BaseTest):

    def test_send_invite_success(self):
        rv = send_invite(self.client)
        self.assertEqual(rv.status_code, 201)
        data = rv.get_json()
        self.assertEqual(data["status"], "pending")
        self.assertIn("invitation_id", data)

    def test_send_invite_missing_fields(self):
        rv = self.client.post("/pvp/invite",
            data=json.dumps({"inviter": "alice"}),
            content_type="application/json")
        self.assertEqual(rv.status_code, 400)

    def test_cannot_invite_yourself(self):
        rv = send_invite(self.client, "alice", "alice")
        self.assertEqual(rv.status_code, 400)

    def test_duplicate_invite_blocked(self):
        send_invite(self.client)
        rv = send_invite(self.client)
        self.assertEqual(rv.status_code, 409)

    def test_accept_invite(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        rv = accept_invite(self.client, inv_id)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], "accepted")

    def test_decline_invite(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        rv = self.client.post(f"/pvp/invite/{inv_id}/respond",
            data=json.dumps({"action": "decline"}),
            content_type="application/json")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], "declined")

    def test_invalid_response_action(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        rv = self.client.post(f"/pvp/invite/{inv_id}/respond",
            data=json.dumps({"action": "maybe"}),
            content_type="application/json")
        self.assertEqual(rv.status_code, 400)

    def test_respond_to_nonexistent_invite(self):
        rv = accept_invite(self.client, 9999)
        self.assertEqual(rv.status_code, 404)

    def test_cannot_respond_to_already_accepted(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        accept_invite(self.client, inv_id)
        rv = accept_invite(self.client, inv_id)
        self.assertEqual(rv.status_code, 400)

    def test_get_invite(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        rv = self.client.get(f"/pvp/invite/{inv_id}")
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertEqual(data["inviter"], "alice")
        self.assertEqual(data["invitee"], "bob")

    def test_get_nonexistent_invite(self):
        rv = self.client.get("/pvp/invite/9999")
        self.assertEqual(rv.status_code, 404)

    def test_list_invites_for_user(self):
        send_invite(self.client, "alice", "bob")
        send_invite(self.client, "charlie", "alice")
        rv = self.client.get("/pvp/invitations?username=alice")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(rv.get_json()["invitations"]), 2)

    def test_list_invites_missing_username(self):
        rv = self.client.get("/pvp/invitations")
        self.assertEqual(rv.status_code, 400)


# -------------------------------------------------------
# Battle tests
# -------------------------------------------------------

class TestBattle(BaseTest):

    def test_battle_requires_accepted_invite(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        rv = start_battle(self.client, inv_id)
        self.assertEqual(rv.status_code, 409)

    def test_battle_invalid_invite(self):
        rv = start_battle(self.client, 9999)
        self.assertEqual(rv.status_code, 404)

    def test_battle_missing_party(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        accept_invite(self.client, inv_id)
        rv = self.client.post("/pvp/battle/start",
            data=json.dumps({"invitation_id": inv_id}),
            content_type="application/json")
        self.assertEqual(rv.status_code, 400)

    def test_valid_battle_runs(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        accept_invite(self.client, inv_id)
        rv = start_battle(self.client, inv_id)
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertIn(data["result"], ("inviter_wins", "invitee_wins", "draw"))
        self.assertIn("battle_log", data)
        self.assertIn("inviter_party", data)
        self.assertIn("invitee_party", data)

    def test_strong_team_always_wins(self):
        for _ in range(5):
            inv_id = send_invite(self.client).get_json()["invitation_id"]
            accept_invite(self.client, inv_id)
            rv = start_battle(self.client, inv_id,
                party_a=[make_hero("Tank", attack=999, defense=999, hp=9999)],
                party_b=[make_hero("Minion", attack=1, defense=1, hp=1)])
            self.assertEqual(rv.get_json()["result"], "inviter_wins")

    def test_battle_updates_league(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        accept_invite(self.client, inv_id)
        start_battle(self.client, inv_id)
        rv = self.client.get("/pvp/league")
        usernames = [s["username"] for s in rv.get_json()["standings"]]
        self.assertIn("alice", usernames)
        self.assertIn("bob", usernames)

    def test_completed_invite_cant_be_reused(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        accept_invite(self.client, inv_id)
        start_battle(self.client, inv_id)
        rv = start_battle(self.client, inv_id)
        self.assertEqual(rv.status_code, 409)


# -------------------------------------------------------
# League tests
# -------------------------------------------------------

class TestLeague(BaseTest):

    def test_league_starts_empty(self):
        rv = self.client.get("/pvp/league")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["standings"], [])

    def test_league_sorted_by_wins(self):
        for _ in range(2):
            inv_id = send_invite(self.client, "alice", "charlie").get_json()["invitation_id"]
            accept_invite(self.client, inv_id)
            start_battle(self.client, inv_id,
                party_a=[make_hero("Alice", attack=999, hp=9999)],
                party_b=[make_hero("Charlie", attack=1, hp=1)])

        inv_id = send_invite(self.client, "bob", "dave").get_json()["invitation_id"]
        accept_invite(self.client, inv_id)
        start_battle(self.client, inv_id,
            party_a=[make_hero("Bob", attack=999, hp=9999)],
            party_b=[make_hero("Dave", attack=1, hp=1)])

        standings = self.client.get("/pvp/league").get_json()["standings"]
        self.assertEqual(standings[0]["username"], "alice")
        self.assertEqual(standings[0]["wins"], 2)

    def test_get_player_stats(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        accept_invite(self.client, inv_id)
        start_battle(self.client, inv_id)
        rv = self.client.get("/pvp/league/alice")
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertEqual(data["username"], "alice")
        self.assertEqual(data["wins"] + data["losses"] + data["draws"], 1)

    def test_get_unknown_player(self):
        rv = self.client.get("/pvp/league/nobody")
        self.assertEqual(rv.status_code, 404)


# -------------------------------------------------------
# Battle engine tests (pure logic, no HTTP)
# -------------------------------------------------------

class TestBattleEngine(unittest.TestCase):

    def test_hero_takes_damage(self):
        h = Hero(make_hero(hp=100))
        h.take_damage(30)
        self.assertEqual(h.hp, 70)

    def test_shield_absorbs_damage_first(self):
        h = Hero(make_hero(hp=100))
        h.shield = 20
        h.take_damage(30)
        self.assertEqual(h.shield, 0)
        self.assertEqual(h.hp, 90)

    def test_hp_does_not_go_below_zero(self):
        h = Hero(make_hero(hp=10))
        h.take_damage(9999)
        self.assertEqual(h.hp, 0)

    def test_hero_is_alive(self):
        h = Hero(make_hero(hp=1))
        self.assertTrue(h.is_alive)
        h.hp = 0
        self.assertFalse(h.is_alive)

    def test_restore_hp_capped_at_max(self):
        h = Hero(make_hero(hp=50))
        h.max_hp = 100
        h.restore_hp(9999)
        self.assertEqual(h.hp, 100)

    def test_restore_mana_capped_at_max(self):
        h = Hero(make_hero(mana=10))
        h.max_mana = 50
        h.restore_mana(9999)
        self.assertEqual(h.mana, 50)

    def test_defend_restores_hp_and_mana(self):
        h = Hero(make_hero(hp=50, mana=10))
        h.max_hp = 100
        h.max_mana = 50
        do_defend(h, [])
        self.assertEqual(h.hp, 60)
        self.assertEqual(h.mana, 15)

    def test_basic_attack_reduces_enemy_hp(self):
        attacker = Hero(make_hero("Attacker", attack=20, defense=5))
        defender = Hero(make_hero("Defender", attack=5, defense=5, hp=100))
        do_basic_attack(attacker, [defender], [])
        self.assertEqual(defender.hp, 85)  # 20 - 5 = 15 damage

    def test_cast_heal_restores_hp(self):
        caster = Hero(make_hero(class_name="Order", mana=100))
        injured = Hero(make_hero(hp=40))
        injured.max_hp = 100
        cast_heal(caster, [injured], [])
        self.assertGreater(injured.hp, 40)

    def test_cast_protect_applies_shield(self):
        caster = Hero(make_hero(class_name="Order", mana=100))
        ally = Hero(make_hero(hp=100))
        cast_protect(caster, [ally], [])
        self.assertEqual(ally.shield, 10)  # 10% of 100 max HP

    def test_run_battle_returns_winner(self):
        result = run_battle([make_hero("Alice")], [make_hero("Bob")], "alice", "bob")
        self.assertIn(result["winner"], ("inviter", "invitee", "draw"))
        self.assertGreater(len(result["log"]), 0)

    def test_stronger_hero_wins(self):
        for _ in range(5):
            result = run_battle(
                [make_hero("Strong", attack=999, defense=999, hp=9999)],
                [make_hero("Weak", attack=1, defense=1, hp=1)],
                "alice", "bob"
            )
            self.assertEqual(result["winner"], "inviter")

    def test_battle_log_not_empty(self):
        result = run_battle([make_hero("A")], [make_hero("B")], "alice", "bob")
        self.assertGreater(len(result["log"]), 0)


# -------------------------------------------------------
# Health check
# -------------------------------------------------------

class TestHealth(BaseTest):

    def test_health_endpoint(self):
        rv = self.client.get("/health")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], "ok")


# -------------------------------------------------------
# Run all tests
# -------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
