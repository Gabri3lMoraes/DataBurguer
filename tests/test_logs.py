import pandas as pd

from pipelines.logs.aggregate import aggregate_logs_pandas, clean_logs


def sample_logs() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": "2025-06-01T10:00:00", "ip": "1.1.1.1", "url": "/", "status_http": 200, "user_agent": "test", "cidade": "Recife", "estado": "PE"},
            {"timestamp": "2025-06-01T10:30:00", "ip": "1.1.1.2", "url": "/cardapio", "status_http": 404, "user_agent": "test", "cidade": "Recife", "estado": "PE"},
            {"timestamp": "2025-06-01T11:00:00", "ip": "1.1.1.3", "url": "/", "status_http": 200, "user_agent": "test", "cidade": "Olinda", "estado": "PE"},
        ]
    )


def test_log_aggregation_map_reduce_equivalent():
    result = aggregate_logs_pandas(sample_logs())
    assert result["resumo"] == {"total_acessos": 3, "acessos_validos": 2, "erros_http": 1}
    assert result["cidade"].set_index("cidade").loc["Recife", "acessos"] == 2
    assert result["pagina"].set_index("pagina").loc["/", "acessos"] == 2
    assert result["hora"].set_index("hora").loc[10, "acessos"] == 2


def test_invalid_log_is_removed():
    logs = sample_logs()
    logs.loc[len(logs)] = ["invalid", None, "/", 999, "test", "Recife", "PE"]
    assert len(clean_logs(logs)) == 3
