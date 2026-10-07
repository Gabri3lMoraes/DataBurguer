import argparse
import csv
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path

from app.config import ROOT_DIR

logger = logging.getLogger("databurguer.logs.generate")

URLS = ["/", "/cardapio", "/produtos", "/promocoes", "/carrinho", "/checkout", "/pedido"]
CITIES = ["Recife", "Olinda", "Paulista", "Jaboatão dos Guararapes"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125",
    "Mozilla/5.0 (Linux; Android 14) Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5) Mobile/15E148 Safari/604.1",
    "DataBurguerApp/1.0",
]
STATUSES = [200] * 82 + [201] * 5 + [304] * 4 + [400] * 2 + [404] * 5 + [500] * 2


def generate_logs(rows: int = 10_000, output_path: Path | None = None, seed: int = 42) -> Path:
    if rows <= 0:
        raise ValueError("A quantidade de logs deve ser maior que zero")
    path = output_path or ROOT_DIR / "data" / "raw" / "access_logs.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    random.seed(seed)
    now = datetime.now().replace(microsecond=0)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["timestamp", "ip", "url", "status_http", "user_agent", "cidade", "estado"],
        )
        writer.writeheader()
        for _ in range(rows):
            timestamp = now - timedelta(seconds=random.randint(0, 3 * 24 * 3600 - 1))
            writer.writerow(
                {
                    "timestamp": timestamp.isoformat(),
                    "ip": ".".join(str(random.randint(1, 254)) for _ in range(4)),
                    "url": random.choice(URLS),
                    "status_http": random.choice(STATUSES),
                    "user_agent": random.choice(USER_AGENTS),
                    "cidade": random.choices(CITIES, weights=[40, 30, 18, 12], k=1)[0],
                    "estado": "PE",
                }
            )
    logger.info("Gerados %s logs em %s", rows, path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera logs sintéticos do DataBurguer")
    parser.add_argument("--rows", type=int, default=10_000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    generate_logs(args.rows, args.output)


if __name__ == "__main__":
    main()
