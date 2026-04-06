from fastapi import APIRouter

router = APIRouter(prefix="/battle", tags=["Battle"])

controller = None


def init(ctrl):
    global controller
    controller = ctrl


@router.post("/start")
def start_battle(player1: str, player2: str):
    return controller.start_battle(player1, player2)