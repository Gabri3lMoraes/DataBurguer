from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import (
    AnalyticsCliente,
    AnalyticsLogCidade,
    AnalyticsLogHora,
    AnalyticsLogPagina,
    AnalyticsLogStatus,
    AnalyticsVendaDiaria,
    Cliente,
    Pagamento,
    Pedido,
    Produto,
)
from app.schemas import PedidoCreate, PedidoResponse
from app.services.orders import BusinessError, create_order

router = APIRouter()


def rows_to_dicts(rows) -> list[dict]:
    return [dict(row._mapping) for row in rows]


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(select(1))
        return {"status": "ok", "database": "connected"}
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível") from exc


@router.get("/clientes")
def list_clients(
    limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)
) -> list[dict]:
    clients = db.scalars(select(Cliente).order_by(Cliente.id).limit(limit)).all()
    return [
        {
            "id": item.id,
            "nome": item.nome,
            "email": item.email,
            "telefone": item.telefone,
            "cidade": item.cidade,
            "estado": item.estado,
            "criado_em": item.criado_em,
        }
        for item in clients
    ]


@router.get("/produtos")
def list_products(db: Session = Depends(get_db)) -> list[dict]:
    products = db.scalars(select(Produto).order_by(Produto.id)).all()
    return [
        {
            "id": item.id,
            "nome": item.nome,
            "categoria": item.categoria,
            "preco": item.preco,
            "estoque_atual": item.estoque_atual,
            "ativo": item.ativo,
        }
        for item in products
    ]


@router.get("/pedidos")
def list_orders(
    limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)
) -> list[dict]:
    orders = db.scalars(
        select(Pedido)
        .options(selectinload(Pedido.itens), selectinload(Pedido.pagamento))
        .order_by(Pedido.data_pedido.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": order.id,
            "cliente_id": order.cliente_id,
            "data_pedido": order.data_pedido,
            "status": order.status,
            "valor_total": order.valor_total,
            "forma_pagamento": order.pagamento.forma_pagamento if order.pagamento else None,
            "itens": [
                {
                    "produto_id": item.produto_id,
                    "quantidade": item.quantidade,
                    "preco_unitario": item.preco_unitario,
                    "subtotal": item.subtotal,
                }
                for item in order.itens
            ],
        }
        for order in orders
    ]


@router.post("/pedidos", response_model=PedidoResponse, status_code=201)
def post_order(payload: PedidoCreate, db: Session = Depends(get_db)) -> Pedido:
    try:
        return create_order(db, payload)
    except BusinessError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Falha ao registrar pedido; transação revertida") from exc


@router.get("/analytics/resumo")
def analytics_summary(db: Session = Depends(get_db)) -> dict:
    clients = db.scalar(select(func.count(Cliente.id))) or 0
    order_count, revenue, average = db.execute(
        select(
            func.count(Pedido.id),
            func.coalesce(func.sum(Pedido.valor_total), 0),
            func.coalesce(func.avg(Pedido.valor_total), 0),
        )
    ).one()
    total_access = db.scalar(select(func.coalesce(func.sum(AnalyticsLogStatus.acessos), 0))) or 0
    http_errors = db.scalar(
        select(func.coalesce(func.sum(AnalyticsLogStatus.acessos), 0)).where(
            AnalyticsLogStatus.status_http >= 400
        )
    ) or 0
    return {
        "quantidade_clientes": clients,
        "quantidade_pedidos": order_count,
        "faturamento_total": Decimal(revenue),
        "ticket_medio": Decimal(average),
        "total_acessos": total_access,
        "erros_http": http_errors,
    }


@router.get("/analytics/vendas")
def analytics_sales(db: Session = Depends(get_db)) -> list[dict]:
    return rows_to_dicts(
        db.execute(
            select(
                AnalyticsVendaDiaria.data,
                AnalyticsVendaDiaria.quantidade_pedidos,
                AnalyticsVendaDiaria.faturamento,
            ).order_by(AnalyticsVendaDiaria.data)
        )
    )


@router.get("/analytics/clientes")
def analytics_clients(db: Session = Depends(get_db)) -> list[dict]:
    return rows_to_dicts(
        db.execute(
            select(
                AnalyticsCliente.cliente_id,
                AnalyticsCliente.nome,
                AnalyticsCliente.cidade,
                AnalyticsCliente.estado,
                AnalyticsCliente.quantidade_pedidos,
                AnalyticsCliente.valor_total_compras,
                AnalyticsCliente.ticket_medio,
                AnalyticsCliente.ultima_compra,
                AnalyticsCliente.forma_pagamento_predominante,
            ).order_by(AnalyticsCliente.cliente_id)
        )
    )


@router.get("/analytics/logs")
def analytics_logs(db: Session = Depends(get_db)) -> dict:
    total = db.scalar(select(func.coalesce(func.sum(AnalyticsLogStatus.acessos), 0))) or 0
    valid = db.scalar(
        select(func.coalesce(func.sum(AnalyticsLogStatus.acessos), 0)).where(
            AnalyticsLogStatus.status_http < 400
        )
    ) or 0
    return {"total_acessos": total, "acessos_validos": valid, "erros_http": total - valid}


@router.get("/analytics/acessos-por-cidade")
def access_by_city(db: Session = Depends(get_db)) -> list[dict]:
    return rows_to_dicts(
        db.execute(
            select(AnalyticsLogCidade.cidade, AnalyticsLogCidade.acessos).order_by(
                AnalyticsLogCidade.acessos.desc()
            )
        )
    )


@router.get("/analytics/acessos-por-pagina")
def access_by_page(db: Session = Depends(get_db)) -> list[dict]:
    return rows_to_dicts(
        db.execute(
            select(AnalyticsLogPagina.pagina, AnalyticsLogPagina.acessos).order_by(
                AnalyticsLogPagina.acessos.desc()
            )
        )
    )


@router.get("/analytics/acessos-por-hora")
def access_by_hour(db: Session = Depends(get_db)) -> list[dict]:
    return rows_to_dicts(
        db.execute(
            select(AnalyticsLogHora.hora, AnalyticsLogHora.acessos).order_by(
                AnalyticsLogHora.hora
            )
        )
    )


@router.get("/analytics/status-http")
def status_http(db: Session = Depends(get_db)) -> list[dict]:
    return rows_to_dicts(
        db.execute(
            select(AnalyticsLogStatus.status_http, AnalyticsLogStatus.acessos).order_by(
                AnalyticsLogStatus.status_http
            )
        )
    )


@router.get("/analytics/formas-pagamento")
def payment_methods(db: Session = Depends(get_db)) -> list[dict]:
    return rows_to_dicts(
        db.execute(
            select(Pagamento.forma_pagamento, func.count(Pagamento.id).label("quantidade"))
            .group_by(Pagamento.forma_pagamento)
            .order_by(func.count(Pagamento.id).desc())
        )
    )
