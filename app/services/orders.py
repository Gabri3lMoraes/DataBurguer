from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cliente, ItemPedido, Pagamento, Pedido, Produto
from app.schemas import PedidoCreate


class BusinessError(Exception):
    """Base class for errors that can be safely returned to API clients."""


class NotFoundError(BusinessError):
    pass


class InsufficientStockError(BusinessError):
    pass


def create_order(db: Session, payload: PedidoCreate) -> Pedido:
    """Create an order, payment and stock movements in one atomic transaction."""
    quantities: dict[int, int] = defaultdict(int)
    for item in payload.itens:
        quantities[item.produto_id] += item.quantidade

    try:
        with db.begin():
            client = db.get(Cliente, payload.cliente_id)
            if client is None:
                raise NotFoundError(f"Cliente {payload.cliente_id} não encontrado")

            statement = (
                select(Produto)
                .where(Produto.id.in_(quantities), Produto.ativo.is_(True))
                .with_for_update()
            )
            products = {product.id: product for product in db.scalars(statement)}
            missing = sorted(set(quantities) - set(products))
            if missing:
                raise NotFoundError(f"Produto(s) inexistente(s) ou inativo(s): {missing}")

            for product_id, requested in quantities.items():
                product = products[product_id]
                if product.estoque_atual < requested:
                    raise InsufficientStockError(
                        f"Estoque insuficiente para {product.nome}: "
                        f"disponível={product.estoque_atual}, solicitado={requested}"
                    )

            order = Pedido(cliente_id=client.id, status="CONFIRMADO", valor_total=Decimal("0"))
            db.add(order)
            db.flush()

            total = Decimal("0")
            for product_id, quantity in quantities.items():
                product = products[product_id]
                subtotal = product.preco * quantity
                total += subtotal
                product.estoque_atual -= quantity
                order.itens.append(
                    ItemPedido(
                        produto_id=product.id,
                        quantidade=quantity,
                        preco_unitario=product.preco,
                        subtotal=subtotal,
                    )
                )

            order.valor_total = total
            order.pagamento = Pagamento(
                    forma_pagamento=payload.forma_pagamento,
                    valor=total,
                    status="APROVADO",
                )

        return order
    except Exception:
        db.rollback()
        raise
