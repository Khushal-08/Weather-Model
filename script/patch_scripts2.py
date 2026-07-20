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
    # 8. predict_pipeline.py
    predict_replacements = [
        ("MODELS_DIR = Path(\"models\")\nDATA_FILE = Path(\"data/processed/training_features.csv\")", """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

if CITY == 'mumbai':
    MODELS_DIR = Path("models/mumbai")
    DATA_FILE = Path("data/processed/training_features.csv")
else:
    MODELS_DIR = Path(f"models/{CITY}")
    DATA_FILE = Path(f"data/processed/{CITY}_training_features.csv")
""")
    ]
    replace_in_file("c:/Weathermodel/script/predict_pipeline.py", predict_replacements)

    # 9. dashboard.py
    dashboard_replacements = [
        ("DEMO_DIR = Path(\"data/demo\")", """
CITY = st.sidebar.selectbox("Select City", ["Mumbai", "Delhi"]).lower()

if CITY == 'mumbai':
    DEMO_DIR = Path("data/demo/mumbai")
else:
    DEMO_DIR = Path(f"data/demo/{CITY}")
"""),
        ("station_files = list(DEMO_DIR.glob(\"*.json\"))", "station_files = list(DEMO_DIR.glob(\"*.json\"))\n    if not station_files:\n        st.warning(f\"No station data found for {CITY.capitalize()}.\")\n        st.stop()")
    ]
    if os.path.exists("c:/Weathermodel/dashboard.py"):
        replace_in_file("c:/Weathermodel/dashboard.py", dashboard_replacements)
    else:
        print("dashboard.py not found in root")

if __name__ == "__main__":
    main()
