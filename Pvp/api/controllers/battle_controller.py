class BattleController:

    def __init__(self, start_battle_service, update_league_service):
        self.start_battle_service = start_battle_service
        self.update_league_service = update_league_service

    def start_battle(self, player1: str, player2: str):
        result = self.start_battle_service.start(player1, player2)
        self.update_league_service.update(result)
        return result