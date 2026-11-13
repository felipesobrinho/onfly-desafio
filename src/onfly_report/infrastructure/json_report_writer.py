"""Serialização do relatório para o JSON do contrato."""

from __future__ import annotations

import json
from datetime import timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from ..domain.report import Report

REPORT_VERSION = "1.0"
REPORT_TIMEZONE = timezone(timedelta(hours=-3))
MONEY_QUANTUM = Decimal("0.01")


def format_money(value: Decimal) -> str:
    """Serializa dinheiro com duas casas, arredondamento half-up."""
    return format(value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP), "f")


def report_to_dict(report: Report) -> dict:
    """Monta o documento com os nomes, tipos e formatos do contrato."""
    summary = report.summary
    return {
        "report_version": REPORT_VERSION,
        "generated_at": report.generated_at.astimezone(REPORT_TIMEZONE).isoformat(timespec="seconds"),
        "summary": {
            "total_reservations": summary.total_reservations,
            "confirmed_reservations": summary.confirmed_reservations,
            "cancelled_reservations": summary.cancelled_reservations,
            "no_show_reservations": summary.no_show_reservations,
            "total_room_nights": summary.total_room_nights,
            "total_amount_brl": format_money(summary.total_amount_brl),
            "average_nightly_rate_brl": format_money(summary.average_nightly_rate_brl),
        },
        "by_month": [
            {
                "month": month.month,
                "reservations": month.reservations,
                "room_nights": month.room_nights,
                "total_brl": format_money(month.total_brl),
            }
            for month in report.by_month
        ],
        "top_hotels": [
            {
                "hotel_id": hotel.hotel_id,
                "hotel_name": hotel.hotel_name,
                "room_nights": hotel.room_nights,
                "total_brl": format_money(hotel.total_brl),
            }
            for hotel in report.top_hotels
        ],
    }


class JsonReportWriter:
    """Grava o relatório em um arquivo JSON, criando o diretório se preciso."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def write(self, report: Report) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(report_to_dict(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
