# Final Forecasting Model Report

## 1. Dataset Overview
- **Source Data**: `data/Maharasthra.xlsx` (Historical AQI) merged with `Open-Meteo Archive API` (Historical Weather).
- **Date Range**: 2021-08-01 to 2023-07-31 (exactly 2 years).
- **Monitoring Stations**: 8 high-completeness (>60%) monitoring stations located within the Mumbai metropolitan region.
- **Observations**: 5,110 daily records processed.

## 2. Feature Groups Engineered
The model leverages a robust set of 56 features designed to capture both short-term memory and long-term seasonal dynamics:
- **Pollution History**: Short-term lag features (t-1, t-7, t-14) and longer-term rolling window statistics (7-day, 14-day, and 30-day means and standard deviations) for multiple pollutants including PM2.5, PM10, NO2, CO, and O3.
- **Meteorology (Weather)**: Daily mean temperature, relative humidity, total precipitation, and wind speed to account for atmospheric dispersion and accumulation.
- **Calendar Logic**: Day of the week, month, day of the year, and binary weekend indicators to capture human-activity cycles.
- **Cyclical Encoding**: Mathematical sine/cosine transformations applied to all calendar variables to ensure the model correctly understands the continuous nature of time (e.g., December 31st is adjacent to January 1st).

## 3. Validation Methodology
A rigorous, multi-layered validation framework was designed to simulate real-world production deployment and prevent data leakage:
- **Strict Chronological Split**: Data was split strictly through time without random shuffling.
  - *Train (14 months)*: 2021-08-16 to 2022-09-30
  - *Validation (3 months)*: 2022-10-01 to 2022-12-31
  - *Test (7 months)*: 2023-01-01 to 2023-07-28
- **Persistence Baseline**: The model's performance was actively evaluated against a "Persistence Baseline" (the assumption that tomorrow's pollution will equal today's pollution), which serves as a highly competitive benchmark for time-series forecasting.
- **Winter Evaluation**: Because winter generates the highest and most volatile pollution events, a secondary evaluation was isolated exclusively to the peak winter months (January and February) within the Test set to honestly assess capability during extreme conditions.

## 4. Final Performance Metrics

The XGBoost models successfully outperformed the Persistence Baseline across all horizons (24h, 48h, 72h). 

### Overall Test Performance (Jan-Jul 2023)
| Horizon | XGBoost RMSE | Persistence RMSE | Improvement % | XGBoost R² |
|---------|--------------|------------------|---------------|------------|
| **24h** | 14.43        | 15.76            | **+8.43%**    | 0.7712     |
| **48h** | 18.01        | 19.45            | **+7.39%**    | 0.6428     |
| **72h** | 19.61        | 21.63            | **+9.35%**    | 0.5737     |

### Winter-Only Test Performance (Peak Winter: Jan-Feb)
| Horizon | XGBoost RMSE | Persistence RMSE | Improvement % |
|---------|--------------|------------------|---------------|
| **24h** | 16.01        | 16.87            | **+5.11%**    |
| **48h** | 20.75        | 22.47            | **+7.65%**    |
| **72h** | 23.88        | 25.07            | **+4.73%**    |

## 5. Known Limitations
While the forecasting engine is highly performant, it operates with the following known limitations:
- **Extreme Event Volatility**: The absolute error (RMSE) inevitably climbs during the winter months. While the model correctly anticipates the broad upward curve of winter pollution, precisely pinpointing massive, localized spike events remains inherently difficult compared to the stable monsoon baseline.
- **Limited Spatial Coverage**: The model relies entirely on the 8 most complete monitoring stations in Mumbai. Hyper-local, neighborhood-level forecasting is restricted by this geographic sparsity.
- **Lack of Emission Inventories**: The system relies heavily on atmospheric memory and weather to *infer* emissions. It currently lacks direct, dynamic integrations with real-time vehicular traffic flows, live industrial emissions reporting, or sudden localized construction data.
