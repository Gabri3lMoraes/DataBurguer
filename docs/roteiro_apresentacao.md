# Roteiro de apresentação — 10 a 15 minutos

## 1. Introdução — 1 minuto

“O DataBurguer demonstra como uma operação de delivery registra vendas com integridade e transforma fontes e logs em informação analítica.” Mostre a página inicial do dashboard.

## 2. Problema — 1 minuto

Explique os três riscos: venda com estoque inconsistente, arquivos de origens diferentes e análise de alto volume competindo com o sistema de pedidos.

## 3. Arquitetura — 2 minutos

Mostre o Mermaid do README. Destaque a separação entre PostgreSQL operacional, data lake/ETL/Spark e PostgreSQL analítico. Diga que a API atende o dashboard.

## 4. Banco operacional — 1 minuto

Abra Swagger e consulte `/clientes`, `/produtos` e `/pedidos`. Aponte relacionamentos e preço armazenado no servidor.

## 5. Transação — 2 minutos

Anote o estoque, crie um pedido via `POST /pedidos` e mostre a baixa. Tente estoque impossível e confirme que nada foi parcialmente salvo. Cite bloqueio de linha e rollback.

## 6. ETL — 2 minutos

Mostre inconsistências em `data/raw`, execute `python pipelines/etl/pipeline.py` e abra `data/curated`. Explique Extract, Transform e Load e a tabela `etl_execucoes`.

## 7. Spark/MapReduce — 2 minutos

Execute o gerador e o job. Explique map (chave), shuffle (`groupBy`) e reduce (`count`). Mostre partições por data e agregados; deixe claro se a máquina usou Spark ou o fallback Pandas.

## 8. Dashboard — 1 minuto

Passe pelos cards e gráficos. Reforce que os números são calculados, não fixos, e que não há ranking de clientes.

## 9. Escalabilidade — 1 minuto

Explique cluster Spark, S3/HDFS, Kafka, Airflow e ClickHouse/BigQuery. O notebook processa amostra; a arquitetura é o elemento escalável.

## 10. Conclusão — 1 minuto

“O MVP cobre OLTP com transação, ETL, data lake, processamento distribuído conceitual, serving e visualização, preservando uma execução simples.” Finalize exibindo os testes aprovados.
