import pytest
from application.invite_player import InvitePlayerService
from domain.entities.user import User
from domain.entities.party import Party
from domain.entities.invitation import Invitation

def make_user_with_party(username):
    party = Party(party_id="p1", owner_username=username, hero_ids=("h1","h2"))
    return User(username=username, parties=(party,))

def test_create_invitation_happy_path():
    inviter = make_user_with_party("alice")
    invitee = make_user_with_party("bob")
    service = InvitePlayerService()
    invitation = service.create_invitation(inviter, invitee)
    assert isinstance(invitation, Invitation)
    assert invitation.inviter == inviter
    assert invitation.invitee == invitee