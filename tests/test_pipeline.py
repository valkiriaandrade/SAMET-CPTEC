"""The samet-cptec command run end to end on small files laid out like the SAMeT ones."""

import calendar
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import xarray as xr
from conftest import load_script

from samet_cptec import cli, plotting

LAT = np.arange(-34.0, -21.9, 1.0)  # 34–22° S
LON = np.arange(-58.0, -47.9, 1.0)  # 58–48° W
FILL = -999000000.0


def samet_file(path, variable, values, nobs=True):
    """One SAMeT-style file: (time, lat, lon), _FillValue −999e6, a nobs variable, no units."""
    data = {variable: (("time", "lat", "lon"), values[None].astype("float64"))}
    if nobs:
        data["nobs"] = (("time", "lat", "lon"), np.ones((1, LAT.size, LON.size)))
    encoding = {name: {"_FillValue": FILL} for name in data}
    xr.Dataset(data, coords={"time": [0.0], "lat": LAT, "lon": LON}).to_netcdf(
        path, engine="h5netcdf", encoding=encoding
    )
    return path


def field(value):
    """A field that varies with longitude: ``value`` + 0.1 per degree east of 58° W."""
    return np.full((LAT.size, LON.size), value) + 0.1 * (LON - LON[0])[None, :]


@pytest.fixture
def month(tmp_path):
    """Daily files ``SAMeT_CPTEC_TMAX_YYYYMMDD.nc`` and the matching climatology."""

    def make(year=2024, month=7, days=None, variable="tmax", daily=25.0, clim_month=None):
        days = days or range(1, calendar.monthrange(year, month)[1] + 1)
        folder = tmp_path / f"{variable}_daily_{calendar.month_abbr[month].lower()}_{year}"
        folder.mkdir()
        for day in days:
            values = field(
                daily + (day % 2) * 2.0
            )  # alternate days +2 °C: the mean is not one file
            if day == 1:
                values[0, 0] = np.nan  # written as _FillValue
            samet_file(
                folder / f"SAMeT_CPTEC_{variable.upper()}_{year}{month:02d}{day:02d}.nc",
                variable,
                values,
            )
        name = calendar.month_abbr[clim_month or month].lower()
        clim = samet_file(
            tmp_path / f"SAMeT_CPTEC_{variable.upper()}_mean_{name}.nc",
            variable,
            field(24.0),
            nobs=False,
        )
        return folder, clim

    return make


@pytest.fixture
def drawn(monkeypatch):
    calls = []
    monkeypatch.setattr(
        cli,
        "plot_map",
        lambda values, lat, lon, output, **kw: calls.append(SimpleNamespace(values=values, **kw)),
    )
    return calls


def test_monthly_anomaly_command(month, tmp_path, drawn):
    folder, clim = month()
    netcdf = tmp_path / "anomaly.nc"
    cli.main(["--input", str(folder), "--climatology", str(clim), "--variable", "tmax"]
             + ["--output", "unused.png", "--netcdf", str(netcdf)])  # fmt: skip
    [call] = drawn
    # 16 odd days at +2 °C over 31 days: mean = 25 + 32/31 °C, minus the 24 °C climatology
    expected = 1 + 32 / 31
    np.testing.assert_allclose(call.values[1:, :], expected, rtol=1e-6)
    assert np.isnan(call.values[0, 0])  # a missing day propagates, never filled in
    assert call.title == "SAMeT maximum temperature anomaly – Brazil, July 2024 (°C)"
    assert call.extend_colours is True and call.cmap == "coolwarm"
    saved = xr.open_dataset(netcdf, engine="h5netcdf")
    assert saved.temperature_anomaly.attrs["units"] == "degC"
    assert saved.temperature_anomaly.attrs["source_file_count"] == 31
    saved.close()


def test_partial_month_is_refused_unless_allowed(month, drawn, capsys):
    folder, clim = month(days=range(1, 26))
    args = [
        "--input",
        str(folder),
        "--climatology",
        str(clim),
        "--variable",
        "tmax",
        "--output",
        "x.png",
    ]
    with pytest.raises(SystemExit):
        cli.main(args)
    assert "6 of 31 days of July 2024 missing" in capsys.readouterr().err and not drawn
    cli.main([*args, "--allow-partial"])
    assert drawn[0].title.endswith("Brazil, 01 Jul 2024 to 25 Jul 2024 (°C)")


def test_climatology_of_another_month_is_refused(month, drawn, capsys):
    folder, clim = month(clim_month=6)
    with pytest.raises(SystemExit):
        cli.main(
            [
                "--input",
                str(folder),
                "--climatology",
                str(clim),
                "--variable",
                "tmax",
                "--output",
                "x.png",
            ]
        )
    assert "the climatology SAMeT_CPTEC_TMAX_mean_jun.nc is for June" in capsys.readouterr().err


