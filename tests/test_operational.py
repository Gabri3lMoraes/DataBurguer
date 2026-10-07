from decimal import Decimal

import pytest
from sqlalchemy import event, func, select

from app.models import Cliente, Pagamento, Pedido, Produto
from app.schemas import ItemPedidoCreate, PedidoCreate
from app.services.orders import InsufficientStockError, create_order


def payload(client_id: int, product_id: int, quantity: int = 2) -> PedidoCreate:
    return PedidoCreate(
        cliente_id=client_id,
        itens=[ItemPedidoCreate(produto_id=product_id, quantidade=quantity)],
        forma_pagamento="pix",
    )


def test_create_client(db):
    db.add(
        Cliente(
            nome="Bruno",
            email="bruno@example.com",
            cidade="Olinda",
            estado="PE",
        )
    )
    db.commit()
    assert db.scalar(select(func.count(Cliente.id))) == 1


def test_create_product(db):
    db.add(
        Produto(
            nome="Suco",
            categoria="Bebida",
            preco=Decimal("8.50"),
            estoque_atual=20,
            ativo=True,
        )
    )
    db.commit()
    assert db.scalar(select(Produto).where(Produto.nome == "Suco")).estoque_atual == 20


def test_create_order_calculates_total(operational_data, db):
    client, product = operational_data
    order = create_order(db, payload(client.id, product.id, 2))
    assert order.valor_total == Decimal("40.00")
    assert order.pagamento.forma_pagamento == "PIX"
    assert len(order.itens) == 1


def test_order_decreases_stock(operational_data, db):
    client, product = operational_data
    create_order(db, payload(client.id, product.id, 3))
    assert db.get(Produto, product.id).estoque_atual == 7


def test_insufficient_stock_is_blocked(operational_data, db):
    client, product = operational_data
    with pytest.raises(InsufficientStockError):
        create_order(db, payload(client.id, product.id, 99))
    assert db.scalar(select(func.count(Pedido.id))) == 0
    assert db.get(Produto, product.id).estoque_atual == 10


def test_rollback_restores_stock_on_mid_transaction_failure(operational_data, db):
    client, product = operational_data

    def fail_when_payment_is_flushed(session, *_):
        if any(isinstance(item, Pagamento) for item in session.new):
            raise RuntimeError("falha simulada no pagamento")

    event.listen(db, "before_flush", fail_when_payment_is_flushed)
    try:
        with pytest.raises(RuntimeError, match="falha simulada"):
            create_order(db, payload(client.id, product.id, 2))
    finally:
        event.remove(db, "before_flush", fail_when_payment_is_flushed)

    assert db.scalar(select(func.count(Pedido.id))) == 0
    assert db.get(Produto, product.id).estoque_atual == 10
