import os
import argparse
from pathlib import Path

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched {filepath}")

def main():
    # 1. fetch_weather.py
    fetch_replacements = [
        ("TARGET_STATIONS = [", """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

TARGET_STATIONS_MUMBAI = ["""),
        ("]\n\nAQI_DATA_PATH = \"data/raw/aqi.csv\"", """]

TARGET_STATIONS_DELHI = [
    {"full_name": "Anand Vihar", "latitude": 28.6469, "longitude": 77.3159},
    {"full_name": "Bawana", "latitude": 28.7997, "longitude": 77.0396},
    {"full_name": "Dwarka Sector 8", "latitude": 28.5710, "longitude": 77.0719},
    {"full_name": "Jahangirpuri", "latitude": 28.7328, "longitude": 77.1706},
    {"full_name": "Jawaharlal Nehru Stadium", "latitude": 28.5818, "longitude": 77.2343},
    {"full_name": "Mundka", "latitude": 28.6836, "longitude": 77.0149},
    {"full_name": "Okhla Phase II", "latitude": 28.5307, "longitude": 77.2736},
    {"full_name": "RK Puram", "latitude": 28.5638, "longitude": 77.1869}
]

TARGET_STATIONS = TARGET_STATIONS_MUMBAI if CITY == 'mumbai' else TARGET_STATIONS_DELHI

AQI_DATA_PATH = "data/raw/aqi.csv"
"""),
        ("OUTPUT_FILE = os.path.join(OUTPUT_DIR, \"weather_daily.csv\")", "OUTPUT_FILE = os.path.join(OUTPUT_DIR, f\"weather_daily_{CITY}.csv\" if CITY != 'mumbai' else \"weather_daily.csv\")")
    ]
    replace_in_file("c:/Weathermodel/script/fetch_weather.py", fetch_replacements)

    # 2. build_dataset.py
    build_replacements = [
        ("OUTPUT_DATASET_PATH = PROCESSED_DIR / \"training_dataset.csv\"", """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

if CITY == 'mumbai':
    AQI_RAW_PATH = Path("data/raw/aqicn_consolidated.csv")
    WEATHER_RAW_PATH = Path("data/raw/weather_daily.csv")
    OUTPUT_DATASET_PATH = PROCESSED_DIR / "training_dataset.csv"
else:
    AQI_RAW_PATH = Path("data/raw/india_air_quality_consolidated.csv")
    WEATHER_RAW_PATH = Path(f"data/raw/weather_daily_{CITY}.csv")
    OUTPUT_DATASET_PATH = PROCESSED_DIR / f"{CITY}_training_dataset.csv"
"""),
        ("AQI_RAW_PATH = Path(\"data/raw/aqicn_consolidated.csv\")\nWEATHER_RAW_PATH = Path(\"data/raw/weather_daily.csv\")\nPROCESSED_DIR = Path(\"data/processed\")\n", "PROCESSED_DIR = Path(\"data/processed\")\n"),
        ("df_aqi = pd.read_csv(AQI_RAW_PATH)", """df_aqi = pd.read_csv(AQI_RAW_PATH)
    if CITY == 'delhi':
        df_aqi = df_aqi[df_aqi['city'] == 'Delhi'].copy()
        df_aqi = df_aqi.rename(columns={'location': 'station'})
        # ensure columns match expected format
"""),
    ]
    replace_in_file("c:/Weathermodel/script/build_dataset.py", build_replacements)

    # 3. feature_engineering.py
    fe_replacements = [
        ("INPUT_FILE = Path(\"data/processed/training_dataset.csv\")\nOUTPUT_FILE = Path(\"data/processed/training_features.csv\")", """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

if CITY == 'mumbai':
    INPUT_FILE = Path("data/processed/training_dataset.csv")
    OUTPUT_FILE = Path("data/processed/training_features.csv")
else:
    INPUT_FILE = Path(f"data/processed/{CITY}_training_dataset.csv")
    OUTPUT_FILE = Path(f"data/processed/{CITY}_training_features.csv")
""")
    ]
    replace_in_file("c:/Weathermodel/script/feature_engineering.py", fe_replacements)

    # 4. feature_validation.py
    fv_replacements = [
        ("INPUT_FILE = Path(\"data/processed/training_features.csv\")", """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

if CITY == 'mumbai':
    INPUT_FILE = Path("data/processed/training_features.csv")
else:
    INPUT_FILE = Path(f"data/processed/{CITY}_training_features.csv")
""")
    ]
    replace_in_file("c:/Weathermodel/script/feature_validation.py", fv_replacements)

    # 5. train_multi_horizon.py
    train_replacements = [
        ("INPUT_FILE = Path(\"data/processed/training_features.csv\")\nMODELS_DIR = Path(\"models/2026\")\nREPORTS_DIR = Path(\"reports/figures\")", """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

if CITY == 'mumbai':
    INPUT_FILE = Path("data/processed/training_features.csv")
    MODELS_DIR = Path("models/mumbai")
    REPORTS_DIR = Path("reports/figures")
else:
    INPUT_FILE = Path(f"data/processed/{CITY}_training_features.csv")
    MODELS_DIR = Path(f"models/{CITY}")
    REPORTS_DIR = Path(f"reports/{CITY}")
"""),
        ("MODELS_DIR.mkdir(parents=True, exist_ok=True)", "MODELS_DIR.mkdir(parents=True, exist_ok=True)\n    REPORTS_DIR.mkdir(parents=True, exist_ok=True)")
    ]
    replace_in_file("c:/Weathermodel/script/train_multi_horizon.py", train_replacements)

    # 6. shap_explainer.py
    shap_replacements = [
        ("INPUT_FILE = Path(\"data/processed/training_features.csv\")\nMODELS_DIR = Path(\"models\")\nREPORTS_DIR = Path(\"reports/figures\")", """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

if CITY == 'mumbai':
    INPUT_FILE = Path("data/processed/training_features.csv")
    MODELS_DIR = Path("models/mumbai")
    REPORTS_DIR = Path("reports/figures")
else:
    INPUT_FILE = Path(f"data/processed/{CITY}_training_features.csv")
    MODELS_DIR = Path(f"models/{CITY}")
    REPORTS_DIR = Path(f"reports/{CITY}")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
""")
    ]
    replace_in_file("c:/Weathermodel/script/shap_explainer.py", shap_replacements)

    # 7. generate_demo_cache.py
    demo_replacements = [
        ("DATA_FILE = Path(\"data/processed/training_features.csv\")\nDEMO_DIR = Path(\"data/demo\")\nMODELS_DIR = Path(\"models\")", """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

if CITY == 'mumbai':
    DATA_FILE = Path("data/processed/training_features.csv")
    DEMO_DIR = Path("data/demo/mumbai")
    MODELS_DIR = Path("models/mumbai")
else:
    DATA_FILE = Path(f"data/processed/{CITY}_training_features.csv")
    DEMO_DIR = Path(f"data/demo/{CITY}")
    MODELS_DIR = Path(f"models/{CITY}")
DEMO_DIR.mkdir(parents=True, exist_ok=True)
""")
    ]
    replace_in_file("c:/Weathermodel/script/generate_demo_cache.py", demo_replacements)

if __name__ == "__main__":
    main()
