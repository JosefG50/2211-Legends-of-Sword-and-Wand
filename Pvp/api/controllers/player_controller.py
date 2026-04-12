class PlayerController:
    def __init__(self, user_repo, party_repo):
        self.user_repo = user_repo
        self.party_repo = party_repo

    def get_parties(self, username: str):
        # This bridges the route to the repository method you just added
        return self.party_repo.get_by_user(username)