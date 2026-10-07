import argparse
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.logging_config import configure_logging  # noqa: E402
from pipelines.etl.pipeline import run_pipeline  # noqa: E402
from pipelines.logs.generate_logs import generate_logs  # noqa: E402
from pipelines.logs.spark_job import run_log_pipeline  # noqa: E402
from scripts.generate_source_data import generate_source_data  # noqa: E402
from scripts.seed_database import seed_database  # noqa: E402

logger = logging.getLogger("databurguer.run_all")


def run_all(log_rows: int = 10_000, log_engine: str = "auto") -> dict:
    started = time.perf_counter()
    for directory in [
        ROOT / "data" / "raw",
        ROOT / "data" / "processed",
        ROOT / "data" / "curated",
        ROOT / "logs",
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    logger.info("1/5 Criando tabelas e dados operacionais")
    seed = seed_database()
    logger.info("2/5 Gerando fontes CSV e JSON")
    sources = generate_source_data()
    logger.info("3/5 Executando ETL")
    etl = run_pipeline()
    logger.info("4/5 Gerando %s logs", log_rows)
    log_path = generate_logs(log_rows)
    logger.info("5/5 Processando logs")
    logs = run_log_pipeline(log_path, engine=log_engine)
    result = {
        "seed": seed,
        "source_files": {key: str(value) for key, value in sources.items()},
        "etl": etl,
        "logs": logs,
        "duration_seconds": round(time.perf_counter() - started, 3),
    }
    logger.info("MVP preparado com sucesso em %ss", result["duration_seconds"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara todo o MVP DataBurguer")
    parser.add_argument("--log-rows", type=int, default=10_000)
    parser.add_argument("--log-engine", choices=["auto", "spark", "pandas"], default="auto")
    args = parser.parse_args()
    configure_logging()
    result = run_all(args.log_rows, args.log_engine)
    print("\nResumo da execução")
    print(f"- Clientes: {result['seed']['clientes']}")
    print(f"- Pedidos: {result['seed']['pedidos']}")
    print(f"- Linhas analíticas: {result['etl']['analytics_rows']}")
    print(f"- Logs: {result['logs']['total_acessos']} ({result['logs']['engine']})")
    print(f"- Duração: {result['duration_seconds']}s")


if __name__ == "__main__":
    main()
