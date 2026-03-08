import pytest
from application.decline_invite import DeclineInviteService
from domain.entities.user import User
from domain.entities.party import Party
from domain.entities.invitation import Invitation, InvitationStatus

def make_user_with_party(username):
    party = Party(party_id="p1", owner_username=username, hero_ids=("h1","h2"))
    return User(username=username, parties=(party,))

def test_decline_invitation_happy_path():
    inviter = make_user_with_party("alice")
    invitee = make_user_with_party("bob")
    invitation = Invitation(inviter, invitee)
    service = DeclineInviteService()
    service.decline(invitation)
    assert invitation.status == InvitationStatus.DECLINED