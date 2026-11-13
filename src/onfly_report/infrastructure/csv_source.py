"""Leitura de arquivos CSV com cabeçalho."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..exceptions import InputFileError


@dataclass(frozen=True)
class CsvRow:
    """Linha crua do CSV, com o número da linha física no arquivo."""

    line_number: int
    values: dict[str, str]

    def text(self, column: str) -> str:
        """Valor da coluna sem espaços nas pontas; vazio quando ausente."""
        return (self.values.get(column) or "").strip()


def read_csv(path: Path, required_columns: Sequence[str]) -> list[CsvRow]:
    """Lê todas as linhas do CSV, exigindo as colunas obrigatórias no cabeçalho."""
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            header = reader.fieldnames or []
            missing = [column for column in required_columns if column not in header]
            if missing:
                raise InputFileError(f"colunas obrigatórias ausentes em {path}: {', '.join(missing)}")
            return [CsvRow(line_number=reader.line_num, values=values) for values in reader]
    except FileNotFoundError as err:
        raise InputFileError(f"arquivo não encontrado: {path}") from err
    except (OSError, UnicodeDecodeError, csv.Error) as err:
        raise InputFileError(f"falha ao ler {path}: {err}") from err
