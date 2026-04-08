"""
tests.py - Unit and Integration Tests for the Battle Service
-------------------------------------------------------------
Run with:  python tests.py

Covers:
  - PvP invitation endpoints
  - Turn-based battles (PvP mode)
  - Turn-based battles (PvE mode)
  - Auto-battle endpoint (for PvE service)
  - League standings
  - Full battle flow integration tests
"""

import unittest
import json
import os
import app as app_module
from app import app, init_db


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def make_hero(name="Hero", level=1, attack=10, defense=5, hp=100, mana=80, class_name="Warrior"):
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


def start_battle(client, team_a=None, team_b=None, mode="pvp"):
    if team_a is None:
        team_a = [make_hero("Alice", level=5, attack=20)]
    if team_b is None:
        team_b = [make_hero("Bob", level=5, attack=18)]
    return client.post("/battle/start",
        data=json.dumps({
            "team_a": team_a, "team_b": team_b,
            "name_a": "alice", "name_b": "bob",
            "mode": mode
        }),
        content_type="application/json")


def do_action(client, battle_id, action, target_index=0):
    return client.post("/battle/action",
        data=json.dumps({"battle_id": battle_id, "action": action, "target_index": target_index}),
        content_type="application/json")


def play_to_end(client, battle_id, max_turns=100):
    """Keep attacking until the battle is over."""
    for _ in range(max_turns):
        state = client.get(f"/battle/state/{battle_id}").get_json()
        if state["battle_over"]:
            return state
        do_action(client, battle_id, "attack", target_index=0)
    return client.get(f"/battle/state/{battle_id}").get_json()


# -------------------------------------------------------
# Base test class
# -------------------------------------------------------

