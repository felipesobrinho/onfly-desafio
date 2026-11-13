"""Testes adicionais: regras do domínio isoladas de CSV, JSON e CLI."""

from datetime import date
from decimal import Decimal

import pytest

from onfly_report.domain.exchange import ExchangeRates
from onfly_report.domain.report import Summary
from onfly_report.domain.reservation import Reservation, ReservationStatus
from onfly_report.exceptions import UnknownCurrencyError


def make_reservation(**overrides):
    values = {
        "reservation_id": "R-1",
        "hotel_id": "H01",
        "hotel_name": "Hotel Teste",
        "checkin": date(2025, 1, 10),
        "checkout": date(2025, 1, 11),
        "rooms": 1,
        "status": ReservationStatus.CONFIRMED,
        "currency": "BRL",
        "amount": Decimal("100.00"),
        **overrides,
    }
    return Reservation(**values)


@pytest.mark.parametrize(
    ("status", "billable"),
    [
        (ReservationStatus.CONFIRMED, True),
        (ReservationStatus.CANCELLED, False),
        (ReservationStatus.NO_SHOW, False),
    ],
)
def test_only_confirmed_is_billable(status, billable):
    """Só CONFIRMED é faturável."""
    assert status.is_billable is billable


@pytest.mark.parametrize(
    ("checkin", "checkout", "rooms", "expected"),
    [
        (date(2025, 1, 10), date(2025, 1, 13), 1, 3),
        (date(2025, 1, 30), date(2025, 2, 2), 1, 3),
        (date(2024, 12, 30), date(2025, 1, 2), 2, 6),
        (date(2024, 2, 28), date(2024, 3, 1), 1, 2),
        (date(2025, 1, 10), date(2025, 1, 10), 3, 0),
    ],
)
def test_room_nights_use_the_date_difference(checkin, checkout, rooms, expected):
    """A diferença é não inclusiva e vale em viradas de mês, de ano e em ano bissexto."""
    reservation = make_reservation(checkin=checkin, checkout=checkout, rooms=rooms)

    assert reservation.room_nights == expected


def test_month_is_the_checkin_month():
    """O mês da reserva é o do check-in."""
    reservation = make_reservation(checkin=date(2025, 1, 30), checkout=date(2025, 2, 2))

    assert reservation.month == "2025-01"


@pytest.mark.parametrize(
    "overrides",
    [
        {"rooms": 0},
        {"checkin": date(2025, 1, 10), "checkout": date(2025, 1, 9)},
        {"amount": Decimal("NaN")},
    ],
)
def test_inconsistent_reservation_is_rejected(overrides):
    """Quartos, datas ou valor inconsistentes não formam uma reserva."""
    with pytest.raises(ValueError):
        make_reservation(**overrides)


def test_conversion_multiplies_by_the_rate_without_rounding():
    """A conversão é exata; o arredondamento fica para a serialização."""
    rates = ExchangeRates({"USD": Decimal("5.420000")})

    assert rates.to_brl(Decimal("0.75"), "USD") == Decimal("4.065")


def test_conversion_of_unknown_currency_fails():
    """Moeda sem taxa é erro de domínio."""
    rates = ExchangeRates({"BRL": Decimal("1")})

    with pytest.raises(UnknownCurrencyError):
        rates.to_brl(Decimal("10.00"), "GBP")


def test_average_nightly_rate_is_zero_without_nights():
    """Sem noites, a média é zero em vez de divisão por zero."""
    summary = Summary(
        total_reservations=1,
        confirmed_reservations=0,
        cancelled_reservations=1,
        no_show_reservations=0,
        total_room_nights=0,
        total_amount_brl=Decimal(0),
    )

    assert summary.average_nightly_rate_brl == Decimal(0)
