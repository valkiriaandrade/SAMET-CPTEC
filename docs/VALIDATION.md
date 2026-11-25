# Refactoring validation

- Python 3.11 on Windows: tests for tmin/tmax, mean minus climatology, missing values,
  grids, file closing and offline map rendering.
- Processed the 31 maximum-temperature files of July 2024 with the matching
  climatology; produced `output/tmax.png` and `output/tmax.nc`.
- Incremental processing: the whole month is never held in memory.
- Editable install of the package and Ruff checks executed.

The provided files do not declare temperature units. The original project's convention
is kept: temperature in °C, or K in both inputs for differences. Diverging units
metadata is rejected. Month, day coverage and reference climatology should be checked
by the user. Missing values propagate per grid cell.

## English translation and figure regeneration (v0.2.0)

- Folders and files renamed to English; code, CLI help, messages, titles and labels
  translated. The anomaly calculation, colour palette (`coolwarm`) and class levels
  (−3 to 3 °C every 0.5 °C) are unchanged.
- `figures/max_temperature_anomaly_jul.png` regenerated with `make figures` from
  `data/tmax_daily_jul_2024/` and `data/SAMeT_CPTEC_TMAX_mean_jul.nc`.
- `figures/min_temperature_anomaly_jun.png` and
  `figures/min_temperature_anomaly_jul_south.png` could not be regenerated: the daily
  minimum-temperature files (and, for July, the TMIN climatology) are not in the
  repository. The original images are kept under their new names.

## Downloaded data and 2000–2023 climatologies (v0.3.0)

- `scripts/download_data.py` (`make data`) downloads from the public CPTEC/INPE server
  (https://ftp.cptec.inpe.br/modelos/tempo/SAMeT/) the daily files and monthly
  climatologies the figures need; downloaded files are git-ignored.
- All maps now use the current CPTEC monthly climatologies (base period **2000–2023**).
  The two older committed climatologies (`SAMeT_CPTEC_TMAX_mean_jul.nc`,
  `SAMeT_CPTEC_TMIN_mean_jun.nc`) were replaced by the 2000–2023 versions (same grid;
  differences up to ~0.4–0.5 °C at individual grid points, mean below 0.05 °C).
- The daily Tmax files for 26–31 July 2024 first committed were **preliminary** versions;
  CPTEC republished those days on 2–3 August 2024 (mean absolute difference ~0.6 °C,
  locally up to 10–18 °C). They were replaced by the current server versions with
  `python scripts/download_data.py --variable tmax --months 2024-07 --overwrite`
  (the other 25 days and the climatology were already identical), and the July Tmax
  figure was regenerated.
- Maps are drawn with filled contours (`contourf`) as in the original scripts.