class BaseTest(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app_module.DB = "test_pvp.db"
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def tearDown(self):
        if os.path.exists("test_pvp.db"):
            os.remove("test_pvp.db")


# -------------------------------------------------------
# Invitation tests
# -------------------------------------------------------

class TestInvitations(BaseTest):

    def test_send_invite(self):
        rv = send_invite(self.client)
        self.assertEqual(rv.status_code, 201)
        self.assertEqual(rv.get_json()["status"], "pending")

    def test_cannot_invite_yourself(self):
        self.assertEqual(send_invite(self.client, "alice", "alice").status_code, 400)

    def test_duplicate_invite_blocked(self):
        send_invite(self.client)
        self.assertEqual(send_invite(self.client).status_code, 409)

    def test_accept_invite(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        rv = accept_invite(self.client, inv_id)
        self.assertEqual(rv.get_json()["status"], "accepted")

    def test_decline_invite(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        rv = self.client.post(f"/pvp/invite/{inv_id}/respond",
            data=json.dumps({"action": "decline"}), content_type="application/json")
        self.assertEqual(rv.get_json()["status"], "declined")

    def test_get_invite(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        rv = self.client.get(f"/pvp/invite/{inv_id}")
        self.assertEqual(rv.get_json()["inviter"], "alice")

    def test_get_nonexistent_invite(self):
        self.assertEqual(self.client.get("/pvp/invite/9999").status_code, 404)

    def test_list_invites(self):
        send_invite(self.client, "alice", "bob")
        send_invite(self.client, "charlie", "alice")
        rv = self.client.get("/pvp/invitations?username=alice")
        self.assertEqual(len(rv.get_json()["invitations"]), 2)

    def test_invalid_response_action(self):
        inv_id = send_invite(self.client).get_json()["invitation_id"]
        rv = self.client.post(f"/pvp/invite/{inv_id}/respond",
            data=json.dumps({"action": "maybe"}), content_type="application/json")
        self.assertEqual(rv.status_code, 400)


# -------------------------------------------------------
# Turn-based battle tests — PvP mode
# -------------------------------------------------------

class TestTurnBattlePvP(BaseTest):

    def test_start_pvp_battle(self):
        rv = start_battle(self.client, mode="pvp")
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertEqual(data["mode"], "pvp")
        self.assertFalse(data["battle_over"])
        self.assertIn("battle_id", data)

    def test_current_turn_shows_actions_and_targets(self):
        rv = start_battle(self.client, mode="pvp")
        turn = rv.get_json()["current_turn"]
        self.assertIn("attack", turn["available_actions"])
        self.assertIn("defend", turn["available_actions"])
        self.assertGreater(len(turn["valid_targets"]), 0)

    def test_attack_reduces_enemy_hp(self):
        rv = start_battle(self.client,
            team_a=[make_hero("Alice", attack=20, defense=5, hp=100)],
            team_b=[make_hero("Bob", attack=5, defense=5, hp=100)],
            mode="pvp")
        battle_id = rv.get_json()["battle_id"]
        state = rv.get_json()
        # Only attack if it's team_a's turn
        if state["current_turn"]["team"] == "a":
            rv2 = do_action(self.client, battle_id, "attack", target_index=0)
            bob_hp = rv2.get_json()["team_b"][0]["hp"]
            self.assertLess(bob_hp, 100)

    def test_defend_restores_hp_and_mana(self):
        hero = make_hero("Alice", hp=80, mana=70)
        rv = start_battle(self.client, team_a=[hero], team_b=[make_hero("Bob")], mode="pvp")
        battle_id = rv.get_json()["battle_id"]
        state = rv.get_json()
        if state["current_turn"]["team"] == "a":
            rv2 = do_action(self.client, battle_id, "defend")
            alice = rv2.get_json()["team_a"][0]
            self.assertGreaterEqual(alice["hp"], 80)
            self.assertGreaterEqual(alice["mana"], 70)

    def test_invalid_action_rejected(self):
        battle_id = start_battle(self.client, mode="pvp").get_json()["battle_id"]
        rv = do_action(self.client, battle_id, "fly_away")
        self.assertEqual(rv.status_code, 400)

    def test_pvp_battle_ends_and_has_winner(self):
        strong = [make_hero("Crusher", attack=999, defense=999, hp=9999)]
        weak = [make_hero("Minion", attack=1, defense=1, hp=1)]
        battle_id = start_battle(self.client, team_a=strong, team_b=weak, mode="pvp").get_json()["battle_id"]
        final = play_to_end(self.client, battle_id)
        self.assertTrue(final["battle_over"])
        self.assertEqual(final["winner"], "alice")

    def test_pvp_battle_updates_league(self):
        strong = [make_hero("Crusher", attack=999, defense=999, hp=9999)]
        weak = [make_hero("Minion", attack=1, defense=1, hp=1)]
        battle_id = start_battle(self.client, team_a=strong, team_b=weak, mode="pvp").get_json()["battle_id"]
        play_to_end(self.client, battle_id)
        rv = self.client.get("/pvp/league")
        usernames = [s["username"] for s in rv.get_json()["standings"]]
        self.assertIn("alice", usernames)

    def test_action_after_battle_ends_rejected(self):
        strong = [make_hero("Crusher", attack=999, defense=999, hp=9999)]
        weak = [make_hero("Minion", attack=1, defense=1, hp=1)]
        battle_id = start_battle(self.client, team_a=strong, team_b=weak, mode="pvp").get_json()["battle_id"]
        play_to_end(self.client, battle_id)
        rv = do_action(self.client, battle_id, "attack")
        self.assertEqual(rv.status_code, 400)

    def test_multiple_heroes_per_team(self):
        team_a = [make_hero(f"A{i}", level=3) for i in range(3)]
        team_b = [make_hero(f"B{i}", level=3) for i in range(3)]
        rv = start_battle(self.client, team_a=team_a, team_b=team_b, mode="pvp")
        self.assertEqual(len(rv.get_json()["team_a"]), 3)
        self.assertEqual(len(rv.get_json()["team_b"]), 3)

    def test_cast_fireball(self):
        hero = make_hero("Alice", attack=20, mana=80, class_name="Chaos")
        rv = start_battle(self.client, team_a=[hero], team_b=[make_hero("Bob", hp=200)], mode="pvp")
        battle_id = rv.get_json()["battle_id"]
        state = rv.get_json()
        if state["current_turn"]["team"] == "a" and "cast:fireball" in state["current_turn"]["available_actions"]:
            rv2 = do_action(self.client, battle_id, "cast:fireball", target_index=0)
            self.assertEqual(rv2.status_code, 200)

    def test_get_battle_state(self):
        battle_id = start_battle(self.client, mode="pvp").get_json()["battle_id"]
        rv = self.client.get(f"/battle/state/{battle_id}")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["battle_id"], battle_id)

    def test_get_nonexistent_battle(self):
        self.assertEqual(self.client.get("/battle/state/9999").status_code, 404)

    def test_invalid_mode_rejected(self):
        rv = self.client.post("/battle/start",
            data=json.dumps({"team_a": [make_hero()], "team_b": [make_hero()], "mode": "badmode"}),
            content_type="application/json")
        self.assertEqual(rv.status_code, 400)


# -------------------------------------------------------
# Turn-based battle tests — PvE mode
# -------------------------------------------------------

class TestTurnBattlePvE(BaseTest):

    def test_start_pve_battle(self):
        rv = start_battle(self.client, mode="pve")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["mode"], "pve")

    def test_pve_battle_ends_with_winner(self):
        strong = [make_hero("Hero", attack=999, defense=999, hp=9999)]
        weak = [make_hero("Enemy", attack=1, defense=1, hp=1)]
        battle_id = start_battle(self.client, team_a=strong, team_b=weak, mode="pve").get_json()["battle_id"]
        final = play_to_end(self.client, battle_id)
        self.assertTrue(final["battle_over"])
        self.assertIsNotNone(final["winner"])

    def test_pve_battle_does_not_update_league(self):
        """PvE battles should not affect PvP league standings."""
        strong = [make_hero("Hero", attack=999, defense=999, hp=9999)]
        weak = [make_hero("Enemy", attack=1, defense=1, hp=1)]
        battle_id = start_battle(self.client, team_a=strong, team_b=weak, mode="pve").get_json()["battle_id"]
        play_to_end(self.client, battle_id)
        rv = self.client.get("/pvp/league")
        self.assertEqual(rv.get_json()["standings"], [])

    def test_pve_valid_targets_shown(self):
        """PvE service needs valid_targets to know which enemies can be attacked."""
        rv = start_battle(self.client,
            team_a=[make_hero("Hero")],
            team_b=[make_hero("Enemy1"), make_hero("Enemy2")],
            mode="pve")
        turn = rv.get_json()["current_turn"]
        self.assertIn("valid_targets", turn)

    def test_pve_full_battle_flow(self):
        """Integration test: simulate a full PvE battle from start to finish."""
        player = [make_hero("Hero", attack=30, defense=10, hp=200)]
        enemies = [make_hero("Goblin", attack=8, defense=3, hp=30),
                   make_hero("Orc", attack=10, defense=5, hp=50)]
        battle_id = start_battle(self.client, team_a=player, team_b=enemies, mode="pve").get_json()["battle_id"]
        final = play_to_end(self.client, battle_id)
        self.assertTrue(final["battle_over"])
        self.assertIsNotNone(final["winner"])
        self.assertEqual(final["mode"], "pve")


# -------------------------------------------------------
# Auto-battle tests (for PvE service calling /battle/run)
# -------------------------------------------------------

class TestAutoBattle(BaseTest):

    def test_auto_battle_returns_result(self):
        rv = self.client.post("/battle/run",
            data=json.dumps({
                "team_a": [make_hero("Player", attack=20, hp=200)],
                "team_b": [make_hero("Enemy", attack=5, hp=50)],
                "name_a": "Player", "name_b": "Enemy"
            }),
            content_type="application/json")
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertIn("winner", data)
        self.assertIn("battle_log", data)
        self.assertIn("team_a", data)
        self.assertIn("team_b", data)

    def test_auto_battle_strong_team_wins(self):
        for _ in range(3):
            rv = self.client.post("/battle/run",
                data=json.dumps({
                    "team_a": [make_hero("S", attack=999, defense=999, hp=9999)],
                    "team_b": [make_hero("W", attack=1, defense=1, hp=1)],
                    "name_a": "strong", "name_b": "weak"
                }),
                content_type="application/json")
            self.assertEqual(rv.get_json()["winner"], "inviter")

    def test_auto_battle_missing_teams(self):
        rv = self.client.post("/battle/run",
            data=json.dumps({"team_a": [make_hero()]}),
            content_type="application/json")
        self.assertEqual(rv.status_code, 400)

    def test_auto_battle_returns_final_hero_states(self):
        rv = self.client.post("/battle/run",
            data=json.dumps({
                "team_a": [make_hero("P", attack=999, hp=9999)],
                "team_b": [make_hero("E", attack=1, hp=1)],
                "name_a": "p", "name_b": "e"
            }),
            content_type="application/json")
        data = rv.get_json()
        # Enemy should be at 0 HP
        self.assertEqual(data["team_b"][0]["hp"], 0)


# -------------------------------------------------------
# League tests
# -------------------------------------------------------

class TestLeague(BaseTest):

    def test_league_starts_empty(self):
        self.assertEqual(self.client.get("/pvp/league").get_json()["standings"], [])

    def test_get_unknown_player(self):
        self.assertEqual(self.client.get("/pvp/league/nobody").status_code, 404)

    def test_league_sorted_by_wins(self):
        # Alice wins twice
        for _ in range(2):
            strong = [make_hero("Alice", attack=999, hp=9999)]
            weak = [make_hero("Charlie", attack=1, hp=1)]
            battle_id = start_battle(self.client, team_a=strong, team_b=weak, mode="pvp").get_json()["battle_id"]
            play_to_end(self.client, battle_id)
        standings = self.client.get("/pvp/league").get_json()["standings"]
        self.assertEqual(standings[0]["username"], "alice")
        self.assertEqual(standings[0]["wins"], 2)


# -------------------------------------------------------
# Health check
# -------------------------------------------------------

class TestHealth(BaseTest):

    def test_health(self):
        rv = self.client.get("/health")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)