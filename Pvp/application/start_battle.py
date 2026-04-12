from domain.entities.battle_match import BattleMatch
from domain.entities.invitation import Invitation

class StartBattleService:

    def start_battle(self, invitation: "Invitation") -> BattleMatch:
        """
        Create a BattleMatch once both parties are selected.
        """
        if not invitation.is_ready_for_battle():
            raise ValueError("Both parties must be selected before starting battle")

        return BattleMatch(
            player1_username=invitation.inviter.username,
            player2_username=invitation.invitee.username,
            player1_party=invitation.inviter_party,
            player2_party=invitation.invitee_party
        )