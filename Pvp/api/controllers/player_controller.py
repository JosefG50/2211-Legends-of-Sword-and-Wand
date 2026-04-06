class PlayerController:

    def __init__(self, user_repo, party_repo):
        self.user_repo = user_repo
        self.party_repo = party_repo

    def get_player(self, username: str):
        return self.user_repo.get(username)

    def get_parties(self, username: str):
        return self.party_repo.get_by_user(username)