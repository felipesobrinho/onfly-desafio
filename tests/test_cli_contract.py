"""Testes adicionais: contrato do CLI (argumentos, códigos de saída e formato)."""

import json
import re

import pytest

from onfly_report.cli import main

HEADER = (
    "reservation_id,traveler_name,company_id,hotel_id,hotel_name,city,country,"
    "checkin_date,checkout_date,rooms,status,currency,amount,payment_method,booked_at\n"
)
ROW = (
    "R-1,Pessoa Teste,EMP-001,H01,Hotel Teste,Sao Paulo,BR,{checkin},{checkout},{rooms},"
    "{status},{currency},{amount},PIX,2025-01-01T10:00:00-03:00\n"
)
RATES = "currency,rate_to_brl\nBRL,1.000000\nUSD,5.420000\n"


def write_inputs(tmp_path, reservations=None, rates=RATES, **fields):
    values = {
        "checkin": "2025-01-10",
        "checkout": "2025-01-12",
        "rooms": "1",
        "status": "CONFIRMED",
        "currency": "USD",
        "amount": "100.00",
        **fields,
    }
    input_path = tmp_path / "reservas.csv"
    rates_path = tmp_path / "rates.csv"
    input_path.write_text(reservations if reservations is not None else HEADER + ROW.format(**values), encoding="utf-8")
    rates_path.write_text(rates, encoding="utf-8")
    return ["--input", str(input_path), "--rates", str(rates_path)]


def test_report_follows_the_documented_format(tmp_path, capsys):
    """O JSON tem exatamente os campos, tipos e formatos do contrato."""
    output_path = tmp_path / "saida" / "report.json"

    exit_code = main([*write_inputs(tmp_path), "--output", str(output_path)])

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert list(report) == ["report_version", "generated_at", "summary", "by_month", "top_hotels"]
    assert report["report_version"] == "1.0"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-03:00", report["generated_at"])
    assert report["summary"] == {
        "total_reservations": 1,
        "confirmed_reservations": 1,
        "cancelled_reservations": 0,
        "no_show_reservations": 0,
        "total_room_nights": 2,
        "total_amount_brl": "542.00",
        "average_nightly_rate_brl": "271.00",
    }
    assert report["by_month"] == [{"month": "2025-01", "reservations": 1, "room_nights": 2, "total_brl": "542.00"}]
    assert report["top_hotels"] == [
        {"hotel_id": "H01", "hotel_name": "Hotel Teste", "room_nights": 2, "total_brl": "542.00"}
    ]
    assert "Reservas: 1" in capsys.readouterr().out


def test_output_defaults_to_output_report_json(tmp_path, monkeypatch):
    """Sem --output, o relatório vai para output/report.json e o diretório é criado."""
    monkeypatch.chdir(tmp_path)

    exit_code = main(write_inputs(tmp_path))

    assert exit_code == 0
    assert (tmp_path / "output" / "report.json").is_file()


def test_missing_input_file_exits_with_2(tmp_path):
    """Arquivo de reservas inexistente é entrada inválida."""
    arguments = write_inputs(tmp_path)
    arguments[1] = str(tmp_path / "nao-existe.csv")

    assert main([*arguments, "--output", str(tmp_path / "report.json")]) == 2
    assert not (tmp_path / "report.json").exists()


def test_missing_rates_file_exits_with_2(tmp_path):
    """Tabela de câmbio inexistente é entrada inválida."""
    arguments = write_inputs(tmp_path)
    arguments[3] = str(tmp_path / "nao-existe.csv")

    assert main([*arguments, "--output", str(tmp_path / "report.json")]) == 2


def test_missing_column_exits_with_2(tmp_path):
    """CSV sem uma coluna obrigatória é entrada inválida."""
    arguments = write_inputs(tmp_path, reservations="reservation_id,hotel_id\nR-1,H01\n")

    assert main([*arguments, "--output", str(tmp_path / "report.json")]) == 2


@pytest.mark.parametrize(
    "fields",
    [
        {"checkin": "10/01/2025"},
        {"rooms": "dois"},
        {"amount": "cem"},
    ],
)
def test_malformed_value_exits_with_2(tmp_path, fields):
    """Data, quartos ou valor fora do formato são entrada inválida."""
    arguments = write_inputs(tmp_path, **fields)

    assert main([*arguments, "--output", str(tmp_path / "report.json")]) == 2


@pytest.mark.parametrize("top", ["0", "-1", "abc"])
def test_invalid_top_exits_with_2(tmp_path, top):
    """--top precisa ser um inteiro maior ou igual a 1."""
    with pytest.raises(SystemExit) as raised:
        main([*write_inputs(tmp_path), "--top", top])

    assert raised.value.code == 2


def test_missing_required_argument_exits_with_2():
    """--input e --rates são obrigatórios."""
    with pytest.raises(SystemExit) as raised:
        main(["--input", "reservas.csv"])

    assert raised.value.code == 2
