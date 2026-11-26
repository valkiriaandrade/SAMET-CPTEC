"""Monthly anomaly computation."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import xarray as xr

from .io import align_exact, read_field, spatial
from .labels import TEMPERATURE_UNITS, units_label


def monthly_anomaly(
    files: Sequence[str | Path], climatology: str | Path, variable: str
) -> xr.DataArray:
    """Mean of the daily ``files`` minus the ``climatology`` field.

    Files are accumulated one at a time, so the whole month is never held in memory.
    Grids must match the climatology exactly and units metadata must agree. SAMeT files
    carry no ``units`` attribute and are in °C; a file that declares units must use °C
    or K.

    Raises:
        ValueError: if no files are given, grids differ or units disagree or are not
            temperatures.
    """
    if not files:
        raise ValueError("No daily files given; pass a directory with daily NetCDF files")
    reference = spatial(read_field(climatology, variable))
    declared = reference.attrs.get("units")
    if declared is not None and units_label(declared) not in TEMPERATURE_UNITS:
        raise ValueError(f"Climatology {climatology} is in {declared!r}; expected °C or K")
    total = None
    for path in files:
        daily = spatial(read_field(path, variable))
        _, daily = align_exact(reference, daily)
        if reference.attrs.get("units") != daily.attrs.get("units"):
            raise ValueError(
                f"Units in {path} differ from the climatology; convert both to the same units"
            )
        total = daily.astype(float) if total is None else total + daily
    # Missing values propagate: an incomplete month is not presented as a full mean.
    result = total / len(files) - reference
    result.name = "temperature_anomaly"
    result.attrs = {
        # an anomaly in K equals the anomaly in °C; keep the unit the files declare
        "units": TEMPERATURE_UNITS.get(units_label(declared), "degC"),
        "source_file_count": len(files),
        "missing_data_policy": "propagate",
        "variable": variable,
    }
    return result
