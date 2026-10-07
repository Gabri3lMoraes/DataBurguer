# Desafio 3 — logs, MapReduce e escala

O gerador aceita `--rows` e cria timestamp, IP, URL, status, user-agent, cidade e estado. O job Spark aplica schema, descarta registros inválidos, deriva data/hora e agrega dimensões.

- Map: cada evento é projetado para chaves como cidade ou página.
- Shuffle: `groupBy` redistribui eventos com a mesma chave.
- Reduce: `count` soma os eventos por chave.

O detalhe fica em Parquet particionado por data e apenas agregados chegam ao PostgreSQL. O overwrite dinâmico preserva dias ausentes na execução. Em escala real seriam usados cluster Spark, objeto/HDFS, Kafka, Airflow e um data warehouse colunar.
