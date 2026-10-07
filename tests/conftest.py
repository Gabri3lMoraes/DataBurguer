from decimal import Decimal
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.database import Base
from app.models import Cliente, Produto


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def operational_data(db):
    client = Cliente(
        nome="Ana Silva",
        email="ana@example.com",
        telefone="81999999999",
        cidade="Recife",
        estado="PE",
    )
    product = Produto(
        nome="X-Burguer",
        categoria="Hambúrguer",
        preco=Decimal("20.00"),
        estoque_atual=10,
        ativo=True,
    )
    db.add_all([client, product])
    db.commit()
    return client, product
