from domain.entities.invitation import Invitation

class InvitePlayerService:

    def create_invitation(self, inviter, invitee):
        """
        Create an Invitation between inviter and invitee.
        """
        if inviter.username == invitee.username:
            raise ValueError("Cannot invite yourself")

        if not inviter.has_parties():
            raise ValueError("Inviter has no parties")

        if not invitee.has_parties():
            raise ValueError("Invitee has no parties")

        return Invitation(inviter=inviter, invitee=invitee)