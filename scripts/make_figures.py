"""Regenerate every figure in ``figures/`` from the data in ``data/``.

Usage::

    python scripts/make_figures.py [--data-dir data] [--figures-dir figures] [--dpi 200]

Figures whose source data is not in the repository are skipped with a warning and
the existing image is kept.
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

from samet_cptec.cli import main as samet_cptec

ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger("make_figures")


@dataclass(frozen=True)
class Figure:
    """One published figure and the inputs needed to rebuild it."""

    output: str
    variable: str
    daily_dir: str
    climatology: str
    region: str = "brazil"


FIGURES = [
    Figure(
        "max_temperature_anomaly_jul.png",
        "tmax",
        "tmax_daily_jul_2024",
        "SAMeT_CPTEC_TMAX_mean_jul.nc",
    ),
    Figure(
        "min_temperature_anomaly_jun.png",
        "tmin",
        "tmin_daily_jun_2024",
        "SAMeT_CPTEC_TMIN_mean_jun.nc",
    ),
    Figure(
        "min_temperature_anomaly_jul_south.png",
        "tmin",
        "tmin_daily_jul_2024",
        "SAMeT_CPTEC_TMIN_mean_jul.nc",
        region="south",
    ),
]


def build(data_dir: Path, figures_dir: Path, dpi: int) -> list[str]:
    """Rebuild all figures with available data; return the names that were skipped."""
    skipped = []
    shapefile = data_dir / "BR_UF_2022.zip"
    for figure in FIGURES:
        daily = data_dir / figure.daily_dir
        climatology = data_dir / figure.climatology
        missing = [str(p) for p in (daily, climatology) if not p.exists()]
        if missing:
            logger.warning(
                "Skipping %s (kept existing image): missing %s",
                figure.output,
                ", ".join(missing),
            )
            skipped.append(figure.output)
            continue
        logger.info("Building %s", figure.output)
        samet_cptec(
            [
                "--input", str(daily),
                "--climatology", str(climatology),
                "--variable", figure.variable,
                "--region", figure.region,
                "--shapefile", str(shapefile),
                "--dpi", str(dpi),
                "--output", str(figures_dir / figure.output),
            ]
        )  # fmt: skip
    return skipped


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--figures-dir", type=Path, default=ROOT / "figures")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    skipped = build(args.data_dir, args.figures_dir, args.dpi)
    built = len(FIGURES) - len(skipped)
    logger.info("Done: %d figure(s) regenerated, %d kept as-is", built, len(skipped))


if __name__ == "__main__":
    main()
