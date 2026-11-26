"""Regenerate every figure in ``figures/`` from the data in ``data/``.

Usage::

    python scripts/make_figures.py [--data-dir data] [--figures-dir figures] [--dpi 200]

Figures whose source data is missing or incomplete (run ``make data``) are skipped with
a warning and the existing image is kept. A figure that fails does not stop the others.
The exit status is 1 if any figure was skipped or failed.
"""

from __future__ import annotations

import argparse
import calendar
import logging
import re
import sys
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
    # The daily minimum-temperature files behind these two figures are not committed;
    # `make data` downloads them (without it, the existing images are kept).
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


def incomplete_month(folder: Path) -> str | None:
    """Describe a daily folder that does not hold every day of its month, else None."""
    match = re.search(r"_([a-z]{3})_(\d{4})$", folder.name)
    if not match or not folder.is_dir():
        return None
    month = [m.lower() for m in calendar.month_abbr].index(match.group(1))
    expected = calendar.monthrange(int(match.group(2)), month)[1]
    found = len(list(folder.glob("*.nc")))
    if found != expected:
        return f"{folder.name} has {found} of {expected} daily files"
    return None


def build(data_dir: Path, figures_dir: Path, dpi: int) -> tuple[list[str], list[str]]:
    """Rebuild all figures with available data; return the names skipped and failed."""
    skipped, failed = [], []
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
        problem = incomplete_month(daily)
        if problem:
            logger.error("Skipping %s: %s; run `make data` first", figure.output, problem)
            skipped.append(figure.output)
            continue
        logger.info("Building %s", figure.output)
        args = [
                "--input", str(daily),
                "--climatology", str(climatology),
                "--variable", figure.variable,
                "--region", figure.region,
                "--shapefile", str(shapefile),
                "--dpi", str(dpi),
                "--output", str(figures_dir / figure.output),
            ]  # fmt: skip
        try:
            samet_cptec(args)
        except SystemExit as error:  # the CLI reports expected errors with exit status 2
            if error.code:
                logger.error("Failed: %s", figure.output)
                failed.append(figure.output)
        except Exception:
            logger.exception("Failed: %s", figure.output)
            failed.append(figure.output)
    return skipped, failed


def main() -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--figures-dir", type=Path, default=ROOT / "figures")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    skipped, failed = build(args.data_dir, args.figures_dir, args.dpi)
    built = len(FIGURES) - len(skipped) - len(failed)
    logger.info(
        "Done: %d figure(s) regenerated, %d skipped, %d failed", built, len(skipped), len(failed)
    )
    return 1 if skipped or failed else 0


if __name__ == "__main__":
    sys.exit(main())
