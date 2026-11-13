"""Testes adicionais: caso de uso com fontes em memória e serialização do resultado."""

from datetime import date, datetime, timezone
from decimal import Decimal

from onfly_report.application.build_report import BuildReport
from onfly_report.domain.exchange import ExchangeRates
from onfly_report.domain.reservation import Reservation, ReservationStatus
from onfly_report.infrastructure.json_report_writer import report_to_dict

NOON_UTC = datetime(2025, 7, 1, 13, 0, 0, tzinfo=timezone.utc)


class InMemoryReservations:
    def __init__(self, reservations):
        self._reservations = reservations

    def read(self):
        return self._reservations


class InMemoryRates:
    def read(self):
        return ExchangeRates({"BRL": Decimal("1"), "USD": Decimal("5.42")})


def reservation(reservation_id, hotel_id, amount, status=ReservationStatus.CONFIRMED, currency="BRL", nights=1):
    return Reservation(
        reservation_id=reservation_id,
        hotel_id=hotel_id,
        hotel_name=f"Hotel {hotel_id}",
        checkin=date(2025, 1, 10),
        checkout=date(2025, 1, 10 + nights),
        rooms=1,
        status=status,
        currency=currency,
        amount=Decimal(amount),
    )


def build(reservations, top_n=5):
    use_case = BuildReport(
        reservations=InMemoryReservations(reservations),
        exchange_rates=InMemoryRates(),
        top_n=top_n,
        clock=lambda: NOON_UTC,
    )
    return use_case.execute()


def test_use_case_counts_every_status_and_aggregates_only_confirmed():
    """A contagem considera todas as reservas; noites e valores, só as confirmadas."""
    report = build(
        [
            reservation("R-1", "H01", "100.00", nights=2),
            reservation("R-2", "H02", "10.00", currency="USD"),
            reservation("R-3", "H03", "999.00", status=ReservationStatus.CANCELLED),
            reservation("R-4", "H04", "999.00", status=ReservationStatus.NO_SHOW),
        ]
    )

    assert report.summary.total_reservations == 4
    assert report.summary.confirmed_reservations == 2
    assert report.summary.cancelled_reservations == 1
    assert report.summary.no_show_reservations == 1
    assert report.summary.total_room_nights == 3
    assert report.summary.total_amount_brl == Decimal("154.20")
    assert [hotel.hotel_id for hotel in report.top_hotels] == ["H01", "H02"]


def test_use_case_keeps_exact_values_until_serialization():
    """O relatório guarda o valor exato; as duas casas aparecem só no JSON."""
    report = build([reservation("R-1", "H01", "0.75", currency="USD")])

    assert report.summary.total_amount_brl == Decimal("4.0650")
    assert report_to_dict(report)["summary"]["total_amount_brl"] == "4.07"


def test_non_billable_reservation_in_unknown_currency_does_not_block_the_report():
    """Só o que é faturável precisa de taxa de câmbio."""
    report = build(
        [
            reservation("R-1", "H01", "100.00"),
            reservation("R-2", "H02", "50.00", status=ReservationStatus.CANCELLED, currency="GBP"),
        ]
    )

    assert report.summary.total_amount_brl == Decimal("100.00")


def test_top_n_limits_the_ranking():
    """O ranking respeita o limite pedido."""
    report = build(
        [
            reservation("R-1", "H01", "300.00"),
            reservation("R-2", "H02", "200.00"),
            reservation("R-3", "H03", "100.00"),
        ],
        top_n=2,
    )

    assert [hotel.hotel_id for hotel in report.top_hotels] == ["H01", "H02"]


def test_generated_at_is_serialized_with_fixed_offset():
    """generated_at sai sempre em -03:00, qualquer que seja o fuso do relógio."""
    document = report_to_dict(build([]))

    assert document["generated_at"] == "2025-07-01T10:00:00-03:00"
