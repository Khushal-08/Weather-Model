# Urban Air Quality Intelligence Platform: Final Project Report

## 1. PROBLEM STATEMENT & SCOPE
**Original Challenge:** To develop an AI-driven solution for forecasting urban air quality, predicting pollution hotspots, and providing actionable insights for both city administrators and citizens.

**Scope Strategy:**
- **Built:** A complete end-to-end pipeline covering multi-horizon forecasting, AI explainability (SHAP), heuristic source risk estimation, and an LLM-powered multi-lingual citizen advisory system. We successfully scaled the architecture to support a **Multi-City** environment (Mumbai and Delhi) to prove geographic scalability.
- **Not Built (Deliberately Scoped Out):** A rigorous Chemical Mass Balance (CMB) model or chemical transport model (CTM). Given the hackathon timeline and the lack of live public emission inventory APIs in India, we explicitly opted for a heuristic geospatial estimation approach rather than a verified chemical attribution model. Live real-time ingestion pipelines were also substituted with historical archives (2021-2023) to guarantee stable, reproducible evaluation.

## 2. DATA PIPELINE
**Exact Data Sources Integrated & Tested:**
- **Historical Air Quality:** CPCB/MPCB station data accessed via **AQICN** and **OpenAQ** public repositories.
- **Meteorological Data:** **Open-Meteo** (ERA5 reanalysis) for historical weather and wind vectors.
- **Geospatial Context:** **OpenStreetMap (OSMnx)** for road network density and industrial land-use polygons.

**Dataset Characteristics:**
- **Date Range:** 2021-08-01 to 2023-07-31 (exactly 2 years). This range provided exactly two full winter cycles for training and evaluation.
- **Monitoring Stations:** 16 total stations (8 in Mumbai, 8 in Delhi) selected based on strict completeness thresholds (>60% data availability).

**Data Quality Safeguards Implemented:**
- **Leakage Prevention:** Fixed a critical bidirectional backfilling (`bfill`) bug where future pollutant concentrations were accidentally leaking into past missing values.
- **Continuous Date Reindexing:** Enforced strict daily reindexing to guarantee temporal continuity, preventing the model from skipping days and breaking the rolling window logic.
- **Seasonal Train/Test Split:** Addressed a random-split bug by enforcing a strict chronological split to ensure the model was evaluated on unseen future data, exactly simulating real-world deployment.

## 3. FORECASTING MODEL
**Approach:** Multi-Horizon XGBoost Regression (Direct Strategy).
Instead of recursive forecasting (where the model uses its own predictions to predict further into the future, causing compounding errors), we trained three separate, independent XGBoost models for the 24h, 48h, and 72h horizons.

**Feature Engineering:**
- **Pollutant History:** Lag features (t-1, t-7, t-14) and rolling window statistics (7d, 14d, 30d means/stdevs).
- **Calendar Logic:** Cyclical encoding (sine/cosine transformations) of month, day of year, and day of week to accurately represent the continuous nature of time.

**Full Final Validated Performance Table (Mumbai Test Set: Jan-Jul 2023):**

*Overall Test Performance*
| Horizon | XGBoost RMSE | Persistence RMSE | Improvement % | XGBoost R² |
|---------|--------------|------------------|---------------|------------|
| **24h** | 14.43        | 15.76            | **+8.43%**    | 0.7712     |
| **48h** | 18.01        | 19.45            | **+7.39%**    | 0.6428     |
| **72h** | 19.61        | 21.63            | **+9.35%**    | 0.5737     |

*Winter-Only Subset Performance (Peak Winter Volatility: Jan-Feb)*
| Horizon | XGBoost RMSE | Persistence RMSE | Improvement % |
|---------|--------------|------------------|---------------|
| **24h** | 16.01        | 16.87            | **+5.11%**    |
| **48h** | 20.75        | 22.47            | **+7.65%**    |
| **72h** | 23.88        | 25.07            | **+4.73%**    |

**Known Limitation:** Performance naturally degrades at longer horizons (72h) and during winter. Winter causes extreme, sudden pollution spikes driven by temperature inversions that are inherently more difficult to pinpoint exactly compared to the stable monsoon baseline.

## 4. EXPLAINABILITY (SHAP)
**Implementation:** We integrated SHapley Additive exPlanations (SHAP) to unpack the "black box" of the XGBoost predictions, outputting the exact top factors increasing and decreasing pollution for any given prediction.
**Crucial Distinction:** SHAP explains the *mathematical reasoning of the model*, whereas our Source Estimation module attempts to explain the *physical world*. We explicitly separate these.
**Limitation:** SHAP identifies correlation, not causation. If "PM10 Lag 7" is the top increasing factor, it means the model heavily relied on that variable, not necessarily that historical PM10 physically generated today's PM2.5.

