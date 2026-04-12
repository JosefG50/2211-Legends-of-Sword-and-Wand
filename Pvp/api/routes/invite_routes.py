from fastapi import APIRouter

router = APIRouter(prefix="/invites", tags=["Invites"])

controller = None


def init(ctrl):
    global controller
    controller = ctrl


class InviteRequest:
    def __init__(self, inviter: str, invitee: str):
        self.inviter = inviter
        self.invitee = invitee


@router.post("")
def send_invite(inviter: str, invitee: str):
    return controller.send_invite(inviter, invitee)


@router.post("/{invite_id}/accept")
def accept_invite(invite_id: int):
    return controller.accept_invite(invite_id)


@router.post("/{invite_id}/decline")
def decline_invite(invite_id: int):
    return controller.decline_invite(invite_id)