"""Conversão de valores para BRL."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from ..exceptions import UnknownCurrencyError


class ExchangeRates:
    """Tabela de taxas de câmbio para BRL."""

    def __init__(self, rates_to_brl: Mapping[str, Decimal]) -> None:
        self._rates_to_brl = dict(rates_to_brl)

    def to_brl(self, amount: Decimal, currency: str) -> Decimal:
        """Converte o valor multiplicando pela taxa da moeda, sem arredondar."""
        try:
            rate = self._rates_to_brl[currency]
        except KeyError:
            raise UnknownCurrencyError(f"moeda sem taxa de câmbio: {currency}") from None
        return amount * rate
