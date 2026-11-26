"""``samet-cptec`` command: monthly temperature anomaly maps."""

from __future__ import annotations

import argparse
import calendar
import logging
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from .arguments import build_parser, execute
from .io import files_in, save_netcdf
from .labels import (
    SOURCE_CREDIT,
    dates_from_names,
    format_period,
    format_title,
    month_coverage_problem,
    month_from_name,
    units_label,
)
from .plotting import plot_map
from .processing import monthly_anomaly
from .regions import ALIASES, REGIONS, normalize_region

logger = logging.getLogger(__name__)

LEVELS = np.arange(-3, 3.5, 0.5)
CMAP = "coolwarm"


def check_month(files: list[Path], climatology: str | Path, allow_partial: bool) -> None:
    """Check that ``files`` are the days of one whole month, the month of ``climatology``.

    Raises:
        ValueError: on a partial month (unless ``allow_partial``) or another month's
            climatology.
    """
    dates = dates_from_names(files)
    problem = month_coverage_problem(dates)
    if problem and not allow_partial:
        raise ValueError(
            f"{problem}; a monthly anomaly needs every day of the month "
            "(run `make data`, or pass --allow-partial to compute it anyway)"
        )
    if problem:
        logger.warning("Not a whole month: %s", problem)
    expected = month_from_name(climatology)
    months = sorted({calendar.month_name[d.month] for d in dates})
    if expected is None:
        logger.warning("Cannot tell the month of %s from its name; not checked", climatology)
    elif dates and months != [expected]:
        raise ValueError(
            f"The daily files are from {' and '.join(months)} but the climatology "
            f"{Path(climatology).name} is for {expected}"
        )


def run(args: argparse.Namespace) -> None:
    """Compute the anomaly described by ``args`` and draw the map."""
    files = files_in(args.input, ".nc")
    logger.info("Averaging %d daily %s files from %s", len(files), args.variable, args.input)
    check_month(files, args.climatology, args.allow_partial)
    field = monthly_anomaly(files, args.climatology, args.variable)
    if args.netcdf:
        save_netcdf(field, args.netcdf)
        logger.info("Anomaly field written to %s", args.netcdf)
    region = REGIONS[args.region]
    period = args.period or format_period(dates_from_names(files))
    units = units_label(field.attrs.get("units"))
    plot_map(
        field.values,
        field.lat,
        field.lon,
        args.output,
        title=args.title or format_title(args.variable, period, region.label, units),
        label=f"Temperature anomaly ({units})",
        levels=LEVELS,
        cmap=CMAP,
        # Areas beyond ±3 °C get their own shades, as in the original scripts
        # (contourf with extend="both"), not the colours of the end classes.
        extend_colours=True,
        shapefile=args.shapefile,
        states=list(region.states) if region.states else None,
        extent=list(region.extent),
        credit=SOURCE_CREDIT,
        dpi=args.dpi,
    )


def build_cli() -> argparse.ArgumentParser:
    """Return the parser for the ``samet-cptec`` command."""
    parser = build_parser(
        "SAMeT monthly temperature anomaly: mean of the daily files minus the climatology. "
        "Use daily files from a single month, with the same units as the climatology."
    )
    parser.add_argument("--input", required=True, help="directory with daily NetCDF files")
    parser.add_argument(
        "--climatology", required=True, help="NetCDF climatology for the same month"
    )
    parser.add_argument("--variable", choices=["tmin", "tmax"], default="tmin")
    parser.add_argument(
        "--region",
        type=normalize_region,
        choices=list(REGIONS),
        default="brazil",
        help=f"map domain (Portuguese aliases accepted: {', '.join(ALIASES)})",
    )
    parser.add_argument(
        "--period", help='period shown in the title, e.g. "July 2024" (default: from file names)'
    )
    parser.add_argument("--netcdf", help="also save the computed anomaly field to this file")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="compute the anomaly even if the daily files are not one whole month",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point of the ``samet-cptec`` command."""
    execute(build_cli(), run, argv)
