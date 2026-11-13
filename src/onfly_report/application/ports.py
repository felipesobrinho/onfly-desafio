"""Portas de entrada de dados do caso de uso."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ..domain.exchange import ExchangeRates
from ..domain.reservation import Reservation


class ReservationReader(Protocol):
    """Fonte das reservas já convertidas para os tipos do domínio."""

    def read(self) -> Sequence[Reservation]: ...


class ExchangeRateReader(Protocol):
    """Fonte da tabela de câmbio."""

    def read(self) -> ExchangeRates: ...
