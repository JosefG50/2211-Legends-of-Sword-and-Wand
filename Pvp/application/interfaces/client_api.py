# application/interfaces/client_api.py

from application.invite_player import InvitePlayerService
from application.accept_invite import AcceptInviteService
from application.decline_invite import DeclineInviteService
from application.select_party import SelectPartyService
from application.start_battle import StartBattleService

class ClientAPI:
    """
    Simulates the endpoints/UI requests for PvP service.
    """

    def __init__(self, invite_service, accept_service, decline_service,
                 select_party_service, start_battle_service):
        self.invite_service = invite_service
        self.accept_service = accept_service
        self.decline_service = decline_service
        self.select_party_service = select_party_service
        self.start_battle_service = start_battle_service

    # ----- Invitation endpoints -----
    def create_invite(self, inviter, invitee):
        return self.invite_service.create_invitation(inviter, invitee)

    def accept_invite(self, invitation):
        self.accept_service.accept(invitation)

    def decline_invite(self, invitation):
        self.decline_service.decline(invitation)

    # ----- Party selection -----
    def select_party(self, invitation, username, party):
        self.select_party_service.select_party(invitation, username, party)

    # ----- Battle -----
    def start_battle(self, invitation):
        return self.start_battle_service.start_battle(invitation)