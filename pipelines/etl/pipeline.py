import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, create_tables  # noqa: E402
from app.logging_config import configure_logging  # noqa: E402
from pipelines.etl.extract import extract_sources  # noqa: E402
from pipelines.etl.load import load_results  # noqa: E402
from pipelines.etl.transform import transform_sources  # noqa: E402

logger = logging.getLogger("databurguer.etl")


def run_pipeline(raw_dir: Path | None = None, curated_dir: Path | None = None) -> dict:
    started = time.perf_counter()
    raw = raw_dir or ROOT / "data" / "raw"
    curated = curated_dir or ROOT / "data" / "curated"
    logger.info("Início do ETL")
    create_tables()
    sources = extract_sources(raw)
    transformed = transform_sources(sources)
    with SessionLocal() as db:
        result = load_results(db, transformed, sources, curated)
    result["duration_seconds"] = round(time.perf_counter() - started, 3)
    result["rejected_records"] = sum(item.invalid_records for item in sources.values())
    logger.info("Fim do ETL: %s", result)
    return result


if __name__ == "__main__":
    configure_logging()
    run_pipeline()
