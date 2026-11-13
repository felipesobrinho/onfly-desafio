"""Leitura da exportação de reservas em CSV."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..domain.reservation import Reservation, ReservationStatus
from ..exceptions import InputFileError
from .csv_source import CsvRow, read_csv

REQUIRED_COLUMNS = (
    "reservation_id",
    "traveler_name",
    "company_id",
    "hotel_id",
    "hotel_name",
    "city",
    "country",
    "checkin_date",
    "checkout_date",
    "rooms",
    "status",
    "currency",
    "amount",
    "payment_method",
    "booked_at",
)


class CsvReservationReader:
    """Lê as reservas do CSV e as converte para os tipos do domínio."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> list[Reservation]:
        return [self._to_reservation(row) for row in read_csv(self._path, REQUIRED_COLUMNS)]

    def _to_reservation(self, row: CsvRow) -> Reservation:
        try:
            return Reservation(
                reservation_id=row.text("reservation_id"),
                hotel_id=row.text("hotel_id"),
                hotel_name=row.text("hotel_name"),
                checkin=date.fromisoformat(row.text("checkin_date")),
                checkout=date.fromisoformat(row.text("checkout_date")),
                rooms=int(row.text("rooms")),
                status=ReservationStatus(row.text("status")),
                currency=row.text("currency").upper(),
                amount=Decimal(row.text("amount")),
            )
        except (ValueError, InvalidOperation) as err:
            raise InputFileError(f"linha {row.line_number} inválida em {self._path}: {err}") from err
