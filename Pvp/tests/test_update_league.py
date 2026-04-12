import pytest
from application.update_league import UpdateLeagueService
from domain.entities.league_record import LeagueRecord
from domain.entities.battle_match import BattleMatch
from domain.entities.party import Party

def make_party(username, party_id="p1"):
    return Party(party_id=party_id, owner_username=username, hero_ids=("h1","h2"))

def test_update_league_happy_path():
    p1 = make_party("alice")
    p2 = make_party("bob")
    match = BattleMatch("alice", "bob", p1, p2)
    match.record_result("alice")
    league_records = {
        "alice": LeagueRecord("alice"),
        "bob": LeagueRecord("bob")
    }
    service = UpdateLeagueService()
    service.update(match, league_records)
    assert league_records["alice"].wins == 1
    assert league_records["bob"].losses == 1