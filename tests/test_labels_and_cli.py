import argparse
from datetime import date

import numpy as np
import pytest
import xarray as xr

from samet_cptec.arguments import positive_int
from samet_cptec.cli import build_cli
from samet_cptec.labels import (
    dates_from_names,
    format_period,
    format_title,
    units_label,
)
from samet_cptec.processing import monthly_anomaly
from samet_cptec.regions import REGIONS, normalize_region


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("brazil", "brazil"),
        ("south", "south"),
        ("brasil", "brazil"),
        ("sul", "south"),
        ("SUL", "south"),
        (" South ", "south"),
    ],
)
def test_region_names_and_portuguese_aliases(value, expected):
    assert normalize_region(value) == expected


def test_unknown_region_lists_accepted_values():
    with pytest.raises(argparse.ArgumentTypeError, match="brazil, south, brasil, sul"):
        normalize_region("east")


@pytest.mark.parametrize("alias", ["sul", "south"])
def test_cli_accepts_region_alias(alias):
    args = build_cli().parse_args(
        ["--input", "d", "--climatology", "c.nc", "--output", "o.png", "--region", alias]
    )
    assert args.region == "south"
    assert REGIONS[args.region].states == ("PR", "SC", "RS")


def test_cli_dpi_default_and_validation():
    base = ["--input", "d", "--climatology", "c.nc", "--output", "o.png"]
    assert build_cli().parse_args(base).dpi == 200
    assert build_cli().parse_args([*base, "--dpi", "300"]).dpi == 300
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int("0")


@pytest.mark.parametrize(
    ("units", "label"),
    [("degC", "°C"), ("degree_Celsius", "°C"), ("K", "K"), (None, ""), ("W m-2", "W m-2")],
)
def test_units_label(units, label):
    assert units_label(units) == label


def test_units_mismatch_is_rejected(tmp_path):
    paths = []
    for name, units in [("ref", "degC"), ("day", "K")]:
        path = tmp_path / f"{name}.nc"
        data = xr.DataArray([[1.0]], dims=("lat", "lon"), attrs={"units": units})
        xr.Dataset({"tmax": data}, coords={"lat": [0], "lon": [0]}).to_netcdf(
            path, engine="h5netcdf"
        )
        paths.append(path)
    with pytest.raises(ValueError, match="same units"):
        monthly_anomaly(paths[1:], paths[0], "tmax")


def test_anomaly_units_metadata(tmp_path):
    path = tmp_path / "ref.nc"
    xr.Dataset({"tmin": (("lat", "lon"), [[1.0]])}, coords={"lat": [0], "lon": [0]}).to_netcdf(
        path, engine="h5netcdf"
    )
    result = monthly_anomaly([path], path, "tmin")
    assert units_label(result.attrs["units"]) == "°C"
    np.testing.assert_allclose(result, [[0.0]])


def test_period_from_provider_file_names():
    names = [f"SAMeT_CPTEC_TMAX_202407{day:02d}.nc" for day in (1, 15, 31)]
    dates = dates_from_names(names)
    assert dates[0] == date(2024, 7, 1)
    assert format_period(dates) == "July 2024"
    assert format_period([date(2024, 6, 30), date(2024, 7, 2)]) == "30 Jun 2024 to 02 Jul 2024"
    assert format_period([]) is None
    assert dates_from_names(["climatology.nc"]) == []


def test_title_formatting():
    assert (
        format_title("tmax", "July 2024", "Brazil")
        == "SAMeT maximum temperature anomaly – Brazil, July 2024 (°C)"
    )
    assert (
        format_title("tmin", "June 2024", "Southern Brazil")
        == "SAMeT minimum temperature anomaly – Southern Brazil, June 2024 (°C)"
    )
    assert format_title("tmin") == "SAMeT minimum temperature anomaly (°C)"
