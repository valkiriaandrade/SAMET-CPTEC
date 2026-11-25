"""Map regions accepted by the command line, with Portuguese aliases."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    """A map domain: display name, extent and optional subset of states."""

    name: str
    label: str
    extent: tuple[float, float, float, float]
    states: tuple[str, ...] | None = None


REGIONS: dict[str, Region] = {
    "brazil": Region("brazil", "Brazil", (-75.0, -34.0, -35.0, 7.0)),
    "south": Region("south", "Southern Brazil", (-57.6, -48.0, -33.75, -22.5), ("PR", "SC", "RS")),
}

#: Portuguese names kept so that existing commands keep working.
ALIASES: dict[str, str] = {"brasil": "brazil", "sul": "south"}


def normalize_region(value: str) -> str:
    """Return the canonical English region name for ``value``.

    Accepts the English names (``brazil``, ``south``) and the Portuguese aliases
    (``brasil``, ``sul``), case-insensitively.

    Raises:
        argparse.ArgumentTypeError: if the name is not a known region or alias.
    """
    key = value.strip().lower()
    key = ALIASES.get(key, key)
    if key not in REGIONS:
        accepted = ", ".join([*REGIONS, *ALIASES])
        raise argparse.ArgumentTypeError(f"unknown region {value!r}; choose one of: {accepted}")
    return key
