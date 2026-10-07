# Desafio 2 — ETL

## Extract

Lê dois CSVs e um JSON, valida existência/estrutura e registra arquivo, total, inválidos e horário na tabela `etl_execucoes`.

## Transform

Remove duplicidades por chave e e-mail, padroniza nomes, cidade, estado, status e pagamento, converte datas mistas, descarta chaves/valores essenciais inválidos e preenche campos opcionais. Em seguida une pedidos, pagamentos e clientes.

## Load

Grava conjuntos limpos e integrados em Parquet e atualiza tabelas analíticas com quantidade de pedidos, gasto, ticket médio, última compra e pagamento predominante. Também produz vendas diárias e resumo geral. Não há ranking de pessoas.
