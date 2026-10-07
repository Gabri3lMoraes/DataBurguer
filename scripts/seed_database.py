import argparse
import logging
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select  # noqa: E402

from app.database import SessionLocal, create_tables  # noqa: E402
from app.logging_config import configure_logging  # noqa: E402
from app.models import (  # noqa: E402
    AnalyticsCliente,
    AnalyticsLogCidade,
    AnalyticsLogHora,
    AnalyticsLogPagina,
    AnalyticsLogStatus,
    AnalyticsResumoVendas,
    AnalyticsVendaDiaria,
    Cliente,
    EtlExecucao,
    ItemPedido,
    Pagamento,
    Pedido,
    Produto,
)
from app.schemas import ItemPedidoCreate, PedidoCreate  # noqa: E402
from app.services.orders import create_order  # noqa: E402

logger = logging.getLogger("databurguer.seed")

PRODUCTS = [
    ("X-Burguer", "Hambúrguer", "22.90"),
    ("X-Bacon", "Hambúrguer", "27.90"),
    ("X-Salada", "Hambúrguer", "24.90"),
    ("Batata Frita", "Acompanhamento", "14.90"),
    ("Refrigerante", "Bebida", "7.00"),
    ("Suco", "Bebida", "9.00"),
    ("Combo Individual", "Combo", "39.90"),
    ("Combo Família", "Combo", "89.90"),
]
CITIES = ["Recife", "Olinda", "Paulista", "Jaboatão dos Guararapes"]
PAYMENTS = ["PIX", "CARTAO_CREDITO", "CARTAO_DEBITO", "DINHEIRO"]
FIRST_NAMES = ["Ana", "Bruno", "Carla", "Daniel", "Eduarda", "Felipe", "Gabriela", "Henrique", "Isabela", "João"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Costa", "Almeida", "Pereira", "Ferreira", "Gomes"]


def clear_database(db) -> None:
    for model in [
        AnalyticsLogStatus,
        AnalyticsLogHora,
        AnalyticsLogPagina,
        AnalyticsLogCidade,
        AnalyticsVendaDiaria,
        AnalyticsResumoVendas,
        AnalyticsCliente,
        EtlExecucao,
        Pagamento,
        ItemPedido,
        Pedido,
        Produto,
        Cliente,
    ]:
        db.execute(delete(model))
    db.commit()


def seed_database(client_count: int = 50, order_count: int = 100, reset: bool = True) -> dict:
    create_tables()
    random.seed(42)

    with SessionLocal() as db:
        if reset:
            clear_database(db)
        elif db.scalar(select(Cliente.id).limit(1)):
            logger.info("Banco já possui dados; use --reset para recriar")
            return {"clientes": 0, "produtos": 0, "pedidos": 0}

        clients = []
        for index in range(client_count):
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            clients.append(
                Cliente(
                    nome=name,
                    email=f"cliente{index + 1}@databurguer.local",
                    telefone=f"(81) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                    cidade=random.choice(CITIES),
                    estado="PE",
                    criado_em=datetime.now() - timedelta(days=random.randint(30, 365)),
                )
            )
        db.add_all(clients)
        db.add_all(
            [
                Produto(
                    nome=name,
                    categoria=category,
                    preco=Decimal(price),
                    estoque_atual=600,
                    ativo=True,
                )
                for name, category, price in PRODUCTS
            ]
        )
        db.commit()

        client_ids = list(db.scalars(select(Cliente.id)))
        product_ids = list(db.scalars(select(Produto.id)))
        db.commit()

        for _ in range(order_count):
            selected = random.sample(product_ids, k=random.randint(1, 3))
            payload = PedidoCreate(
                cliente_id=random.choice(client_ids),
                itens=[
                    ItemPedidoCreate(produto_id=product_id, quantidade=random.randint(1, 3))
                    for product_id in selected
                ],
                forma_pagamento=random.choice(PAYMENTS),
            )
            order = create_order(db, payload)
            with db.begin():
                order.data_pedido = datetime.now() - timedelta(
                    days=random.randint(0, 29), hours=random.randint(0, 23)
                )
                order.pagamento.data_pagamento = order.data_pedido

        result = {"clientes": client_count, "produtos": len(PRODUCTS), "pedidos": order_count}
        logger.info("Seed concluído: %s", result)
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Popula o PostgreSQL operacional")
    parser.add_argument("--clientes", type=int, default=50)
    parser.add_argument("--pedidos", type=int, default=100)
    parser.add_argument("--no-reset", action="store_true")
    args = parser.parse_args()
    configure_logging()
    seed_database(args.clientes, args.pedidos, reset=not args.no_reset)


if __name__ == "__main__":
    main()
