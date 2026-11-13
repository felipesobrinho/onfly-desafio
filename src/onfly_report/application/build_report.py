"""Caso de uso: consolidar as reservas em um relatório."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from ..domain.exchange import ExchangeRates
from ..domain.report import HotelTotal, MonthlyTotal, Report, Summary
from ..domain.reservation import Reservation, ReservationStatus
from .ports import ExchangeRateReader, ReservationReader

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class BillableStay:
    """Reserva faturável com noites calculadas e valor convertido para BRL."""

    hotel_id: str
    hotel_name: str
    month: str
    room_nights: int
    amount_brl: Decimal

    @classmethod
    def from_reservation(cls, reservation: Reservation, rates: ExchangeRates) -> BillableStay:
        return cls(
            hotel_id=reservation.hotel_id,
            hotel_name=reservation.hotel_name,
            month=reservation.month,
            room_nights=reservation.room_nights,
            amount_brl=rates.to_brl(reservation.amount, reservation.currency),
        )


class BuildReport:
    """Lê as reservas, conta os status, filtra as faturáveis e agrega."""

    def __init__(
        self,
        reservations: ReservationReader,
        exchange_rates: ExchangeRateReader,
        top_n: int = 5,
        clock: Clock = utc_now,
    ) -> None:
        self._reservations = reservations
        self._exchange_rates = exchange_rates
        self._top_n = top_n
        self._clock = clock

    def execute(self) -> Report:
        reservations = self._reservations.read()
        rates = self._exchange_rates.read()

        status_counts = Counter(reservation.status for reservation in reservations)
        stays = [
            BillableStay.from_reservation(reservation, rates)
            for reservation in reservations
            if reservation.status.is_billable
        ]

        return Report(
            generated_at=self._clock(),
            summary=Summary(
                total_reservations=len(reservations),
                confirmed_reservations=status_counts[ReservationStatus.CONFIRMED],
                cancelled_reservations=status_counts[ReservationStatus.CANCELLED],
                no_show_reservations=status_counts[ReservationStatus.NO_SHOW],
                total_room_nights=total_room_nights(stays),
                total_amount_brl=total_amount_brl(stays),
            ),
            by_month=totals_by_month(stays),
            top_hotels=top_hotels(stays, self._top_n),
        )


def total_room_nights(stays: Iterable[BillableStay]) -> int:
    return sum(stay.room_nights for stay in stays)


def total_amount_brl(stays: Iterable[BillableStay]) -> Decimal:
    return sum((stay.amount_brl for stay in stays), Decimal(0))


def group_by(stays: Iterable[BillableStay], key: Callable[[BillableStay], str]) -> dict[str, list[BillableStay]]:
    groups: dict[str, list[BillableStay]] = defaultdict(list)
    for stay in stays:
        groups[key(stay)].append(stay)
    return groups


def totals_by_month(stays: Sequence[BillableStay]) -> tuple[MonthlyTotal, ...]:
    """Totais por mês de check-in, em ordem crescente de mês."""
    months = group_by(stays, lambda stay: stay.month)
    return tuple(
        MonthlyTotal(
            month=month,
            reservations=len(month_stays),
            room_nights=total_room_nights(month_stays),
            total_brl=total_amount_brl(month_stays),
        )
        for month, month_stays in sorted(months.items())
    )


def top_hotels(stays: Sequence[BillableStay], limit: int) -> tuple[HotelTotal, ...]:
    """Hotéis de maior valor primeiro; empate decidido pelo hotel_id crescente."""
    hotels = group_by(stays, lambda stay: stay.hotel_id)
    totals = [
        HotelTotal(
            hotel_id=hotel_id,
            hotel_name=hotel_stays[-1].hotel_name,
            room_nights=total_room_nights(hotel_stays),
            total_brl=total_amount_brl(hotel_stays),
        )
        for hotel_id, hotel_stays in hotels.items()
    ]
    ranked = sorted(totals, key=lambda hotel: (-hotel.total_brl, hotel.hotel_id))
    return tuple(ranked[:limit])
