import pandas as pd

REQUIRED_COLUMNS = {
    "timestamp", "ip", "url", "status_http", "user_agent", "cidade", "estado"
}


class LogProcessingError(RuntimeError):
    pass


def clean_logs(frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise LogProcessingError(f"Colunas ausentes nos logs: {sorted(missing)}")
    clean = frame.copy()
    clean["timestamp"] = pd.to_datetime(clean["timestamp"], errors="coerce")
    clean["status_http"] = pd.to_numeric(clean["status_http"], errors="coerce")
    clean = clean.dropna(subset=list(REQUIRED_COLUMNS)).copy()
    clean["status_http"] = clean["status_http"].astype(int)
    clean = clean[clean["status_http"].between(100, 599)]
    clean["data"] = clean["timestamp"].dt.date.astype(str)
    clean["ano"] = clean["timestamp"].dt.year
    clean["mes"] = clean["timestamp"].dt.month
    clean["dia"] = clean["timestamp"].dt.day
    clean["hora"] = clean["timestamp"].dt.hour
    return clean


def _count(frame: pd.DataFrame, column: str, output_name: str | None = None) -> pd.DataFrame:
    name = output_name or column
    return (
        frame.groupby(column, as_index=False)
        .size()
        .rename(columns={column: name, "size": "acessos"})
        .sort_values("acessos", ascending=False)
        .reset_index(drop=True)
    )


def aggregate_logs_pandas(frame: pd.DataFrame) -> dict[str, pd.DataFrame | dict]:
    clean = clean_logs(frame)
    total = len(clean)
    valid = int((clean["status_http"] < 400).sum())
    return {
        "clean": clean,
        "cidade": _count(clean, "cidade"),
        "estado": _count(clean, "estado"),
        "pagina": _count(clean, "url", "pagina"),
        "hora": _count(clean, "hora"),
        "data": _count(clean, "data"),
        "status": _count(clean, "status_http"),
        "resumo": {
            "total_acessos": total,
            "acessos_validos": valid,
            "erros_http": total - valid,
        },
    }
