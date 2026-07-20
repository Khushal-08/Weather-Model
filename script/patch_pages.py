import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched {filepath}")

def main():
    replacements_admin = [
        ("st.title(\"Mumbai Urban Air Quality\")", "city = st.session_state.get('city', 'mumbai')\n    st.title(f\"{city.capitalize()} Urban Air Quality\")"),
        ("df_hist, station_list = load_historical_data()", "df_hist, station_list = load_historical_data(city=city)"),
        ("intelligence_data = load_demo_json(selected_station)", "intelligence_data = load_demo_json(selected_station, city=city)")
    ]
    replace_in_file("c:/Weathermodel/pages/1_Administrator.py", replacements_admin)

    replacements_citizen = [
        ("st.title(\"Mumbai Urban Air Quality\")", "city = st.session_state.get('city', 'mumbai')\n    st.title(f\"{city.capitalize()} Urban Air Quality\")"),
        ("df_hist, station_list = load_historical_data()", "df_hist, station_list = load_historical_data(city=city)"),
        ("intelligence_data = load_demo_json(selected_station)", "intelligence_data = load_demo_json(selected_station, city=city)")
    ]
    replace_in_file("c:/Weathermodel/pages/2_Citizen.py", replacements_citizen)

if __name__ == "__main__":
    main()
