"""Testes adicionais: amostra de validação do README e dataset completo."""

import json

from helpers import PROJECT_ROOT

from onfly_report.cli import main

DATA_DIR = PROJECT_ROOT / "data"


def generate(tmp_path, input_name, top=5):
    output_path = tmp_path / "report.json"
    exit_code = main(
        [
            "--input",
            str(DATA_DIR / input_name),
            "--rates",
            str(DATA_DIR / "taxas_cambio.csv"),
            "--output",
            str(output_path),
            "--top",
            str(top),
        ]
    )
    assert exit_code == 0
    return json.loads(output_path.read_text(encoding="utf-8"))


def test_validation_sample_matches_the_readme(tmp_path):
    """A amostra reproduz as três tabelas publicadas no README."""
    report = generate(tmp_path, "exemplo-validacao.csv")

    assert report["summary"] == {
        "total_reservations": 12,
        "confirmed_reservations": 9,
        "cancelled_reservations": 2,
        "no_show_reservations": 1,
        "total_room_nights": 28,
        "total_amount_brl": "7566.00",
        "average_nightly_rate_brl": "270.21",
    }
    assert report["by_month"] == [
        {"month": "2025-01", "reservations": 8, "room_nights": 25, "total_brl": "6684.00"},
        {"month": "2025-02", "reservations": 1, "room_nights": 3, "total_brl": "882.00"},
    ]
    assert report["top_hotels"] == [
        {"hotel_id": "H01", "hotel_name": "Hotel Aurora Paulista", "room_nights": 3, "total_brl": "1200.00"},
        {"hotel_id": "H02", "hotel_name": "Hotel Mirante", "room_nights": 2, "total_brl": "1084.00"},
        {"hotel_id": "H12", "hotel_name": "Hotel Miami Beach", "room_nights": 1, "total_brl": "1000.00"},
        {"hotel_id": "H10", "hotel_name": "Hotel Madrid, Gran Vía", "room_nights": 4, "total_brl": "900.00"},
        {"hotel_id": "H09", "hotel_name": "Hotel Lisboa, Centro", "room_nights": 3, "total_brl": "882.00"},
    ]


def test_full_dataset_is_consolidated_entirely(tmp_path):
    """As 300 reservas do dataset entram no relatório e os meses fecham com o resumo."""
    report = generate(tmp_path, "reservas_hoteis.csv", top=12)
    summary = report["summary"]

    assert summary == {
        "total_reservations": 300,
        "confirmed_reservations": 235,
        "cancelled_reservations": 31,
        "no_show_reservations": 34,
        "total_room_nights": 1347,
        "total_amount_brl": "396170.00",
        "average_nightly_rate_brl": "294.11",
    }
    assert sum(month["reservations"] for month in report["by_month"]) == summary["confirmed_reservations"]
    assert sum(month["room_nights"] for month in report["by_month"]) == summary["total_room_nights"]
    assert sum(hotel["room_nights"] for hotel in report["top_hotels"]) == summary["total_room_nights"]
    assert [month["month"] for month in report["by_month"]] == sorted(month["month"] for month in report["by_month"])
