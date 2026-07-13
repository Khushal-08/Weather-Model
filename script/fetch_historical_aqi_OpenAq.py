import os
import time
import requests
import pandas as pd

# ==========================
# CONFIG
# ==========================

API_KEY = os.getenv("OPENAQ_API_KEY")

BASE_URL = "https://api.openaq.org/v3"

HEADERS = {
    "X-API-Key": API_KEY
}

# ==========================
# GET MUMBAI LOCATIONS
# ==========================

def get_locations():

    url = f"{BASE_URL}/locations"

    params = {
        "coordinates": "19.0760,72.8777",
        "radius": 25000,
        "limit": 100
    }

    r = requests.get(url, headers=HEADERS, params=params)
    print(r.url)

    r.raise_for_status()

    locations = r.json()["results"]

    print(f"\nFound {len(locations)} locations\n")

    return locations

# ==========================
# GET SENSORS
# ==========================

def get_sensors(location_id):

    url = f"{BASE_URL}/locations/{location_id}/sensors"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:

        print(f"Location {location_id}: No sensors")

        return []

    sensors = r.json()["results"]

    print(f"Location {location_id}: {len(sensors)} sensors")

    return sensors


# ==========================
# GET MEASUREMENTS
# ==========================

def get_measurements(sensor_id, date_from, date_to):

    url = f"{BASE_URL}/sensors/{sensor_id}/days"

    page = 1
    all_results = []

    while True:

        params = {
            "date_from": date_from,
            "date_to": date_to,
            "limit": 1000,
            "page": page
        }

        for attempt in range(3):
            try:
                r = requests.get(url, headers=HEADERS, params=params, timeout=60)
                if r.status_code == 200:
                    break
                elif r.status_code == 429: # Rate limit
                    time.sleep(2)
            except requests.exceptions.RequestException:
                time.sleep(2)
        else:
            print(f"Sensor {sensor_id}: Failed after 3 attempts")
            break

        print(r.url)
        if r.status_code != 200:
            print(f"Sensor {sensor_id}: Status {r.status_code}")
            print(r.text)
            break

        data = r.json()
        results = data.get("results", [])

        if not results:
            break

        all_results.extend(results)

        print(f"        Page {page}: {len(results)} records")

        if len(results) < 1000:
            break

        page += 1
        time.sleep(0.3)

    return all_results
# ==========================
# MAIN
# ==========================

def main():
    from datetime import datetime

    if API_KEY is None:
        print("OPENAQ_API_KEY not found!")
        return

    TARGET_STATIONS = [
        "Colaba",
        "Chembur",
        "Sion",
        "Worli",
        "Borivali",
        "Bandra Kurla"
    ]

    REQUESTED_DATE_FROM = "2024-01-01"
    REQUESTED_DATE_TO = "2024-12-31"

    req_from_dt = datetime.strptime(REQUESTED_DATE_FROM, "%Y-%m-%d").date()
    req_to_dt = datetime.strptime(REQUESTED_DATE_TO, "%Y-%m-%d").date()

    # Get all Mumbai locations
    all_locations = get_locations()

    # Filter locations
    filtered = [
        loc for loc in all_locations
        if any(name in loc["name"] for name in TARGET_STATIONS)
    ]

    # Keep only one location per station
    selected = []
    seen = set()

    for loc in filtered:
        for station in TARGET_STATIONS:
            if station in loc["name"] and station not in seen:
                selected.append(loc)
                seen.add(station)
                break

    locations = selected

    print("\nSelected stations:")
    for loc in locations:
        print(f" - {loc['name']}")

    all_records = []

    for loc in locations:

        print(f"\nProcessing {loc['name']}")

        sensors = get_sensors(loc["id"])

        for sensor in sensors:
            
            sensor_id = sensor["id"]
            parameter = sensor.get("parameter", {}).get("name", "Unknown")
            
            print(
                "ID:", sensor["id"],
                "| Parameter:", parameter,
                "| First:", sensor.get("datetimeFirst"),
                "| Last:", sensor.get("datetimeLast")
            )

            AQI_PARAMETERS = {
                "pm25",
                "pm10",
                "no2",
                "so2",
                "co",
                "o3"
            }
            if parameter.lower() not in AQI_PARAMETERS:
                continue

            sensor_first = sensor.get("datetimeFirst")
            sensor_last = sensor.get("datetimeLast")

            if not sensor_first:
                print(f"   Skipping Sensor {sensor_id} ({parameter}): No datetimeFirst")
                continue

            try:
                s_from = datetime.strptime(sensor_first[:10], "%Y-%m-%d").date()
                if sensor_last:
                    s_to = datetime.strptime(sensor_last[:10], "%Y-%m-%d").date()
                else:
                    s_to = datetime.today().date()
                
                if s_from > req_to_dt or s_to < req_from_dt:
                    print(f"   Skipping Sensor {sensor_id} ({parameter}): Active dates ({s_from} to {s_to}) do not overlap requested period.")
                    continue
            except Exception as e:
                print(f"   Date parsing error for sensor {sensor_id}: {e}")
                continue

            print(f"   Fetching Sensor {sensor_id} ({parameter})")

            measurements = get_measurements(sensor_id, REQUESTED_DATE_FROM, REQUESTED_DATE_TO)

            print(f"      {len(measurements)} records")

            for m in measurements:

                m["location_name"] = loc["name"]
                m["location_id"] = loc["id"]
                m["sensor_id"] = sensor_id
                m["parameter"] = parameter

                all_records.append(m)

            time.sleep(0.3)

    print("\nTotal Records:", len(all_records))

    if len(all_records):

        df = pd.json_normalize(all_records)

        os.makedirs("data/raw", exist_ok=True)

        filename = "data/raw/openaq_historical_mumbai.csv"

        df.to_csv(filename, index=False)

        print(f"\nSaved to {filename}")

        print(df.head())


if __name__ == "__main__":

    main()