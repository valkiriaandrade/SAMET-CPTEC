import io
import socket
import urllib.error
from datetime import date

import pytest


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_plan_daily_files_and_climatology(download_module):
    items = download_module.plan("tmin", date(2024, 6, 1))
    assert len(items) == 31  # 30 days + climatology
    first, clim = items[0], items[-1]
    assert first.url.endswith("/DAILY/TMIN/2024/06/SAMeT_CPTEC_TMIN_20240601.nc")
    assert first.path.as_posix() == "tmin_daily_jun_2024/SAMeT_CPTEC_TMIN_20240601.nc"
    assert clim.url.endswith("/CLIMATOLOGY/MONTHLY_AVERAGE/TMIN/SAMeT_CPTEC_TMIN_mean_jun.nc")
    assert clim.path.as_posix() == "SAMeT_CPTEC_TMIN_mean_jun.nc"
    assert len(download_module.plan("tmax", date(2024, 2, 1))) == 30  # leap year


def test_default_plan_matches_make_figures(download_module):
    from conftest import load_script

    make_figures = load_script("make_figures")
    needed = {f.daily_dir for f in make_figures.FIGURES} | {
        f.climatology for f in make_figures.FIGURES
    }
    planned = set()
    for variable, month in download_module.FIGURE_DATA:
        for item in download_module.plan(variable, download_module.parse_month(month)):
            planned.add(item.path.parts[0])
    assert needed <= planned


def test_fetch_downloads_then_skips(tmp_path, download_module):
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        return FakeResponse(b"netcdf")

    dest = tmp_path / "sub" / "file.nc"
    assert download_module.fetch("https://x/file.nc", dest, opener=opener) is True
    assert dest.read_bytes() == b"netcdf"
    assert download_module.fetch("https://x/file.nc", dest, opener=opener) is False
    assert calls == ["https://x/file.nc"]
    assert not list(tmp_path.rglob("*.part"))


def test_missing_file_gives_clear_error(tmp_path, download_module):
    def opener(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)

    with pytest.raises(download_module.DownloadError, match="Not found on the server"):
        download_module.fetch("https://x/missing.nc", tmp_path / "m.nc", opener=opener)
    assert not (tmp_path / "m.nc").exists()


def test_main_dry_run_and_argument_check(capsys, download_module):
    assert download_module.main(["--dry-run", "--variable", "tmin", "--months", "2024-07"]) == 0
    out = capsys.readouterr().out
    assert "SAMeT_CPTEC_TMIN_20240731.nc" in out
    assert download_module.main(["--variable", "tmin"]) == 2
    with pytest.raises(SystemExit):
        download_module.main(["--variable", "tmin", "--months", "2024/07"])


def test_network_is_blocked_in_tests():
    with pytest.raises(RuntimeError, match="must not use the network"):
        socket.create_connection(("ftp.cptec.inpe.br", 443))


class SizedResponse(FakeResponse):
    """A response that announces ``size`` bytes in Content-Length (whatever it sends)."""

    def __init__(self, body, size):
        super().__init__(body)
        self.headers = {"Content-Length": str(size)}


def test_truncated_download_is_retried_and_never_kept(tmp_path, monkeypatch, download_module):
    monkeypatch.setattr(download_module.time, "sleep", lambda seconds: None)
    answers = [SizedResponse(b"DATA", 10), SizedResponse(b"DATA-whole", 10)]
    dest = tmp_path / "file.bin"
    opener = lambda request, timeout: answers.pop(0)  # noqa: E731
    assert download_module.fetch("https://x/file.bin", dest, opener=opener) is True
    assert dest.read_bytes() == b"DATA-whole" and not answers

    always_short = lambda request, timeout: SizedResponse(b"DATA", 10)  # noqa: E731
    with pytest.raises(download_module.DownloadError, match="received 4 of 10 bytes"):
        download_module.fetch("https://x/b.bin", tmp_path / "b.bin", opener=always_short)
    assert list(tmp_path.iterdir()) == [dest]  # no truncated file, no .part left behind


def test_incomplete_chunked_response_is_retried(tmp_path, monkeypatch, download_module):
    import http.client

    monkeypatch.setattr(download_module.time, "sleep", lambda seconds: None)

    class Broken(FakeResponse):
        def read(self, *args):
            raise http.client.IncompleteRead(b"DA", 8)

    answers = [Broken(b""), FakeResponse(b"DATA")]
    dest = tmp_path / "file.bin"
    opener = lambda request, timeout: answers.pop(0)  # noqa: E731
    assert download_module.fetch("https://x/file.bin", dest, opener=opener) is True
    assert dest.read_bytes() == b"DATA"
