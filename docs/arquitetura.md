# Arquitetura do DataBurguer

O sistema separa OLTP, processamento e leitura analítica. O PostgreSQL operacional recebe transações curtas. CSV/JSON e logs entram no data lake local. O ETL e o Spark transformam esses dados sem fazer varreduras nas tabelas operacionais. Somente resultados pequenos chegam às tabelas `analytics_*`, consumidas pela FastAPI e pelo Streamlit.

## Decisões

- SQLAlchemy concentra o modelo relacional e permite transações explícitas.
- Parquet reduz leitura e preserva tipos em comparação com CSV.
- Partições por data evitam reprocessar todo o histórico.
- PySpark demonstra processamento distribuído; Pandas é fallback local transparente.
- A API desacopla o dashboard do acesso direto ao banco.

## Fluxo

1. Operação grava clientes, pedidos, itens, pagamentos e estoque.
2. Uma extração acadêmica produz fontes deliberadamente imperfeitas.
3. ETL limpa, integra e grava dados curados/tabelas analíticas.
4. Logs são processados separadamente e particionados por data.
5. API e dashboard consultam OLTP somente para telas operacionais e analytics para indicadores.
