# Urban Air Quality Intelligence Platform
*Hackathon Pitch, Engineering Overview, and Final Project Report*

---

## 1. Executive Summary

**The Problem:** Urban air quality is volatile and inherently invisible. Existing platforms merely display static numerical indices (AQI), leaving city administrators without actionable targets for enforcement and leaving citizens without personalized, localized health guidance.
**The Solution:** An end-to-end AI platform that bridges the gap between raw data and civic action. The system ingests environmental data, forecasts pollution up to 72 hours ahead, unpacks predictions using Explainable AI (SHAP), heuristically estimates physical pollution sources, and generates multi-lingual, LLM-powered health advisories.
**AI Technologies Used:** XGBoost (Direct Multi-Horizon Regression), SHAP (Model Explainability), and Google Gemini (Constrained LLM for Translation/Advisories).
**Cities Supported:** Scaled successfully to a Multi-City architecture covering 16 stations across Mumbai and Delhi.
**Key Results:** The forecasting engine successfully beat the highly competitive Persistence Baseline (+8.43% improvement at 24h). The platform features an ultra-reliable "Demo Mode" with zero latency and robust API fallback handlers.
**Business Impact:** Transforms reactive pollution monitoring into proactive management. Administrators receive formal, automated "Environmental Field Dispatch Tickets," while citizens receive localized health warnings via mock WhatsApp/SMS integrations.
**Why It's Innovative:** It enforces strict boundaries on GenAI. Rather than a free-form chatbot, the LLM is strictly constrained by statutory CPCB health guidelines, acting solely as a civic translation engine.

---

## 2. Engineering Journey & Major Technical Challenges

Building a robust time-series forecasting model for environmental data revealed significant real-world engineering challenges:
- **The Seasonal Bias Discovery:** Initially, the model was trained on one year of data. Validation revealed catastrophic performance on 48h/72h horizons because the model lacked sufficient "seasonal memory" to anticipate extreme winter pollution spikes caused by temperature inversions. 
- **Dataset Reconstruction:** To solve this, we discarded the initial dataset and rebuilt the pipeline to ingest a full two-year historical archive (2021–2023), ensuring the model trained on two complete monsoon-winter cycles.
- **Leakage Prevention:** During feature engineering, we discovered that Pandas' default `bfill` (backward fill) was accidentally leaking future pollutant concentrations into past missing values—a fatal flaw in time-series forecasting. We strictly replaced this with forward-only interpolation.
- **Multi-City Expansion:** The initial codebase relied on hardcoded Mumbai paths. We successfully undertook a massive architectural refactoring to build a scalable, dynamic parameter-passing system, expanding the platform to Delhi without duplicating code.

---

## 3. Data Validation & Safeguards

To ensure enterprise-grade reliability, the Data Pipeline incorporates rigorous safeguards:
- **Negative Value Handling:** Hardware sensor errors often report negative PM2.5 values. These are explicitly caught and converted to `NaN` prior to interpolation.
- **Continuous Date Reindexing:** We enforced `df.asfreq('D')` to explicitly expose hidden missing days in the CPCB data, preventing the rolling window calculations from silently bridging massive temporal gaps.
- **Forward-Only Interpolation:** Missing data is filled using `ffill()` to absolutely guarantee no future data leaks into the past.
- **Weather Alignment Validation:** Explicit checks ensure the Open-Meteo ERA5 reanalysis weather data perfectly aligns temporally with the AQI observation dates.
- **Station Completeness Threshold:** Stations with less than 60% data coverage were programmatically dropped from the training cohort to prevent the model from learning interpolated noise.
- **Seasonal Validation:** The chronological train/test split was verified to ensure the testing dataset contained the peak January/February winter period, ensuring the model was tested on the hardest possible conditions.

---

## 4. Model Design Decisions

Every architectural choice was deliberately made to maximize reliability and interpretability:
- **Why XGBoost?** Atmospheric dynamics (like temperature inversions trapping pollutants) are highly non-linear. XGBoost handles these non-linear feature interactions natively, is significantly faster to train than Deep Learning, and is highly interpretable via SHAP.
- **Why not LSTMs?** While Deep Learning is powerful for sequence modeling, LSTMs require massive datasets and are highly prone to overfitting on sparse, station-level data. XGBoost, augmented with engineered temporal lag features, achieves competitive memory retention with a fraction of the computational overhead.
- **Why Direct Multi-Horizon vs. Recursive Forecasting?** A recursive approach (predicting t+1, then feeding it back in to predict t+2) compounds error exponentially. We utilized a Direct Strategy: training three entirely independent models for 24h, 48h, and 72h targets, isolating the error variance for each horizon.
- **Why a Persistence Baseline?** The assumption that "tomorrow's air quality will be exactly the same as today's" is notoriously difficult to beat in meteorology. Beating the persistence baseline proves the model has actually learned atmospheric physics, rather than just exploiting auto-correlation.
- **Why Chronological Splitting?** Randomly shuffling time-series data using standard `train_test_split` leaks future context into the training set. We enforced a strict chronological split to simulate deploying the model into a true, unknown future.

