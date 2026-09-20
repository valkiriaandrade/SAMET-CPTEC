from .io import align_exact, read_field, spatial


def monthly_anomaly(files, climatology, variable):
    if not files:
        raise ValueError("Nenhum arquivo diário informado")
    reference = spatial(read_field(climatology, variable))
    total = None
    for path in files:
        daily = spatial(read_field(path, variable))
        _, daily = align_exact(reference, daily)
        if reference.attrs.get("units") != daily.attrs.get("units"):
            raise ValueError(f"Unidades incompatíveis em {path}")
        total = daily.astype(float) if total is None else total + daily
    # Ausências propagam: não apresentar mês incompleto como média completa.
    result = total / len(files) - reference
    result.name = "temperature_anomaly"
    result.attrs = {
        "units": "degC",
        "source_file_count": len(files),
        "missing_data_policy": "propagate",
        "variable": variable,
    }
    return result
