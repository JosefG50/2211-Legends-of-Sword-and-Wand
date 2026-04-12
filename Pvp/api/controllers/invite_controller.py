class InviteController:

    def __init__(
        self,
        invite_service,
        accept_service,
        decline_service
    ):
        self.invite_service = invite_service
        self.accept_service = accept_service
        self.decline_service = decline_service

    def send_invite(self, inviter: str, invitee: str):
        return self.invite_service.invite_player(inviter, invitee)

    def accept_invite(self, invite_id: int):
        return self.accept_service.accept_invite(invite_id)

    def decline_invite(self, invite_id: int):
        return self.decline_service.decline_invite(invite_id)