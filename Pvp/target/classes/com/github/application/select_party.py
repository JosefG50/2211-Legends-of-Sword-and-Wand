from domain.entities.party import Party

class SelectPartyService:

    def select_party(self, invitation, username: str, party: Party):
        """
        Assign a selected party to a user in the invitation.
        """
        invitation.select_party(username, party)