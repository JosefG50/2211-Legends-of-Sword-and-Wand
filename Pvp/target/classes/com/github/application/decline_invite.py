class DeclineInviteService:

    def decline(self, invitation):
        """
        Decline an invitation.
        """
        invitation.decline()