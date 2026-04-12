from fastapi import APIRouter

router = APIRouter(prefix="/players", tags=["Players"])

controller = None


def init(ctrl):
    global controller
    controller = ctrl


@router.get("/{username}")
def get_player(username: str):
    return controller.get_player(username)


@router.get("/{username}/parties")
def get_parties(username: str):
    return controller.get_parties(username)