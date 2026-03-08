import pytest
from domain.entities.league_record import LeagueRecord

def test_record_win_loss():
    record = LeagueRecord(username="alice")
    record.record_win()
    record.record_loss()
    assert record.wins == 1
    assert record.losses == 1

def test_record_match_winner():
    record = LeagueRecord(username="alice")
    record.record_match("alice")
    assert record.wins == 1
    assert record.losses == 0

def test_record_match_loser():
    record = LeagueRecord(username="alice")
    record.record_match("bob")
    assert record.wins == 0
    assert record.losses == 1