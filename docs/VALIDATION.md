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