---

## 5. Complete Performance Section

The models were rigorously audited. The primary benchmark evaluation was conducted on the Mumbai testing cohort (January 2023 - July 2023). Delhi models were successfully integrated into the multi-city pipeline utilizing identical architectures.

**Mumbai: Overall Test Performance (Jan-Jul 2023)**
| Horizon | XGBoost RMSE | Persistence RMSE | Improvement % | XGBoost R² |
|---------|--------------|------------------|---------------|------------|
| **24h** | 14.43        | 15.76            | **+8.43%**    | 0.7712     |
| **48h** | 18.01        | 19.45            | **+7.39%**    | 0.6428     |
| **72h** | 19.61        | 21.63            | **+9.35%**    | 0.5737     |

**Mumbai: Winter-Only Test Performance (Peak Volatility: Jan-Feb)**
| Horizon | XGBoost RMSE | Persistence RMSE | Improvement % |
|---------|--------------|------------------|---------------|
| **24h** | 16.01        | 16.87            | **+5.11%**    |
| **48h** | 20.75        | 22.47            | **+7.65%**    |
| **72h** | 23.88        | 25.07            | **+4.73%**    |

*Interpretation:* The XGBoost models successfully outperformed the Persistence Baseline across all horizons. As expected, absolute error (RMSE) climbs during the volatile winter months; however, the model still outperforms the baseline, proving its ability to anticipate winter accumulation events.

---

## 6. Explainability vs Source Attribution

We explicitly architected two entirely separate systems to avoid conflating statistical correlation with physical causation:
1. **Explainability (SHAP):** Answers the question, *"Why did the AI model make this prediction?"* It unpacks the XGBoost mathematics, revealing which engineered features (e.g., PM10 Lag 7) pushed the numerical prediction higher or lower.
2. **Source Attribution (Geospatial Heuristics):** Answers the question, *"What is the likely physical source of the pollution?"* 
**Explicit Limitation:** The Source Attribution engine is an **evidence-based heuristic model**, NOT a Chemical Mass Balance (CMB) model. Because verified emission inventories (like SAFAR) are published as static PDFs and CPCB stack emissions are locked behind compliance portals in India, a live chemical model is currently impossible for third-party platforms. Our heuristic gracefully circumvents this by using static OSM industrial/road density polygons scaled dynamically by real-time Open-Meteo wind vectors.

---

## 7. Scalable Multi-City Architecture

A major strength of the platform is its horizontal scalability. The architecture is decoupled from any single geographic location:
- **City Registry:** A dynamic UI selector routes traffic between Mumbai and Delhi.
- **Independent Pipelines:** The system maintains strictly isolated weather datasets, engineered feature datasets, trained XGBoost weights, and SHAP explainers for each city.
- **Isolated Caches:** "Demo Mode" JSON caches are siloed by city and station.
- **Scalability:** Adding a new city (e.g., Bangalore) does not require rewriting the system; it simply requires adding the historical CSV and running the automated training scripts.

---

## 8. System Architecture Diagrams

**Data & Inference Pipeline:**
```text
[ Data Ingestion ]
      ├── AQICN / OpenAQ (Historical Pollutants)
      ├── Open-Meteo (ERA5 Historical Weather)
      └── OpenStreetMap (Infrastructure Density)
              │
[ Feature Engineering ] (Leakage Prevention, Rolling Windows, Lags)
              │
[ AI Forecasting Engine ] (Independent 24h, 48h, 72h XGBoost Models)
              │
[ Analytics Split ]
      ├── SHAP Explainer (Model Mathematical Logic)
      └── Geospatial Heuristic Engine (Physical Proxies + Wind)
              │
[ GenAI Advisory ] (Gemini LLM + CPCB Grounding Handlers)
              │
[ Streamlit UI ] (Administrator Dashboard & Citizen View)
```

**Multi-City Routing Architecture:**
```text
[ Dashboard Request ] ──> [ City Selector State ]
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
        [ Mumbai Registry ]              [ Delhi Registry ]
        - Mumbai Models                  - Delhi Models
        - Mumbai SHAP                    - Delhi SHAP
        - Mumbai Caches                  - Delhi Caches
```

---

## 9. Enterprise Readiness

