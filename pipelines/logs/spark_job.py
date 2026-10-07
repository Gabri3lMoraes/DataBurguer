import argparse
import json
import logging
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app.database import SessionLocal, create_tables  # noqa: E402
from app.logging_config import configure_logging  # noqa: E402
from app.models import (  # noqa: E402
    AnalyticsLogCidade,
    AnalyticsLogHora,
    AnalyticsLogPagina,
    AnalyticsLogStatus,
)
from pipelines.logs.aggregate import aggregate_logs_pandas  # noqa: E402

logger = logging.getLogger("databurguer.logs.spark")


def _write_partitioned_pandas(frame: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for partition, group in frame.groupby("data"):
        partition_dir = output_dir / f"data={partition}"
        if partition_dir.exists():
            shutil.rmtree(partition_dir)
        partition_dir.mkdir(parents=True)
        group.drop(columns=["data"]).to_parquet(partition_dir / "part-00000.parquet", index=False)


def _save_aggregates(aggregates: dict, curated_dir: Path) -> None:
    aggregate_dir = curated_dir / "log_aggregates"
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    for name in ["cidade", "estado", "pagina", "hora", "data", "status"]:
        aggregates[name].to_parquet(aggregate_dir / f"{name}.parquet", index=False)
    (aggregate_dir / "resumo.json").write_text(
        json.dumps(aggregates["resumo"], ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_database(aggregates: dict) -> None:
    create_tables()
    with SessionLocal() as db:
        with db.begin():
            for model in [
                AnalyticsLogCidade,
                AnalyticsLogPagina,
                AnalyticsLogHora,
                AnalyticsLogStatus,
            ]:
                db.execute(delete(model))
            db.add_all(AnalyticsLogCidade(**row) for row in aggregates["cidade"].to_dict("records"))
            db.add_all(AnalyticsLogPagina(**row) for row in aggregates["pagina"].to_dict("records"))
            db.add_all(AnalyticsLogHora(**row) for row in aggregates["hora"].to_dict("records"))
            db.add_all(AnalyticsLogStatus(**row) for row in aggregates["status"].to_dict("records"))


def _run_pandas(input_path: Path, processed_dir: Path, curated_dir: Path) -> dict:
    frame = pd.read_csv(input_path)
    aggregates = aggregate_logs_pandas(frame)
    _write_partitioned_pandas(aggregates["clean"], processed_dir)
    _save_aggregates(aggregates, curated_dir)
    _load_database(aggregates)
    return {"engine": "pandas-fallback", **aggregates["resumo"]}


def _run_spark(input_path: Path, processed_dir: Path, curated_dir: Path) -> dict:
    from pyspark.sql import SparkSession, functions as F, types as T

    spark = (
        SparkSession.builder.master("local[*]")
        .appName("DataBurguerLogs")
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .getOrCreate()
    )
    try:
        schema = T.StructType(
            [
                T.StructField("timestamp", T.StringType()),
                T.StructField("ip", T.StringType()),
                T.StructField("url", T.StringType()),
                T.StructField("status_http", T.IntegerType()),
                T.StructField("user_agent", T.StringType()),
                T.StructField("cidade", T.StringType()),
                T.StructField("estado", T.StringType()),
            ]
        )
        frame = spark.read.option("header", True).schema(schema).csv(str(input_path))
        clean = (
            frame.withColumn("timestamp", F.to_timestamp("timestamp"))
            .dropna(subset=["timestamp", "ip", "url", "status_http", "cidade", "estado"])
            .filter(F.col("status_http").between(100, 599))
            .withColumn("data", F.to_date("timestamp"))
            .withColumn("ano", F.year("timestamp"))
            .withColumn("mes", F.month("timestamp"))
            .withColumn("dia", F.dayofmonth("timestamp"))
            .withColumn("hora", F.hour("timestamp"))
        )
        clean.write.mode("overwrite").partitionBy("data").parquet(str(processed_dir))

        def aggregate(column: str, alias: str | None = None) -> pd.DataFrame:
            result = clean.groupBy(column).count().withColumnRenamed("count", "acessos")
            if alias:
                result = result.withColumnRenamed(column, alias)
            return result.orderBy(F.desc("acessos")).toPandas()

        total = clean.count()
        valid = clean.filter(F.col("status_http") < 400).count()
        aggregates = {
            "cidade": aggregate("cidade"),
            "estado": aggregate("estado"),
            "pagina": aggregate("url", "pagina"),
            "hora": aggregate("hora"),
            "data": aggregate("data").assign(data=lambda df: df["data"].astype(str)),
            "status": aggregate("status_http"),
            "resumo": {"total_acessos": total, "acessos_validos": valid, "erros_http": total - valid},
        }
        _save_aggregates(aggregates, curated_dir)
        _load_database(aggregates)
        return {"engine": "pyspark", **aggregates["resumo"]}
    finally:
        spark.stop()


def run_log_pipeline(
    input_path: Path | None = None,
    engine: str = "auto",
    processed_dir: Path | None = None,
    curated_dir: Path | None = None,
) -> dict:
    started = time.perf_counter()
    source = input_path or ROOT / "data" / "raw" / "access_logs.csv"
    processed = processed_dir or ROOT / "data" / "processed" / "logs"
    curated = curated_dir or ROOT / "data" / "curated"
    if not source.exists():
        raise FileNotFoundError(f"Arquivo de logs não encontrado: {source}")
    logger.info("Início do processamento de logs: engine=%s", engine)
    if engine == "pandas":
        result = _run_pandas(source, processed, curated)
    else:
        try:
            result = _run_spark(source, processed, curated)
        except Exception as exc:
            if engine == "spark":
                raise RuntimeError("Falha no processamento PySpark") from exc
            logger.warning("PySpark indisponível (%s). Usando fallback Pandas.", exc)
            result = _run_pandas(source, processed, curated)
    result["duration_seconds"] = round(time.perf_counter() - started, 3)
    result["processed_path"] = str(processed)
    logger.info("Fim do processamento de logs: %s", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Processa logs com PySpark ou fallback Pandas")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--engine", choices=["auto", "spark", "pandas"], default="auto")
    args = parser.parse_args()
    configure_logging()
    run_log_pipeline(args.input, args.engine)


if __name__ == "__main__":
    main()
