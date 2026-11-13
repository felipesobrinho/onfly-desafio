"""Reserva de hotel e as regras que dependem apenas dela."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class ReservationStatus(StrEnum):
    """Situações possíveis de uma reserva."""

    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

    @property
    def is_billable(self) -> bool:
        """Indica se a reserva entra em noites e valores."""
        return self is ReservationStatus.CONFIRMED


@dataclass(frozen=True)
class Reservation:
    """Reserva com os dados que o relatório utiliza."""

    reservation_id: str
    hotel_id: str
    hotel_name: str
    checkin: date
    checkout: date
    rooms: int
    status: ReservationStatus
    currency: str
    amount: Decimal

    def __post_init__(self) -> None:
        if self.rooms < 1:
            raise ValueError(f"quantidade de quartos inválida: {self.rooms}")
        if self.checkout < self.checkin:
            raise ValueError(f"check-out {self.checkout} anterior ao check-in {self.checkin}")
        if not self.amount.is_finite():
            raise ValueError(f"valor inválido: {self.amount}")

    @property
    def room_nights(self) -> int:
        """Noites de quarto: diferença de datas (não inclusiva) vezes quartos."""
        return (self.checkout - self.checkin).days * self.rooms

    @property
    def month(self) -> str:
        """Mês do check-in no formato YYYY-MM."""
        return self.checkin.strftime("%Y-%m")
