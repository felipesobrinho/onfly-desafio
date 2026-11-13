"""Testes adicionais: regras de negócio que os testes fornecidos não cobrem."""

from helpers import run_cli


def test_reads_every_reservation_of_a_large_file(tmp_path):
    """O arquivo é lido por inteiro, sem limite de linhas."""
    rows = [{"reservation_id": f"R-{index}"} for index in range(250)]

    report = run_cli(tmp_path, rows)

    assert report["summary"]["total_reservations"] == 250
    assert report["summary"]["confirmed_reservations"] == 250
    assert report["summary"]["total_room_nights"] == 250
    assert report["summary"]["total_amount_brl"] == "25000.00"


def test_nights_across_year_boundary_multiply_by_rooms(tmp_path):
    """A virada de ano conta as noites reais, multiplicadas pelos quartos."""
    report = run_cli(
        tmp_path,
        [{"checkin_date": "2024-12-30", "checkout_date": "2025-01-02", "rooms": "2"}],
    )

    assert report["summary"]["total_room_nights"] == 6


def test_money_is_summed_exactly_and_rounded_once(tmp_path):
    """Duas parcelas de 1.355 somam 2.71; arredondar cada uma daria 2.72."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "currency": "USD", "amount": "0.25"},
            {"reservation_id": "R-2", "currency": "USD", "amount": "0.25"},
        ],
    )

    assert report["summary"]["total_amount_brl"] == "2.71"


def test_money_rounds_half_up(tmp_path):
    """4.065 vira 4.07; half-even ou float dariam 4.06."""
    report = run_cli(tmp_path, [{"currency": "USD", "amount": "0.75"}])

    assert report["summary"]["total_amount_brl"] == "4.07"
    assert report["summary"]["average_nightly_rate_brl"] == "4.07"


def test_average_is_zero_without_billable_nights(tmp_path):
    """Sem reservas confirmadas não há noites, valores, meses nem ranking."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "status": "CANCELLED"},
            {"reservation_id": "R-2", "status": "NO_SHOW"},
        ],
    )

    assert report["summary"]["total_reservations"] == 2
    assert report["summary"]["total_room_nights"] == 0
    assert report["summary"]["total_amount_brl"] == "0.00"
    assert report["summary"]["average_nightly_rate_brl"] == "0.00"
    assert report["by_month"] == []
    assert report["top_hotels"] == []


def test_by_month_uses_checkin_month_in_ascending_order(tmp_path):
    """O mês é o do check-in, em ordem crescente, só com reservas confirmadas."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "checkin_date": "2025-02-10", "checkout_date": "2025-02-12"},
            {"reservation_id": "R-2", "checkin_date": "2025-01-30", "checkout_date": "2025-02-02"},
            {"reservation_id": "R-3", "checkin_date": "2024-12-31", "checkout_date": "2025-01-01"},
            {"reservation_id": "R-4", "checkin_date": "2025-03-01", "checkout_date": "2025-03-02", "status": "NO_SHOW"},
        ],
    )

    assert report["by_month"] == [
        {"month": "2024-12", "reservations": 1, "room_nights": 1, "total_brl": "100.00"},
        {"month": "2025-01", "reservations": 1, "room_nights": 3, "total_brl": "100.00"},
        {"month": "2025-02", "reservations": 1, "room_nights": 2, "total_brl": "100.00"},
    ]


def test_top_hotels_tie_is_broken_by_hotel_id(tmp_path):
    """Hotéis com o mesmo total aparecem por hotel_id crescente."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H03", "hotel_name": "Hotel C", "amount": "500.00"},
            {"reservation_id": "R-2", "hotel_id": "H01", "hotel_name": "Hotel A", "amount": "500.00"},
            {"reservation_id": "R-3", "hotel_id": "H02", "hotel_name": "Hotel B", "amount": "900.00"},
        ],
    )

    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H02", "H01", "H03"]


def test_top_hotels_aggregates_reservations_of_the_same_hotel(tmp_path):
    """Reservas do mesmo hotel somam noites e valores; as não faturáveis ficam de fora."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H01", "hotel_name": "Hotel A", "amount": "300.00"},
            {"reservation_id": "R-2", "hotel_id": "H01", "hotel_name": "Hotel A", "currency": "EUR"},
            {"reservation_id": "R-3", "hotel_id": "H01", "hotel_name": "Hotel A", "status": "CANCELLED"},
            {"reservation_id": "R-4", "hotel_id": "H02", "hotel_name": "Hotel B", "status": "NO_SHOW"},
        ],
    )

    assert report["top_hotels"] == [
        {"hotel_id": "H01", "hotel_name": "Hotel A", "room_nights": 2, "total_brl": "888.00"},
    ]


def test_top_hotels_returns_fewer_items_when_there_are_fewer_hotels(tmp_path):
    """Com menos hotéis do que --top, o ranking traz todos os que existem."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H01"},
            {"reservation_id": "R-2", "hotel_id": "H02"},
        ],
        top=5,
    )

    assert len(report["top_hotels"]) == 2