def test_declared_units_must_be_temperatures_and_agree(month, tmp_path, drawn, capsys):
    folder, clim = month()
    ds = xr.open_dataset(clim, engine="h5netcdf").load()
    ds.tmax.attrs["units"] = "mm"
    ds.to_netcdf(tmp_path / "SAMeT_CPTEC_TMAX_mean_jul_mm.nc", engine="h5netcdf")
    args = ["--input", str(folder), "--variable", "tmax", "--output", "x.png"]
    with pytest.raises(SystemExit):
        cli.main([*args, "--climatology", str(tmp_path / "SAMeT_CPTEC_TMAX_mean_jul_mm.nc")])
    assert "expected °C or K" in capsys.readouterr().err
    ds.tmax.attrs["units"] = "K"
    ds.to_netcdf(tmp_path / "SAMeT_CPTEC_TMAX_mean_jul_k.nc", engine="h5netcdf")
    with pytest.raises(SystemExit):  # daily files have no units: they do not agree with K
        cli.main([*args, "--climatology", str(tmp_path / "SAMeT_CPTEC_TMAX_mean_jul_k.nc")])
    assert "differ from the climatology" in capsys.readouterr().err


# ---------------------------------------------------------------- masking and colours
@pytest.fixture
def states(tmp_path):
    import geopandas as gpd
    from shapely.geometry import box

    path = tmp_path / "states.geojson"
    gpd.GeoDataFrame(
        {"SIGLA_UF": ["RS", "SC", "PR", "SP"]},
        geometry=[box(-57.5, -33.6, -49.6, -27.1), box(-53.8, -29.3, -48.4, -25.9),
                  box(-54.6, -26.7, -48.1, -22.6), box(-53.1, -25.3, -44.2, -19.8)],
        crs=4326,
    )  .to_file(path)  # fmt: skip
    return path


def test_mask_keeps_only_the_selected_states(states):
    lon2d, lat2d = np.meshgrid(LON, LAT)
    masked = plotting.mask_to_borders(
        np.ones_like(lon2d), lat2d, lon2d + 360, states, ["PR", "SC", "RS"]
    )
    inside = lambda lat, lon: bool(np.isfinite(masked[LAT == lat, LON == lon][0]))  # noqa: E731
    assert inside(-30.0, -53.0) and inside(-27.0, -50.0) and inside(-24.0, -51.0)  # RS, SC, PR
    assert not inside(-22.0, -48.0)  # São Paulo only
    assert not inside(-34.0, -58.0)  # outside every state
    everything = plotting.mask_to_borders(np.ones_like(lon2d), lat2d, lon2d, states)
    assert np.isfinite(everything[LAT == -22.0, LON == -48.0][0])  # all states without a selection


def test_values_beyond_the_scale_get_their_own_colour(monkeypatch, tmp_path, states):
    import matplotlib.colors

    norms = []

    class Recording(matplotlib.colors.BoundaryNorm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            norms.append(self)

    monkeypatch.setattr(matplotlib.colors, "BoundaryNorm", Recording)
    plotting.plot_map(field(0.0), LAT, LON, tmp_path / "m.png", title="t", label="°C", levels=cli.LEVELS,
                      cmap="coolwarm", shapefile=states, extend_colours=True)  # fmt: skip
    [norm] = norms
    top, beyond = norm(np.array([2.75, 3.6]))
    bottom, below = norm(np.array([-2.75, -3.6]))
    assert top != beyond and bottom != below  # the arrows are not the end-class colours
    assert (tmp_path / "m.png").read_bytes().startswith(b"\x89PNG")


# ---------------------------------------------------------------- make figures
def test_make_figures_skips_incomplete_months_and_reports_failures(month, tmp_path, monkeypatch):
    make_figures = load_script("make_figures")
    monkeypatch.setattr(sys, "argv", ["make_figures", "--data-dir", str(tmp_path / "none")])
    assert make_figures.main() == 1  # no data: every figure skipped
    folder, clim = month(days=range(1, 20))
    (tmp_path / "bad_daily_jul_2024").mkdir()
    for day in range(1, 32):
        (tmp_path / "bad_daily_jul_2024" / f"SAMeT_CPTEC_TMAX_202407{day:02d}.nc").write_bytes(b"x")
    Figure = make_figures.Figure
    monkeypatch.setattr(make_figures, "FIGURES", [
        Figure("partial.png", "tmax", folder.name, clim.name),
        Figure("broken.png", "tmax", "bad_daily_jul_2024", clim.name),
    ])  # fmt: skip
    skipped, failed = make_figures.build(tmp_path, tmp_path / "figures", 50)
    assert skipped == ["partial.png"] and failed == ["broken.png"]
