"""Interface de linha de comando do consolidador."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .application.build_report import BuildReport
from .domain.report import Report
from .exceptions import DomainError
from .infrastructure.csv_rate_reader import CsvExchangeRateReader
from .infrastructure.csv_reservation_reader import CsvReservationReader
from .infrastructure.json_report_writer import JsonReportWriter, format_money
from .logging_config import configure_logging

logger = logging.getLogger("onfly_report")

EXIT_OK = 0
EXIT_UNEXPECTED_ERROR = 1
EXIT_INVALID_INPUT = 2


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"valor inteiro inválido: {value!r}") from None
    if number < 1:
        raise argparse.ArgumentTypeError("deve ser maior ou igual a 1")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="onfly_report",
        description="Consolida a exportação de reservas de hotel em um relatório JSON.",
    )
    parser.add_argument("--input", required=True, help="CSV de reservas")
    parser.add_argument("--rates", required=True, help="CSV de taxas de câmbio para BRL")
    parser.add_argument("--output", default="output/report.json", help="caminho do relatório JSON")
    parser.add_argument("--top", type=positive_int, default=5, help="quantidade de hotéis no ranking")
    return parser


def summary_line(report: Report) -> str:
    summary = report.summary
    return (
        f"Reservas: {summary.total_reservations} | Confirmadas: {summary.confirmed_reservations} | "
        f"Noites: {summary.total_room_nights} | Total BRL: {format_money(summary.total_amount_brl)}"
    )


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)

    build_report = BuildReport(
        reservations=CsvReservationReader(Path(args.input)),
        exchange_rates=CsvExchangeRateReader(Path(args.rates)),
        top_n=args.top,
    )
    writer = JsonReportWriter(Path(args.output))

    try:
        report = build_report.execute()
        writer.write(report)
    except DomainError as err:
        logger.error("entrada inválida: %s", err)
        return EXIT_INVALID_INPUT
    except Exception:
        logger.exception("erro inesperado ao gerar o relatório")
        return EXIT_UNEXPECTED_ERROR

    print(summary_line(report))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
