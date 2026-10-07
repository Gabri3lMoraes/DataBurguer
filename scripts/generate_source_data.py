import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.logging_config import configure_logging  # noqa: E402
from app.models import Cliente, Pagamento, Pedido  # noqa: E402

logger = logging.getLogger("databurguer.source_data")


def generate_source_data(output_dir: Path | None = None) -> dict[str, Path]:
    destination = output_dir or ROOT / "data" / "raw"
    destination.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        clients = pd.read_sql(
            select(
                Cliente.id.label("cliente_id"),
                Cliente.nome,
                Cliente.email,
                Cliente.telefone,
                Cliente.cidade,
                Cliente.estado,
                Cliente.criado_em,
            ),
            db.connection(),
        )
        orders = pd.read_sql(
            select(
                Pedido.id.label("pedido_id"),
                Pedido.cliente_id,
                Pedido.data_pedido,
                Pedido.status,
                Pedido.valor_total,
            ),
            db.connection(),
        )
        payments = pd.read_sql(
            select(
                Pagamento.id.label("pagamento_id"),
                Pagamento.pedido_id,
                Pagamento.forma_pagamento,
                Pagamento.valor,
                Pagamento.status,
                Pagamento.data_pagamento,
            ),
            db.connection(),
        )

    if not clients.empty:
        clients.loc[0, "nome"] = f"  {str(clients.loc[0, 'nome']).upper()}  "
        clients.loc[1, "cidade"] = "recife "
        clients.loc[2, "cidade"] = "JABOATAO"
        clients.loc[3, "telefone"] = None
        clients = pd.concat([clients, clients.iloc[[0]]], ignore_index=True)
        clients.loc[len(clients) - 1, "nome"] = "registro duplicado"
    if not orders.empty:
        orders.loc[0, "data_pedido"] = pd.Timestamp(orders.loc[0, "data_pedido"]).strftime(
            "%d/%m/%Y %H:%M"
        )
        orders.loc[1, "status"] = " confirmado "
        orders = pd.concat([orders, orders.iloc[[0]]], ignore_index=True)
    payment_records = payments.copy()
    if not payment_records.empty:
        payment_records.loc[0, "forma_pagamento"] = " pix "
        payment_records.loc[1, "data_pagamento"] = pd.Timestamp(
            payment_records.loc[1, "data_pagamento"]
        ).strftime("%d/%m/%Y")

    clients_path = destination / "clientes.csv"
    orders_path = destination / "pedidos.csv"
    payments_path = destination / "pagamentos.json"
    clients.to_csv(clients_path, index=False)
    orders.to_csv(orders_path, index=False)
    payments_path.write_text(
        json.dumps(payment_records.to_dict(orient="records"), ensure_ascii=False, default=str, indent=2),
        encoding="utf-8",
    )
    logger.info("Fontes geradas em %s", destination)
    return {"clientes": clients_path, "pedidos": orders_path, "pagamentos": payments_path}


if __name__ == "__main__":
    configure_logging()
    generate_source_data()
