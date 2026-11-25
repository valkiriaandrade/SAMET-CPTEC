# SAMET-CPTEC

This repository contains scripts for visualising temperature data from INPE/CPTEC's SAMeT product. This product combines observed data with the ERA5 reanalysis, correcting the temperature field with an estimated lapse rate.

## Description

The SAMET-CPTEC project focuses on visualising temperature anomaly data using CPTEC/INPE's SAMeT product.

## Repository structure

- `Scripts/`: scripts used to process and analyse the data.
- `Dados/`: raw and processed data.
- `Figuras/`: figures generated from the data.

## Prerequisites

Before running the scripts, you will need to install the following Python libraries:

- numpy
- geopandas
- matplotlib
- pygrib
- cartopy
- xarray
- netCDF4

## Images

### Figure 1: Example of a monthly minimum temperature anomaly

![Monthly minimum temperature anomaly](../Figuras/anomalia_temperatura_minima_jun.png)

### Figure 2: Example of a monthly maximum temperature anomaly

![Monthly maximum temperature anomaly](../Figuras/anomalia_temperatura_maxima_jul.png)

### Figure 3: Example of a monthly minimum temperature anomaly - South

![Monthly minimum temperature anomaly - South](../Figuras/anomalia_temperatura_minima_jul_Sul.png)

## How to use

1. Clone this repository:
    ```bash
    git clone https://github.com/valkiriaandrade/SAMET-CPTEC.git
    ```

2. Go to the project folder:
    ```bash
    cd SAMET-CPTEC
    ```

3. Run the scripts as needed.

## Contributing

Contributions are welcome! Feel free to open issues and pull requests.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
