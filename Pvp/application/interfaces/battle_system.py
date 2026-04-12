# application/interfaces/battle_system.py

import random

class BattleSystemAPI:
    """
    Stub for communicating with external battle resolution service.
    """

    def resolve_battle(self, player1_party, player2_party):
        """
        Returns the winner username. Currently a random winner for demo.
        Replace with API call or gRPC request in production.
        """
        return random.choice([player1_party.owner_username, player2_party.owner_username])