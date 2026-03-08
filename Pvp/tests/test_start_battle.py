import pytest
from application.start_battle import StartBattleService
from domain.entities.user import User
from domain.entities.party import Party
from domain.entities.invitation import Invitation, InvitationStatus

def make_user_with_party(username):
    party = Party(party_id="p1", owner_username=username, hero_ids=("h1","h2"))
    return User(username=username, parties=(party,)), party

def test_start_battle_happy_path():
    inviter, inviter_party = make_user_with_party("alice")
    invitee, invitee_party = make_user_with_party("bob")
    
    invitation = Invitation(inviter, invitee)
    invitation.status = InvitationStatus.ACCEPTED

    # Use select_party to properly set parties and trigger _check_ready
    invitation.select_party("alice", inviter_party)
    invitation.select_party("bob", invitee_party)
    
    service = StartBattleService()
    battle = service.start_battle(invitation)

    assert battle.player1_username == "alice"
    assert battle.player2_username == "bob"
    assert battle.player1_party == inviter_party
    assert battle.player2_party == invitee_party
    assert invitation.is_ready_for_battle()