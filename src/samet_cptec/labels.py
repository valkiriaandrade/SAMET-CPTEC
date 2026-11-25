"""Human-readable labels for map titles and colorbars."""

from __future__ import annotations

import calendar
import re
from collections.abc import Iterable
from datetime import date
from pathlib import Path

PRODUCT = "SAMeT"
#: Base period of the CPTEC SAMeT monthly climatologies used for the anomalies.
CLIMATOLOGY_PERIOD = "2000–2023"
SOURCE_CREDIT = f"Data: CPTEC/INPE SAMeT · climatology {CLIMATOLOGY_PERIOD}"

VARIABLE_NAMES: dict[str, str] = {
    "tmin": "minimum temperature",
    "tmax": "maximum temperature",
}

_UNIT_LABELS: dict[str, str] = {
    "degc": "°C",
    "degree_celsius": "°C",
    "degrees_celsius": "°C",
    "celsius": "°C",
    "°c": "°C",
    "c": "°C",
    "k": "K",
    "kelvin": "K",
}

_DATE_IN_NAME = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)")


def units_label(units: str | None) -> str:
    """Return a display label for CF-style ``units`` (``"degC"`` -> ``"°C"``).

    Unknown units are returned unchanged; missing units give an empty string.
    """
    if not units:
        return ""
    return _UNIT_LABELS.get(units.strip().lower(), units.strip())


def dates_from_names(paths: Iterable[str | Path]) -> list[date]:
    """Extract ``YYYYMMDD`` dates from file names such as ``SAMeT_CPTEC_TMAX_20240701.nc``."""
    found = []
    for path in paths:
        match = _DATE_IN_NAME.search(Path(path).name)
        if match:
            year, month, day = map(int, match.groups())
            try:
                found.append(date(year, month, day))
            except ValueError:
                continue
    return sorted(found)


def format_period(dates: Iterable[date]) -> str | None:
    """Describe a list of dates: ``"July 2024"`` for one month, otherwise a date range."""
    dates = sorted(dates)
    if not dates:
        return None
    first, last = dates[0], dates[-1]
    if (first.year, first.month) == (last.year, last.month):
        return f"{calendar.month_name[first.month]} {first.year}"
    return f"{first:%d %b %Y} to {last:%d %b %Y}"


def format_title(
    variable: str, period: str | None = None, region: str | None = None, units: str = "°C"
) -> str:
    """Build a map title with product name, quantity, region, period and units.

    >>> format_title("tmax", "July 2024", "Brazil")
    'SAMeT maximum temperature anomaly – Brazil, July 2024 (°C)'
    """
    quantity = VARIABLE_NAMES.get(variable, variable)
    where = ", ".join(part for part in (region, period) if part)
    title = f"{PRODUCT} {quantity} anomaly"
    if where:
        title += f" – {where}"
    if units:
        title += f" ({units})"
    return title
