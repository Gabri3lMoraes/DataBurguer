import os
from decimal import Decimal

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="DataBurguer", page_icon="🍔", layout="wide")


@st.cache_data(ttl=15)
def api_get(path: str):
    response = requests.get(f"{API_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def money(value: Decimal | float | str) -> str:
    number = float(value)
    return f"R$ {number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def show_dashboard() -> None:
    st.title("🍔 DATA BURGUER")
    st.caption("Painel Analítico · dados operacionais, ETL e logs processados")
    try:
        summary = api_get("/analytics/resumo")
    except requests.RequestException as exc:
        st.error(f"API indisponível em {API_URL}. Inicie-a antes do dashboard. Detalhe: {exc}")
        st.stop()

    columns = st.columns(6)
    metrics = [
        ("Clientes", summary["quantidade_clientes"]),
        ("Pedidos", summary["quantidade_pedidos"]),
        ("Faturamento", money(summary["faturamento_total"])),
        ("Ticket médio", money(summary["ticket_medio"])),
        ("Acessos", summary["total_acessos"]),
        ("Erros HTTP", summary["erros_http"]),
    ]
    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)

    tab_sales, tab_access, tab_operation = st.tabs(
        ["Vendas", "Acessos", "Operação de demonstração"]
    )
    with tab_sales:
        sales = pd.DataFrame(api_get("/analytics/vendas"))
        methods = pd.DataFrame(api_get("/analytics/formas-pagamento"))
        left, right = st.columns(2)
        if not sales.empty:
            sales["data"] = pd.to_datetime(sales["data"])
            left.subheader("Pedidos por dia")
            left.line_chart(sales.set_index("data")["quantidade_pedidos"])
            right.subheader("Faturamento por dia")
            right.bar_chart(sales.set_index("data")["faturamento"])
        if not methods.empty:
            st.subheader("Formas de pagamento")
            st.bar_chart(methods.set_index("forma_pagamento")["quantidade"])

    with tab_access:
        city = pd.DataFrame(api_get("/analytics/acessos-por-cidade"))
        page = pd.DataFrame(api_get("/analytics/acessos-por-pagina"))
        hour = pd.DataFrame(api_get("/analytics/acessos-por-hora"))
        status = pd.DataFrame(api_get("/analytics/status-http"))
        first, second = st.columns(2)
        if not city.empty:
            first.subheader("Acessos por cidade")
            first.bar_chart(city.set_index("cidade")["acessos"])
        if not page.empty:
            second.subheader("Acessos por página")
            second.bar_chart(page.set_index("pagina")["acessos"])
        third, fourth = st.columns(2)
        if not hour.empty:
            third.subheader("Acessos por hora")
            third.line_chart(hour.sort_values("hora").set_index("hora")["acessos"])
        if not status.empty:
            fourth.subheader("Status HTTP")
            fourth.bar_chart(status.set_index("status_http")["acessos"])

    with tab_operation:
        products = pd.DataFrame(api_get("/produtos"))
        clients = pd.DataFrame(api_get("/clientes?limit=100"))
        st.subheader("Produtos e estoque")
        st.dataframe(products, use_container_width=True, hide_index=True)
        st.subheader("Cadastrar pedido")
        if products.empty or clients.empty:
            st.info("Cadastre clientes e produtos antes de criar pedidos.")
        else:
            with st.form("order-form"):
                client_options = {
                    f"{row['id']} · {row['nome']}": int(row["id"]) for _, row in clients.iterrows()
                }
                product_options = {
                    f"{row['id']} · {row['nome']} · estoque {row['estoque_atual']}": int(row["id"])
                    for _, row in products.iterrows()
                    if row["ativo"]
                }
                client_label = st.selectbox("Cliente", list(client_options))
                product_label = st.selectbox("Produto", list(product_options))
                quantity = st.number_input("Quantidade", min_value=1, max_value=20, value=1)
                payment = st.selectbox(
                    "Pagamento", ["PIX", "CARTAO_CREDITO", "CARTAO_DEBITO", "DINHEIRO"]
                )
                submitted = st.form_submit_button("Criar pedido")
            if submitted:
                response = requests.post(
                    f"{API_URL}/pedidos",
                    json={
                        "cliente_id": client_options[client_label],
                        "itens": [
                            {
                                "produto_id": product_options[product_label],
                                "quantidade": int(quantity),
                            }
                        ],
                        "forma_pagamento": payment,
                    },
                    timeout=10,
                )
                if response.ok:
                    st.cache_data.clear()
                    st.success(f"Pedido #{response.json()['id']} criado com sucesso.")
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Falha ao criar pedido"))


show_dashboard()
