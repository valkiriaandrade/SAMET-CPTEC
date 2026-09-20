import numpy as np
import pytest
import xarray as xr

from samet_cptec.processing import monthly_anomaly


@pytest.mark.parametrize("variable", ["tmin", "tmax"])
def test_anomaly_and_missing_data(tmp_path, variable):
    paths = []
    for name, data in [
        ("ref", [[10.0, 10.0]]),
        ("day1", [[12.0, np.nan]]),
        ("day2", [[14.0, 15.0]]),
    ]:
        path = tmp_path / f"{name}.nc"
        xr.Dataset(
            {variable: (("lat", "lon"), data)}, coords={"lat": [0], "lon": [0, 1]}
        ).to_netcdf(path, engine="h5netcdf")
        paths.append(path)
    result = monthly_anomaly(paths[1:], paths[0], variable)
    np.testing.assert_allclose(result, [[3, np.nan]])
    assert result.attrs["source_file_count"] == 2


def test_no_days():
    with pytest.raises(ValueError, match="Nenhum"):
        monthly_anomaly([], "unused", "tmin")
