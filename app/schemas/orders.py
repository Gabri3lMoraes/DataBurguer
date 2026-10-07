from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ItemPedidoCreate(BaseModel):
    produto_id: int = Field(gt=0)
    quantidade: int = Field(gt=0, le=100)


class PedidoCreate(BaseModel):
    cliente_id: int = Field(gt=0)
    itens: list[ItemPedidoCreate] = Field(min_length=1)
    forma_pagamento: str = Field(min_length=2, max_length=30)

    @field_validator("forma_pagamento")
    @classmethod
    def normalize_payment(cls, value: str) -> str:
        return value.strip().upper()


class ItemPedidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal


class PedidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    data_pedido: datetime
    status: str
    valor_total: Decimal
    itens: list[ItemPedidoResponse]
