import logging
from pathlib import Path

from app.config import ROOT_DIR


def configure_logging() -> None:
    log_dir = ROOT_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "databurguer.log", encoding="utf-8"),
        ],
        force=False,
    )
