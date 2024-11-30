import requests
import json
import time
import pandas as pd
import re
from typing import List, Dict, Tuple
from datetime import datetime

def parse_dms_coordinate(coord_str: str) -> float:
    """Parse coordinates from DMS format to decimal degrees."""
    # Remove directional indicator (N, E, S, W)
    direction = 1
    if 'S' in coord_str or 'W' in coord_str:
        direction = -1
    coord_str = coord_str.replace('N', '').replace('S', '').replace('E', '').replace('W', '').strip()
    
    # Extract the components using regex
    match = re.match(r'(\d+)°(\d+)\'(\d+)"?', coord_str)
    if not match:
        raise ValueError(f"Could not parse coordinate: {coord_str}")
    
    degrees = float(match.group(1))
    minutes = float(match.group(2))
    seconds = float(match.group(3))
    
    return direction * (degrees + minutes/60 + seconds/3600)

def read_station_coordinates(filepath: str) -> Dict[str, Dict[str, str]]:
    """Read station coordinates from file."""
    coordinates = {}
    current_station = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('AJKURE_L'):
                current_station = 'Kuressaare'
            elif line.startswith('AJ'):
                continue
            elif not any(prefix in line for prefix in ['Laius:', 'Pikkus:']):
                current_station = line
            elif current_station:
                if line.startswith('Laius:'):
                    if current_station not in coordinates:
                        coordinates[current_station] = {}
                    coordinates[current_station]['latitude'] = line.replace('Laius:', '').strip()
                elif line.startswith('Pikkus:'):
                    if current_station not in coordinates:
                        coordinates[current_station] = {}
                    coordinates[current_station]['longitude'] = line.replace('Pikkus:', '').strip()
    
    return coordinates

def fetch_wind_data() -> List[Dict]:
    """
    Fetch all wind speed data for 2023 using pagination.
    Returns a list of dictionaries containing the wind data.
    """
    base_url = 'https://keskkonnaandmed.envir.ee/f_kliima_paev'
    limit = 20000
    offset = 0
    all_data = []
    has_more = True

    headers = {
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0'
    }
    
    # Read station coordinates
    coordinates = read_station_coordinates('data_extraction/imajaamade_koordinaadid.txt')

    while has_more:
        url = f"{base_url}?aasta=eq.2023&element_kood=eq.DWSX&limit={limit}&offset={offset}"
        print(f"Fetching data with offset {offset}...")

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f'Error response: {response.status_code}')
                print(f'Response headers: {response.headers}')
                print(f'Response content: {response.text}')
            response.raise_for_status()
            data = response.json()

            # Add coordinates to each record
            for record in data:
                station = record.get('jaam_nimi')
                if station in coordinates:
                    record['latitude'] = coordinates[station]['latitude']
                    record['longitude'] = coordinates[station]['longitude']

            # Add the data to our collection
            all_data.extend(data)

            # Check if we need to continue pagination
            if len(data) < limit:
                has_more = False
                print('Reached the end of data')
            else:
                offset += limit

            # Optional: Add a small delay to avoid overwhelming the API
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f'Error fetching data: {e}')
            has_more = False

    print(f"Total records fetched: {len(all_data)}")
    return all_data

def save_to_file(data: List[Dict], filename: str) -> None:
    """
    Save the data to a file in both JSON and CSV formats.
    """
    # Save as JSON
    json_filename = f"{filename}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {json_filename}")

    # Save as CSV
    csv_filename = f"{filename}.csv"
    df = pd.DataFrame(data)
    df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"Data saved to {csv_filename}")

def analyze_data(data: List[Dict]) -> None:
    """Perform basic analysis on the wind speed data."""
    df = pd.DataFrame(data)
    
    # Basic statistics
    total_records = len(df)
    total_stations = len(df['jaam_nimi'].unique())
    max_speed = df['vaartus'].max()
    min_speed = df['vaartus'].min()
    avg_speed = df['vaartus'].mean()
    
    print("\nData Summary:")
    print(f"Number of stations: {total_stations}")
    print(f"Number of measurements: {total_records}")
    print(f"Maximum wind speed: {max_speed:.2f}")
    print(f"Minimum wind speed: {min_speed:.2f}")
    print(f"Average wind speed: {avg_speed:.2f}")
    
    # Station-level summary
    station_summary = df.groupby('jaam_nimi').agg({
        'vaartus': ['mean', 'max', 'count'],
        'latitude': 'first',
        'longitude': 'first'
    })
    
    print("\nStation Summary:")
    print(station_summary)
    
    # Monthly averages
    monthly_avg = df.groupby('kuu')['vaartus'].mean()
    
    print("\nMonthly Average Wind Speeds:")
    for month, avg in monthly_avg.items():
        print(f"Month {month:2d}: {avg:6.2f} m/s")

def main():
    # Record start time
    start_time = datetime.now()
    print(f"Starting data fetch at {start_time}")

    # Fetch the data
    data = fetch_wind_data()

    # Save the data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_to_file(data, f"wind_data_2023_{timestamp}")

    # Analyze the data
    analyze_data(data)

    # Print execution time
    end_time = datetime.now()
    execution_time = end_time - start_time
    print(f"\nScript completed in {execution_time}")

if __name__ == "__main__":
    main()