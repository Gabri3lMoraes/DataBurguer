from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    telefone: Mapped[str | None] = mapped_column(String(30))
    cidade: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(2))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="cliente")


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True)
    categoria: Mapped[str] = mapped_column(String(80))
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estoque_atual: Mapped[int] = mapped_column(Integer)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    itens: Mapped[list["ItemPedido"]] = relationship(back_populates="produto")


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)
    data_pedido: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    status: Mapped[str] = mapped_column(String(30), default="CONFIRMADO")
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    cliente: Mapped[Cliente] = relationship(back_populates="pedidos")
    itens: Mapped[list["ItemPedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan"
    )
    pagamento: Mapped["Pagamento"] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", uselist=False
    )


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), index=True)
    quantidade: Mapped[int] = mapped_column(Integer)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    pedido: Mapped[Pedido] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship(back_populates="itens")


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), unique=True)
    forma_pagamento: Mapped[str] = mapped_column(String(30))
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(30), default="APROVADO")
    data_pagamento: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    pedido: Mapped[Pedido] = relationship(back_populates="pagamento")


class EtlExecucao(Base):
    __tablename__ = "etl_execucoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    arquivo: Mapped[str] = mapped_column(String(255))
    quantidade_registros: Mapped[int] = mapped_column(Integer)
    registros_invalidos: Mapped[int] = mapped_column(Integer)
    processado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    detalhes: Mapped[str | None] = mapped_column(Text)


class AnalyticsCliente(Base):
    __tablename__ = "analytics_clientes"

    cliente_id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    cidade: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(2))
    quantidade_pedidos: Mapped[int] = mapped_column(Integer)
    valor_total_compras: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    ticket_medio: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    ultima_compra: Mapped[datetime | None] = mapped_column(DateTime)
    forma_pagamento_predominante: Mapped[str | None] = mapped_column(String(30))


class AnalyticsResumoVendas(Base):
    __tablename__ = "analytics_resumo_vendas"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    quantidade_clientes: Mapped[int] = mapped_column(Integer)
    quantidade_pedidos: Mapped[int] = mapped_column(Integer)
    faturamento_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    ticket_medio: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class AnalyticsVendaDiaria(Base):
    __tablename__ = "analytics_vendas_diarias"

    data: Mapped[date] = mapped_column(Date, primary_key=True)
    quantidade_pedidos: Mapped[int] = mapped_column(Integer)
    faturamento: Mapped[Decimal] = mapped_column(Numeric(14, 2))


class AnalyticsLogCidade(Base):
    __tablename__ = "analytics_logs_cidade"

    cidade: Mapped[str] = mapped_column(String(100), primary_key=True)
    acessos: Mapped[int] = mapped_column(Integer)


class AnalyticsLogPagina(Base):
    __tablename__ = "analytics_logs_pagina"

    pagina: Mapped[str] = mapped_column(String(120), primary_key=True)
    acessos: Mapped[int] = mapped_column(Integer)


class AnalyticsLogHora(Base):
    __tablename__ = "analytics_logs_hora"

    hora: Mapped[int] = mapped_column(Integer, primary_key=True)
    acessos: Mapped[int] = mapped_column(Integer)


class AnalyticsLogStatus(Base):
    __tablename__ = "analytics_logs_status"

    status_http: Mapped[int] = mapped_column(Integer, primary_key=True)
    acessos: Mapped[int] = mapped_column(Integer)