## 5. GEOSPATIAL SOURCE RISK ESTIMATION
**Methodology:** We utilized an OSMnx pipeline to extract road infrastructure (primary/trunk/motorways) and industrial polygons (landuse=industrial) within a 5km radius of each station. This static density is dynamically modulated by live Open-Meteo wind vectors (direction and speed) to generate heuristic contribution percentages.

**Explicit Limitation:** This is a heuristic, evidence-based estimation, **NOT a chemical mass balance model or verified emission inventory.** 
**Reasoning:** True source attribution requires localized, bulk-accessible vehicle counting data (VKT) matched with ARAI emission factors, or programmatic API access to CPCB OCEMS (Continuous Emission Monitoring Systems) stack data. Because CPCB OCEMS data is restricted to regulatory compliance portals and SAFAR inventories are only published as static research PDFs, it is impossible to build a live, dynamically verifiable chemical model. The heuristic approach was a deliberate, informed scoping decision.

## 6. CITIZEN ADVISORY SYSTEM
**Methodology:** The system matches the predicted PM2.5 to the statutory CPCB Air Quality Index (AQI) categories (Good, Satisfactory, Moderate, Poor, Very Poor, Severe).
**LLM Constraints:** We utilize Google Gemini strictly as a translation and phrasing engine. The LLM is explicitly grounded with the CPCB category and rigid baseline instructions. It is heavily constrained from generating novel or unverified medical claims.
**Reliability:** The system supports localized translations (English, Hindi, Marathi). If the LLM generation fails (e.g., due to parsing errors or quota limits, which was actively tested and caught during development), the system gracefully falls back to a hardcoded standard English guidance dictionary.

## 7. DASHBOARD & USER EXPERIENCE
**Views:**
- **Administrator View:** High-level tactical dashboard featuring the geospatial map, AI Driver Analysis (SHAP), Source Estimation donut charts, and an automated Field Dispatch Ticket generator.
- **Citizen View:** Hyperlocal, simplified interface focusing on the personalized health advisory, massive AQI indicator, and localized translation options.

**Execution Modes:**
- **Live Mode:** Runs the full machine learning, SHAP, and LLM generation pipeline in real-time.
- **Demo Mode:** Loads precomputed intelligence JSON caches. Built deliberately to ensure absolute reliability, zero latency, and zero API quota issues during a live hackathon presentation.

**Concept Features:** The "Automated Push Alert" SMS preview and the "Subscribe to Alerts" button are UI prototypes/concept demonstrations intended to show future integration potential, not active live integrations.

## 8. KNOWN LIMITATIONS
- **Heuristic Source Attribution:** As explicitly noted above, the attribution is based on geospatial proxies, not chemical transport physics. Accepted as a hackathon tradeoff due to the lack of live emission APIs in India.
- **Historical Execution:** The model was trained and evaluated on a static 2021-2023 dataset rather than a live-connected 2024 data feed, ensuring stable, auditable evaluation metrics.
- **Station-Level Resolution:** Predictions are restricted to the precise coordinates of the 16 monitoring stations, rather than an interpolated 1km x 1km continuous city grid.
- **Streamlit Prototyping:** The dashboard is built on Streamlit, which is exceptional for rapid AI prototyping but lacks the concurrent user scalability of a production React/FastAPI architecture.

## 9. ARCHITECTURE DIAGRAM

```text
[ Data Ingestion ]
      |-- AQICN / OpenAQ (Historical Pollutants)
      |-- Open-Meteo (ERA5 Historical Weather)
      |-- OpenStreetMap (Infrastructure Density)
      v
[ Feature Engineering ]
      |-- Bidirectional Leakage Prevention
      |-- Rolling Windows & Lags
      |-- Cyclical Calendar Encoding
      v
[ AI Forecasting Engine ]
      |-- XGBoost 24h Model
      |-- XGBoost 48h Model
      |-- XGBoost 72h Model
      v
[ Explainability & Attribution ]
      |-- SHAP Explainer (Model Logic)
      |-- Geospatial Heuristic Engine (Physical Proxies + Wind)
      v
[ GenAI Advisory ]
      |-- Google Gemini LLM (Translation & Phrasing)
      |-- CPCB Grounding / Fallback Handlers
      v
[ Streamlit UI Presentation ]
      |-- Administrator Dashboard (Tickets, Maps, SHAP)
      |-- Citizen View (Health Advisories, Multi-Lingual)
```

## 10. TECH STACK SUMMARY
- **Core ML/Data:** Python 3.11, Pandas, NumPy, Scikit-learn, XGBoost
- **Explainability:** SHAP
- **Geospatial:** OSMnx, Folium, streamlit-folium
- **Visualization:** Plotly, Streamlit
- **Generative AI:** Google Generative AI (Gemini)
- **Data APIs:** Open-Meteo API, Overpass API (OSM)
