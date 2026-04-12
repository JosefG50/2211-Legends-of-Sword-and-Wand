import pytest
from domain.entities.user import User
from domain.entities.party import Party

def make_user_with_party(username, party_id="p1"):
    party = Party(
        party_id=party_id,
        owner_username=username,
        hero_ids=("h1", "h2")
    )
    return User(username=username, parties=(party,)), party

def test_has_parties_true():
    user, _ = make_user_with_party("alice")
    assert user.has_parties()

def test_has_parties_false():
    user = User(username="bob")
    assert not user.has_parties()

def test_get_party_existing():
    user, party = make_user_with_party("alice")
    assert user.get_party(party.party_id) == party

def test_get_party_nonexistent():
    user, _ = make_user_with_party("alice")
    assert user.get_party("invalid") is None