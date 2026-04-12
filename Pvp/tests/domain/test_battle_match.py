import pytest
from domain.entities.battle_match import BattleMatch
from domain.entities.party import Party

def make_party(username, party_id="p1"):
    return Party(party_id=party_id, owner_username=username, hero_ids=("h1","h2"))

def test_record_result_and_finished():
    p1 = make_party("alice")
    p2 = make_party("bob")
    match = BattleMatch("alice", "bob", p1, p2)

    match.record_result("alice")
    assert match.winner_username == "alice"
    assert match.loser_username == "bob"
    assert match.is_finished()

def test_record_result_invalid_winner_raises():
    p1 = make_party("alice")
    p2 = make_party("bob")
    match = BattleMatch("alice", "bob", p1, p2)

    with pytest.raises(ValueError):
        match.record_result("charlie")