The platform incorporates numerous production-ready design patterns:
- **Live Mode vs. Demo Mode:** "Live Mode" executes the full ML/LLM pipeline. "Demo Mode" serves precomputed JSON intelligence caches, guaranteeing zero-latency, highly reliable presentations immune to API quotas or network drops.
- **Session State Caching:** Streamlit's `session_state` is utilized to cache heavy map renders and selections across tab changes.
- **Graceful Degradation & API Fallback:** If the LLM API drops or hits a quota limit, the system gracefully catches the exception and falls back to a hardcoded standard CPCB dictionary without crashing the UI.
- **Modular Code Architecture:** Script functionality is decoupled (e.g., `train_multi_horizon.py` is entirely distinct from `predict_pipeline.py`).
- **Environment Variable Management:** Sensitive API keys (Gemini) are securely managed via standard `.env` patterns.

---

## 10. Security & Guardrails

Generative AI is strictly constrained to prevent hallucinations:
- **Anti-Hallucination Prompt Grounding:** The Gemini LLM is never allowed to interpret raw numbers. The Python backend evaluates the PM2.5, assigns the statutory CPCB category (e.g., "Very Poor"), and injects that hardcoded category into the prompt.
- **No Medical Diagnosis:** The prompt explicitly forbids the generation of novel medical advice, constraining the LLM to act solely as a translation and phrasing engine for established civic guidelines.
- **Read-Only Inference Pipeline:** The dashboard has zero write-access to the underlying models or historical databases, ensuring strict data integrity.

---

## 11. The "Wow" Factors & UI Features

- **Environmental Dispatch Ticket:** Administrators can generate a formal, ASCII-bordered "Field Dispatch Work Order" in plain text, bridging the gap between a dashboard and actual bureaucratic action.
- **Dynamic SHAP Cards:** Complex model explainability is translated into beautiful, distinct (📈 Increasing vs 📉 Decreasing) cards, showing impacts in exact µg/m³.
- **Interactive Geospatial Map:** A Folium map visually anchors the data, highlighting the station's 5km radius.
- **Source Attribution Donut Chart:** A Plotly chart visually breaks down the heuristic risks (Traffic vs. Industry) based on wind flow.
- **Multi-Language Advisory:** Citizens receive localized advice (English, Hindi, Marathi) with conceptual WhatsApp/SMS push-alert integrations.
- **Glassmorphism UI:** Advanced custom CSS injections bypass Streamlit defaults to create a modern, dark-mode, premium aesthetic.

---

## 12. Business Value

- **For Government & Administrators:** Replaces reactive complaining with proactive, targeted enforcement. By identifying that "Industry upwind" is the primary risk driver today, field teams can be dispatched efficiently.
- **For Citizens:** Empowers sensitive groups (asthmatics, elderly) to plan their outdoor exposure 72 hours in advance via localized, easily understandable health alerts.
- **For Researchers & Smart Cities:** Provides an open, highly modular AI architecture ready to be integrated into broader Smart City command centers.

---

## 13. Honest Limitations

We explicitly acknowledge the following conscious engineering tradeoffs made to fit the hackathon scope:
- **Historical Evaluation:** The platform evaluates against a static 2021-2023 dataset rather than a live 2024 CPCB stream. This was a deliberate choice to guarantee stable, reproducible evaluation metrics for judging.
- **Heuristic Source Attribution:** Lacking live bulk-access to CEMS/SAFAR emission inventories, we rely on geospatial proxies. It is not a verified chemical transport model.
- **Station-Level Resolution:** Forecasts are pin-pointed to specific monitoring stations, rather than a continuous 1km x 1km interpolated city grid.
- **Streamlit Prototype:** While excellent for AI prototyping, Streamlit is not designed for massive concurrent-user production deployment.

---

## 14. Future Roadmap

- **Live Data Ingestion:** Direct API integration with the national CPCB live streaming portal.
- **Satellite Imagery:** Integrating Sentinel-5P NO2/Aerosol data for continuous spatial coverage between stations.
- **Advanced Modeling:** Transitioning from XGBoost to Transformer-based time-series models (e.g., Temporal Fusion Transformers).
- **Chemical Transport Models (CTM):** Replacing the heuristic attribution engine with a true CMAQ/WRF-Chem integration.
- **Production UI:** Migrating the frontend to Next.js/React and the backend to FastAPI.

---

## 15. Comparative Feature Table

| Capability | Standard AQI Apps | Our Intelligence Platform |
| :--- | :--- | :--- |
| **Current AQI Monitoring** | ✅ Yes | ✅ Yes |
| **Multi-Horizon Forecasting** | ❌ No (Usually basic weather) | ✅ Yes (24h/48h/72h XGBoost) |
| **Explainable AI (SHAP)** | ❌ No | ✅ Yes (Driver quantification) |
| **Source Estimation** | ❌ No | ✅ Yes (Geospatial + Wind heuristics) |
| **Administrator Tools** | ❌ No | ✅ Yes (Field Dispatch Tickets) |
| **Generative AI Health Advisories** | ❌ No | ✅ Yes (Multi-lingual, CPCB-grounded) |
| **Scalable Multi-City Architecture** | 🟡 Partial | ✅ Yes (Independent registries) |
