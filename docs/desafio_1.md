# Desafio 1 — integridade transacional

`create_order` abre uma única transação. O cliente é validado; produtos ativos são buscados com bloqueio de linha; duplicidades de um mesmo produto no payload são somadas; o estoque é conferido antes de qualquer baixa. Preços são lidos do banco e os subtotais são calculados com `Decimal`.

Pedido, itens, baixa e pagamento fazem parte do mesmo commit. Exceções acionam rollback. Os testes cobrem estoque insuficiente e uma falha injetada quando o pagamento seria persistido, comprovando que nem pedido nem baixa sobrevivem.

Para demonstrar: consulte `/produtos`, publique em `/pedidos`, consulte o produto novamente e depois tente uma quantidade impossível.
