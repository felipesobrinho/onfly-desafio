"""Relatório consolidado, com valores exatos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Summary:
    """Totais gerais do relatório."""

    total_reservations: int
    confirmed_reservations: int
    cancelled_reservations: int
    no_show_reservations: int
    total_room_nights: int
    total_amount_brl: Decimal

    @property
    def average_nightly_rate_brl(self) -> Decimal:
        """Valor médio por noite de quarto; zero quando não há noites."""
        if self.total_room_nights == 0:
            return Decimal(0)
        return self.total_amount_brl / self.total_room_nights


@dataclass(frozen=True)
class MonthlyTotal:
    """Totais das reservas faturáveis de um mês de check-in."""

    month: str
    reservations: int
    room_nights: int
    total_brl: Decimal


@dataclass(frozen=True)
class HotelTotal:
    """Totais das reservas faturáveis de um hotel."""

    hotel_id: str
    hotel_name: str
    room_nights: int
    total_brl: Decimal


@dataclass(frozen=True)
class Report:
    """Resultado da consolidação."""

    generated_at: datetime
    summary: Summary
    by_month: tuple[MonthlyTotal, ...]
    top_hotels: tuple[HotelTotal, ...]
