from domain.entities.party import Party

def test_hero_count():
    party = Party(party_id="p1", owner_username="alice", hero_ids=("h1", "h2", "h3"))
    assert party.hero_count() == 3