import os
import requests
import pandas as pd

API_KEY = "579b464db66ec23bdd000001891d9e4ca1334dd576c21415e1d35235"

URL = "https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

params = {
    "api-key": API_KEY,
    "format": "json",
    "filters[state]": "Maharashtra",
    "filters[city]": "Mumbai",
    "limit": 500
}

print("Fetching AQI...")

response = requests.get(
    URL,
    params=params,
    headers=headers,
    timeout=60
)

print("Status:", response.status_code)

response.raise_for_status()

data = response.json()

records = data.get("records", [])

print("Records:", len(records))

df = pd.DataFrame(records)

os.makedirs("data/raw", exist_ok=True)

df.to_csv("data/raw/aqi.csv", index=False)

print(df.head())

print("\nColumns:")
print(df.columns.tolist())

print("\nCities:")
print(df["city"].unique())

print("\nMumbai Stations:")
print(df["station"].unique())