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
    # 10. geospatial_features.py
    geospatial_replacements = [
        ("STATIC_FEATURES_PATH = Path(\"data/geospatial/static_features.csv\")\nSTATIC_FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)\nREPORTS_DIR = Path(\"reports/figures\")", """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

if CITY == 'mumbai':
    STATIC_FEATURES_PATH = Path("data/geospatial/static_features.csv")
    REPORTS_DIR = Path("reports/figures")
else:
    STATIC_FEATURES_PATH = Path(f"data/geospatial/{CITY}_static_features.csv")
    REPORTS_DIR = Path(f"reports/{CITY}")
STATIC_FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
"""),
        ("training_data_path = \"data/processed/training_features.csv\"", "training_data_path = \"data/processed/training_features.csv\" if CITY == 'mumbai' else f\"data/processed/{CITY}_training_features.csv\"")
    ]
    replace_in_file("c:/Weathermodel/script/geospatial_features.py", geospatial_replacements)

if __name__ == "__main__":
    main()
