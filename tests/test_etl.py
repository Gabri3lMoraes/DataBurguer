from datetime import datetime
from pathlib import Path

import pandas as pd

from pipelines.etl.extract import ExtractedSource
from pipelines.etl.transform import standardize_city, transform_sources


def source(name: str, frame: pd.DataFrame) -> ExtractedSource:
    return ExtractedSource(name, Path(f"{name}.csv"), frame, len(frame), 0, datetime.now())


def sample_sources() -> dict[str, ExtractedSource]:
    clients = pd.DataFrame(
        [
            {"cliente_id": 1, "nome": "  ANA SILVA ", "email": "ANA@EXAMPLE.COM ", "telefone": None, "cidade": "recife ", "estado": "pe", "criado_em": "2025-01-01"},
            {"cliente_id": 1, "nome": "Duplicada", "email": "ana@example.com", "telefone": "1", "cidade": "RECIFE", "estado": "PE", "criado_em": "01/01/2025"},
            {"cliente_id": 2, "nome": "João Lima", "email": "joao@example.com", "telefone": "2", "cidade": "JABOATAO", "estado": "PE", "criado_em": "2025-01-02"},
        ]
    )
    orders = pd.DataFrame(
        [
            {"pedido_id": 10, "cliente_id": 1, "data_pedido": "01/02/2025", "status": " confirmado ", "valor_total": "20.00"},
            {"pedido_id": 11, "cliente_id": 1, "data_pedido": "2025-02-02", "status": "CONFIRMADO", "valor_total": "40.00"},
            {"pedido_id": 12, "cliente_id": 2, "data_pedido": "2025-02-03", "status": "CONFIRMADO", "valor_total": "30.00"},
        ]
    )
    payments = pd.DataFrame(
        [
            {"pagamento_id": 1, "pedido_id": 10, "forma_pagamento": " pix ", "valor": 20, "status": "APROVADO", "data_pagamento": "2025-02-01"},
            {"pagamento_id": 2, "pedido_id": 11, "forma_pagamento": "PIX", "valor": 40, "status": "APROVADO", "data_pagamento": "02/02/2025"},
            {"pagamento_id": 3, "pedido_id": 12, "forma_pagamento": "DINHEIRO", "valor": 30, "status": "APROVADO", "data_pagamento": "2025-02-03"},
        ]
    )
    return {"clientes": source("clientes", clients), "pedidos": source("pedidos", orders), "pagamentos": source("pagamentos", payments)}


def test_etl_standardizes_values():
    result = transform_sources(sample_sources())
    client = result["clientes_limpos"].iloc[0]
    assert client["nome"] == "Ana Silva"
    assert client["cidade"] == "Recife"
    assert client["estado"] == "PE"
    assert standardize_city("JABOATAO") == "Jaboatão dos Guararapes"


def test_etl_removes_duplicates():
    result = transform_sources(sample_sources())
    assert len(result["clientes_limpos"]) == 2


def test_etl_calculates_average_ticket():
    result = transform_sources(sample_sources())
    ana = result["analytics_clientes"].query("cliente_id == 1").iloc[0]
    assert ana["quantidade_pedidos"] == 2
    assert ana["valor_total_compras"] == 60.0
    assert ana["ticket_medio"] == 30.0
    assert ana["forma_pagamento_predominante"] == "PIX"
