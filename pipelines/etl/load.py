import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import (
    AnalyticsCliente,
    AnalyticsResumoVendas,
    AnalyticsVendaDiaria,
    Cliente,
    EtlExecucao,
    Pedido,
)
from pipelines.etl.extract import ExtractedSource

logger = logging.getLogger("databurguer.etl.load")


def _clean_record(record: dict) -> dict:
    return {key: (None if pd.isna(value) else value) for key, value in record.items()}


def load_results(
    db: Session,
    transformed: dict[str, pd.DataFrame],
    sources: dict[str, ExtractedSource],
    curated_dir: Path,
) -> dict:
    curated_dir.mkdir(parents=True, exist_ok=True)
    parquet_files: list[str] = []
    for name in ["clientes_limpos", "pedidos_limpos", "integrado", "analytics_clientes"]:
        path = curated_dir / f"{name}.parquet"
        transformed[name].to_parquet(path, index=False)
        parquet_files.append(str(path))

    with db.begin():
        db.execute(delete(AnalyticsCliente))
        db.execute(delete(AnalyticsVendaDiaria))
        db.execute(delete(AnalyticsResumoVendas))

        db.add_all(
            AnalyticsCliente(**_clean_record(record))
            for record in transformed["analytics_clientes"].to_dict(orient="records")
        )
        db.add_all(
            AnalyticsVendaDiaria(**_clean_record(record))
            for record in transformed["analytics_vendas_diarias"].to_dict(orient="records")
        )
        order_count, revenue, average = db.execute(
            select(
                func.count(Pedido.id),
                func.coalesce(func.sum(Pedido.valor_total), 0),
                func.coalesce(func.avg(Pedido.valor_total), 0),
            )
        ).one()
        db.add(
            AnalyticsResumoVendas(
                id=1,
                quantidade_clientes=db.scalar(select(func.count(Cliente.id))) or 0,
                quantidade_pedidos=order_count,
                faturamento_total=revenue,
                ticket_medio=average,
                atualizado_em=datetime.now(),
            )
        )
        for source in sources.values():
            db.add(
                EtlExecucao(
                    arquivo=source.path.name,
                    quantidade_registros=source.total_records,
                    registros_invalidos=source.invalid_records,
                    processado_em=source.processed_at,
                    detalhes="Carga concluída",
                )
            )
    logger.info("Carga concluída: %s arquivos Parquet", len(parquet_files))
    return {"parquet_files": parquet_files, "analytics_rows": len(transformed["analytics_clientes"])}
