"""Leitura da tabela de câmbio para BRL em CSV."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..domain.exchange import ExchangeRates
from ..exceptions import InputFileError
from .csv_source import CsvRow, read_csv

REQUIRED_COLUMNS = ("currency", "rate_to_brl")


class CsvExchangeRateReader:
    """Carrega as taxas moeda -> BRL a partir de um CSV."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> ExchangeRates:
        rates = dict(self._to_rate(row) for row in read_csv(self._path, REQUIRED_COLUMNS))
        if not rates:
            raise InputFileError(f"tabela de câmbio vazia: {self._path}")
        return ExchangeRates(rates)

    def _to_rate(self, row: CsvRow) -> tuple[str, Decimal]:
        currency = row.text("currency").upper()
        raw_rate = row.text("rate_to_brl")
        if not currency or not raw_rate:
            raise InputFileError(f"linha {row.line_number} de câmbio incompleta em {self._path}")
        try:
            rate = Decimal(raw_rate)
        except InvalidOperation as err:
            raise InputFileError(f"taxa inválida para {currency} em {self._path}") from err
        if not rate.is_finite() or rate <= 0:
            raise InputFileError(f"taxa não positiva para {currency} em {self._path}")
        return currency, rate
