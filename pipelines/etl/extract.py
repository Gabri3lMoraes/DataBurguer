import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger("databurguer.etl.extract")


class ExtractionError(RuntimeError):
    pass


@dataclass
class ExtractedSource:
    name: str
    path: Path
    frame: pd.DataFrame
    total_records: int
    invalid_records: int
    processed_at: datetime


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ExtractionError(f"CSV inválido: {path}") from exc


def _read_json(path: Path) -> pd.DataFrame:
    try:
        return pd.read_json(path)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ExtractionError(f"JSON inválido: {path}") from exc


def extract_sources(raw_dir: Path) -> dict[str, ExtractedSource]:
    definitions = {
        "clientes": (raw_dir / "clientes.csv", _read_csv, ["cliente_id", "email"]),
        "pedidos": (raw_dir / "pedidos.csv", _read_csv, ["pedido_id", "cliente_id"]),
        "pagamentos": (
            raw_dir / "pagamentos.json",
            _read_json,
            ["pagamento_id", "pedido_id"],
        ),
    }
    extracted: dict[str, ExtractedSource] = {}
    for name, (path, reader, required) in definitions.items():
        if not path.exists():
            raise ExtractionError(f"Arquivo não encontrado: {path}")
        frame = reader(path)
        missing_columns = set(required) - set(frame.columns)
        if missing_columns:
            raise ExtractionError(f"Colunas ausentes em {path.name}: {sorted(missing_columns)}")
        invalid_mask = frame[list(required)].isna().any(axis=1)
        duplicate_mask = frame.duplicated(subset=[required[0]], keep="first")
        invalid = int((invalid_mask | duplicate_mask).sum())
        extracted[name] = ExtractedSource(
            name=name,
            path=path,
            frame=frame,
            total_records=len(frame),
            invalid_records=invalid,
            processed_at=datetime.now(),
        )
        logger.info(
            "Extraído %s: %s registros (%s inválidos)", path.name, len(frame), invalid
        )
    return extracted
