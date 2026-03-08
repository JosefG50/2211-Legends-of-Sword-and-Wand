from enum import Enum


class InvitationStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    READY = "ready"

from dataclasses import dataclass
from typing import Optional
from domain.entities.user import User
from domain.entities.party import Party


@dataclass
class Invitation:
    inviter: User
    invitee: User

    status: InvitationStatus = InvitationStatus.PENDING

    inviter_party: Optional[Party] = None
    invitee_party: Optional[Party] = None

    def accept(self):
        if self.status != InvitationStatus.PENDING:
            raise ValueError("Invitation cannot be accepted")

        if not self.inviter.has_parties():
            raise ValueError("Inviter has no saved parties")

        if not self.invitee.has_parties():
            raise ValueError("Invitee has no saved parties")

        self.status = InvitationStatus.ACCEPTED

    def decline(self):
        if self.status != InvitationStatus.PENDING:
            raise ValueError("Invitation cannot be declined")

        self.status = InvitationStatus.DECLINED

    def select_party(self, username: str, party: Party):
        if self.status != InvitationStatus.ACCEPTED:
            raise ValueError("Parties can only be selected after acceptance")

        if username == self.inviter.username:
            if party.owner_username != username:
                raise ValueError("Party does not belong to inviter")

            self.inviter_party = party

        elif username == self.invitee.username:
            if party.owner_username != username:
                raise ValueError("Party does not belong to invitee")

            self.invitee_party = party

        else:
            raise ValueError("User not part of this invitation")

        self._check_ready()

    def _check_ready(self):
        if self.inviter_party and self.invitee_party:
            self.status = InvitationStatus.READY

    def is_ready_for_battle(self) -> bool:
        return self.status == InvitationStatus.READY