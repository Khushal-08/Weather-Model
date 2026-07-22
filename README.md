# 🌬️ Air Quality Intelligence System (AQIS)

<div align="center">

### AI-Powered Multi-City Air Quality Forecasting & Decision Support Platform

**Predict • Explain • Attribute • Act**

<br>
🌐 <b><a href="https://weather-model-g9pvryhj7tsfr5xvmgqpxi.streamlit.app/">Live Demo: Streamlit Community Cloud</a></b>
<br><br>

![Python](https://img.shields.io/badge/Python-3.11-blue)
![XGBoost](https://img.shields.io/badge/XGBoost-Machine%20Learning-green)
![SHAP](https://img.shields.io/badge/Explainability-SHAP-orange)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![Status](https://img.shields.io/badge/Status-Hackathon-success)

</div>

---

## 📖 Overview

Air pollution is one of the world's most pressing environmental challenges. While existing air quality dashboards primarily display current AQI values, they often fail to answer the questions that matter most:

- **What will happen next?**
- **Why is pollution increasing?**
- **How confident is the prediction?**
- **What action should authorities take?**
- **How can citizens protect themselves?**

The **Air Quality Intelligence System (AQIS)** is an AI-powered decision-support platform designed to bridge this gap.

Built for city administrators and citizens alike, this platform combines **machine learning**, **geospatial intelligence**, **explainable AI**, and **generative AI** into a single solution capable of forecasting PM2.5 concentrations, estimating likely pollution contributors, generating operational recommendations for city administrators, and providing multilingual health advisories for citizens.

The platform currently demonstrates scalability through **multi-city support**, including **Mumbai** and **Delhi**.

---

## ✨ Project Highlights

- 🌆 **Multi-City Architecture** (Mumbai & Delhi)
- 🤖 **AI-powered PM2.5 Forecasting** (24h, 48h & 72h)
- 📈 **Explainable AI** using SHAP
- 🗺️ **Geospatial Pollution Source Estimation**
- 🏛️ **Administrator Decision Support Dashboard**
- 👨‍👩‍👧 **Citizen Health Advisory Portal**
- 🌍 **Multilingual AI Recommendations** (English, Hindi & Marathi)
- 📄 **AI-generated Environmental Response Orders**
- ⚡ **Live Mode & Demo Mode**
- 🎨 **Premium Interactive Dashboard**

---

## 🚀 Key Features

### 🔮 Multi-Horizon Forecasting
AQIS employs tuned **XGBoost regression models** trained on extensive historical pollution and meteorological datasets to forecast PM2.5 concentrations for **24 Hours**, **48 Hours**, and **72 Hours**. The models are trained using chronological validation and consistently outperform standard persistence baselines.

### 📊 Explainable AI (SHAP)
Instead of treating machine learning as a black box, AQIS explains every prediction using **SHAP (SHapley Additive Explanations)**. The dashboard highlights factors increasing and reducing pollution, providing full transparency into exactly which meteorological factors (e.g., wind stagnation, temperature drops) are driving the forecast.

### 🗺️ Geospatial Source Estimation
Using OpenStreetMap (OSMnx), road network density, industrial land use, and meteorological conditions, AQIS maps out city infrastructure to pinpoint whether traffic, industry, or construction is the primary driver of localized pollution spikes.
> **Note:** Source attribution is an evidence-based heuristic geospatial estimation, not a chemical mass balance model.

### 🏛️ Administrator Command Center
Designed for city officials and environmental agencies. Features an "AI Executive Briefing" and one-click generation of formal **Environmental Response Orders** (dispatch tickets) outlining mandated field interventions based on the AI's real-time causal analysis.

### 👨‍👩‍👧 Citizen Health Portal
Using **Google Gemini LLM**, the system automatically translates complex AQI metrics into highly localized, easily readable health advisories. We currently support **English, Hindi, and Marathi**, ensuring critical health warnings reach vulnerable populations in their native language.

### ⚡ Live Mode & Demo Mode
- **Demo Mode:** Uses pre-computed JSON caches for instantaneous demonstrations and pitching without API dependencies.
- **Live Mode:** Dynamically fetches real-time meteorological data from **Open-Meteo** and live pollution data from **OpenAQ / Data.gov.in** for real-world inferences on the fly.

---

## 📈 Model Performance

The forecasting models were evaluated using chronological train-test splits and compared against a Persistence Baseline (which assumes tomorrow's pollution will be exactly the same as today's).

| Forecast Horizon | Performance |
|-----------------|-------------|
| **24 Hours** | Consistently outperforms persistence baseline |
| **48 Hours** | Improved medium-term forecasting |
| **72 Hours** | Maintains predictive capability while accounting for increasing uncertainty |

*Winter-specific evaluations were also performed to validate performance during seasonal pollution spikes when thermal inversions trap pollutants.*

---

## 🏗️ System Architecture

```text
              Air Quality Data
             (OpenAQ / Data.gov)
                      +
            Weather Data (Open-Meteo)
                      +
      Geospatial Infrastructure (OSM)
                      │
                      ▼
          Feature Engineering Pipeline
                      │
                      ▼
        XGBoost Multi-Horizon Models
         (24h • 48h • 72h Forecasts)
                      │
      ┌───────────────┼────────────────┐
      │               │                │
      ▼               ▼                ▼
   SHAP         Source Estimation   Gemini LLM
      │               │                │
      └───────────────┼────────────────┘
                      ▼
        Streamlit Intelligence Dashboard
          ├── Administrator Portal
          └── Citizen Portal
```

---

## 🛠️ Technology Stack

*   **Frontend:** [Streamlit](https://streamlit.io/) (with custom CSS/HTML for a premium UI)
*   **Data Processing:** Python, Pandas, NumPy
*   **Machine Learning:** XGBoost, Scikit-learn
*   **Explainability:** SHAP (SHapley Additive exPlanations)
*   **Geospatial & Visualization:** Plotly, Folium, OSMnx (OpenStreetMap)
*   **APIs:** Google Gemini API, Open-Meteo API, OpenAQ API, Data.gov.in

---

## 📂 Project Structure

```text
📦 Weathermodel
 ┣ 📂 pages/                      # Streamlit multipage application
 ┃ ┣ 📜 1_Administrator.py        # Official dashboard & dispatch tickets
 ┃ ┣ 📜 2_Citizen.py              # Multilingual health advisories
 ┃ ┗ 📜 3_Model_Validation.py     # RMSE metrics & SHAP charts
 ┣ 📂 script/                     # Data pipelines & backend logic
 ┃ ┣ 📜 fetch_weather.py
 ┃ ┣ 📜 fetch_aqi_data_gov.py
 ┃ ┣ 📜 predict_pipeline.py
 ┃ ┗ 📜 ...
 ┣ 📂 data/                       # Raw & processed datasets
 ┣ 📂 models/                     # Pickled/joblib XGBoost models
 ┣ 📂 reports/                    # Generated figures and project scripts
 ┣ 📜 dashboard.py                # Main Streamlit entry point
 ┣ 📜 utils_charts.py             # Custom Plotly configurations
 ┣ 📜 utils_ui.py                 # Custom CSS and styling logic
 ┣ 📜 requirements.txt            # Python dependencies
 ┗ 📜 README.md                   # You are here
```

---

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Khushal-08/Weather-Model.git
   cd Weather-Model
   ```

2. **Install Dependencies:**
   Ensure you have Python 3.9+ installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.streamlit/secrets.toml` file (or a `.env` file locally) and add your API keys:
   ```toml
   DATAGOV_API_KEY = "your_key_here"
   OPENAQ_API_KEY = "your_key_here"
   GEMINI_API_KEY = "your_key_here"
   ```

4. **Run the Dashboard:**
   Launch the Streamlit server locally:
   ```bash
   streamlit run dashboard.py
   ```
   *The app will automatically open in your default browser at `http://localhost:8501`.*

---

## 🎯 Future Improvements

- Satellite imagery integration
- Continuous city-wide pollution heatmaps
- IoT sensor integration
- Push notifications
- Mobile application
- FastAPI + Next.js production deployment
- Additional city support

---

## 📜 Data Sources

- CPCB / MPCB Monitoring Stations
- AQICN
- OpenAQ
- Open-Meteo
- OpenStreetMap

---

## 📄 License & Team

Developed as part of a hackathon project for educational and demonstration purposes.

Built with ❤️ to demonstrate how AI can support smarter, more proactive urban environmental management.
