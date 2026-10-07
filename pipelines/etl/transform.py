import logging
import re
import unicodedata

import pandas as pd

from pipelines.etl.extract import ExtractedSource

logger = logging.getLogger("databurguer.etl.transform")

CITY_MAP = {
    "recife": "Recife",
    "olinda": "Olinda",
    "paulista": "Paulista",
    "jaboatao": "Jaboatão dos Guararapes",
    "jaboatao dos guararapes": "Jaboatão dos Guararapes",
}


def _key(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).strip().lower())
    return re.sub(r"\s+", " ", "".join(char for char in normalized if not unicodedata.combining(char)))


def standardize_name(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).title()


def standardize_city(value: object) -> str:
    key = _key(value)
    return CITY_MAP.get(key, standardize_name(value))


def _payment_mode(series: pd.Series) -> str | None:
    modes = series.dropna().mode()
    return str(modes.iloc[0]) if not modes.empty else None


def transform_sources(sources: dict[str, ExtractedSource]) -> dict[str, pd.DataFrame]:
    clients = sources["clientes"].frame.copy()
    orders = sources["pedidos"].frame.copy()
    payments = sources["pagamentos"].frame.copy()

    clients = clients.dropna(subset=["cliente_id", "email"]).copy()
    clients["cliente_id"] = pd.to_numeric(clients["cliente_id"], errors="coerce")
    clients = clients.dropna(subset=["cliente_id"])
    clients["cliente_id"] = clients["cliente_id"].astype(int)
    clients["email"] = clients["email"].astype(str).str.strip().str.lower()
    clients = clients.drop_duplicates(subset=["cliente_id"], keep="first")
    clients = clients.drop_duplicates(subset=["email"], keep="first")
    clients["nome"] = clients["nome"].fillna("Não informado").map(standardize_name)
    clients["cidade"] = clients["cidade"].fillna("Não informada").map(standardize_city)
    clients["estado"] = clients["estado"].fillna("PE").astype(str).str.strip().str.upper()
    clients["telefone"] = clients["telefone"].fillna("Não informado")
    clients["criado_em"] = pd.to_datetime(clients["criado_em"], errors="coerce", format="mixed")

    orders["pedido_id"] = pd.to_numeric(orders["pedido_id"], errors="coerce")
    orders["cliente_id"] = pd.to_numeric(orders["cliente_id"], errors="coerce")
    orders["valor_total"] = pd.to_numeric(orders["valor_total"], errors="coerce")
    orders["data_pedido"] = pd.to_datetime(
        orders["data_pedido"], errors="coerce", dayfirst=True, format="mixed"
    )
    orders = orders.dropna(
        subset=["pedido_id", "cliente_id", "valor_total", "data_pedido"]
    ).copy()
    orders = orders[orders["valor_total"] >= 0]
    orders["pedido_id"] = orders["pedido_id"].astype(int)
    orders["cliente_id"] = orders["cliente_id"].astype(int)
    orders["status"] = orders["status"].fillna("DESCONHECIDO").astype(str).str.strip().str.upper()
    orders = orders.drop_duplicates(subset=["pedido_id"], keep="first")

    payments["pedido_id"] = pd.to_numeric(payments["pedido_id"], errors="coerce")
    payments = payments.dropna(subset=["pedido_id"]).copy()
    payments["pedido_id"] = payments["pedido_id"].astype(int)
    payments["forma_pagamento"] = (
        payments["forma_pagamento"].fillna("NAO_INFORMADO").astype(str).str.strip().str.upper()
    )
    payments["valor"] = pd.to_numeric(payments["valor"], errors="coerce")
    payments["data_pagamento"] = pd.to_datetime(
        payments["data_pagamento"], errors="coerce", dayfirst=True, format="mixed"
    )
    payments = payments.drop_duplicates(subset=["pedido_id"], keep="first")

    valid_client_ids = set(clients["cliente_id"])
    valid_orders = orders[orders["cliente_id"].isin(valid_client_ids)].copy()
    integrated = valid_orders.merge(
        payments[["pedido_id", "forma_pagamento", "data_pagamento"]],
        on="pedido_id",
        how="left",
    )
    integrated = integrated.merge(
        clients[["cliente_id", "nome", "cidade", "estado"]], on="cliente_id", how="inner"
    )

    grouped = integrated.groupby(["cliente_id", "nome", "cidade", "estado"], as_index=False)
    analytics_clients = grouped.agg(
        quantidade_pedidos=("pedido_id", "nunique"),
        valor_total_compras=("valor_total", "sum"),
        ticket_medio=("valor_total", "mean"),
        ultima_compra=("data_pedido", "max"),
        forma_pagamento_predominante=("forma_pagamento", _payment_mode),
    )
    analytics_clients["valor_total_compras"] = analytics_clients[
        "valor_total_compras"
    ].round(2)
    analytics_clients["ticket_medio"] = analytics_clients["ticket_medio"].round(2)

    sales_daily = (
        valid_orders.assign(data=valid_orders["data_pedido"].dt.date)
        .groupby("data", as_index=False)
        .agg(
            quantidade_pedidos=("pedido_id", "nunique"),
            faturamento=("valor_total", "sum"),
        )
        .sort_values("data")
    )
    logger.info(
        "Transformação concluída: clientes=%s pedidos=%s analytics=%s",
        len(clients),
        len(valid_orders),
        len(analytics_clients),
    )
    return {
        "clientes_limpos": clients,
        "pedidos_limpos": valid_orders,
        "pagamentos_limpos": payments,
        "integrado": integrated,
        "analytics_clientes": analytics_clients,
        "analytics_vendas_diarias": sales_daily,
    }
