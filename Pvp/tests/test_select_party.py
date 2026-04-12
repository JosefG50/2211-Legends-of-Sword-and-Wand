import pytest
from application.select_party import SelectPartyService
from domain.entities.user import User
from domain.entities.party import Party
from domain.entities.invitation import Invitation, InvitationStatus

def make_user_with_party(username):
    party = Party(party_id="p1", owner_username=username, hero_ids=("h1","h2"))
    return User(username=username, parties=(party,)), party

def test_select_party_happy_path():
    inviter, inviter_party = make_user_with_party("alice")
    invitee, invitee_party = make_user_with_party("bob")
    invitation = Invitation(inviter, invitee)
    invitation.status = InvitationStatus.ACCEPTED
    service = SelectPartyService()
    service.select_party(invitation, "alice", inviter_party)
    service.select_party(invitation, "bob", invitee_party)
    assert invitation.status == InvitationStatus.READY