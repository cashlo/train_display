import requests
from bs4 import BeautifulSoup
import json
import re
import time
import sys

# Base URL for relative links
BASE_URL = "https://keisei.ekitan.com"
# The page listing all stations (Index page)
INDEX_URL = "https://keisei.ekitan.com/search/timetable"

# Train type mapping for CSS classes
TYPE_MAPPING = {
    "普通": "type-local",
    "快速": "type-rapid",
    "通勤特急": "type-express",
    "特急": "type-express",
    "アクセス特急": "type-express",
    "快特": "type-express",
    "ライナー": "type-express" # Skyliner etc
}

def get_station_links():
    """
    Visits the main timetable index to find links to all individual stations.
    """
    print(f"Fetching station list from {INDEX_URL}...")
    try:
        resp = requests.get(INDEX_URL)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f"Failed to fetch index: {e}")
        return {}

    station_links = {}
    
    # Logic: Find links usually inside specific lists or tables on the index page.
    # Looking at standard Ekitan structures, they are often in <li><a>...</a></li>
    # We look for links containing '/search/timetable/station/'
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/search/timetable/station/' in href:
            # Check if it's a specific direction link (ends in d1, d2) or a general station link
            # We want the general station link or the first direction to start with.
            # Usually the index links to ".../d1" or ".../index".
            
            # Example href: /search/timetable/station/254-11/d1
            
            name = a.text.strip()
            # Clean up the name (remove extra spaces or newlines)
            name = re.sub(r'\s+', ' ', name)
            
            # Use the station ID code from URL as key (e.g., "254-11")
            match = re.search(r'station/([\d\-]+)', href)
            if match:
                station_id = match.group(1)
                if station_id not in station_links:
                     # Store full URL. If relative, prepend base.
                    full_url = href if href.startswith('http') else BASE_URL + href
                    # Remove the specific direction (d1/d2) to store a "base" station URL
                    # We will append d1/d2 manually to ensure we get both.
                    base_station_url = re.sub(r'/d\d+$', '', full_url)
                    station_links[station_id] = {
                        "name": name,
                        "base_url": base_station_url
                    }
    
    print(f"Found {len(station_links)} stations.")
    return station_links

def fetch_timetable_for_url(url):
    """
    Fetches and parses a single timetable page (e.g., Station X, Direction 1).
    """
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

    # Determine if list view exists
    list_view = soup.find('div', {'v-show': 'isList'})
    if not list_view:
        return None

    # Data structure for this specific direction
    direction_data = {
        "weekday": [],
        "holiday": []
    }

    # Helper to parse containers
    containers = list_view.find_all('div', recursive=False)
    for container in containers:
        v_show = container.get('v-show')
        
        target_key = None
        if v_show == 'isWeekday':
            target_key = "weekday"
        elif v_show == 'isWeekend':
            target_key = "holiday"
        
        if target_key:
            trains = container.find_all('li', class_='ekltip')
            for train in trains:
                # Time
                time_span = train.find('span', class_='ekldeptime')
                if not time_span: continue
                time_str = time_span.text.strip()
                if ':' not in time_str: continue
                
                h, m = map(int, time_str.split(':'))
                
                # Type
                type_span = train.find('span', class_='ekltraintype')
                type_raw = type_span.text.strip() if type_span else "普通"
                
                # Dest
                dest_span = train.find('span', class_='ekldest')
                dest = dest_span.text.strip() if dest_span else ""

                direction_data[target_key].append({
                    "hour": h,
                    "minute": m,
                    "type_raw": type_raw,
                    "type_class": TYPE_MAPPING.get(type_raw, "type-local"),
                    "dest": dest
                })
    
    # Sort
    for k in direction_data:
        direction_data[k].sort(key=lambda x: (x['hour'] if x['hour'] >= 3 else x['hour'] + 24, x['minute']))
        
    return direction_data

def main():
    all_data = {}
    stations = get_station_links()
    
    # Loop through all found stations
    for s_id, info in stations.items():
        print(f"Processing {info['name']} ({s_id})...")
        
        station_result = {
            "name": info['name'],
            "id": s_id,
            "d1": {}, # Direction 1 (usually Up)
            "d2": {}  # Direction 2 (usually Down)
        }

        # Fetch Direction 1
        url_d1 = f"{info['base_url']}/d1"
        data_d1 = fetch_timetable_for_url(url_d1)
        if data_d1:
            station_result["d1"] = data_d1
        else:
            print("  No data for d1")
        
        # Be polite to server
        time.sleep(0.5)

        # Fetch Direction 2
        url_d2 = f"{info['base_url']}/d2"
        data_d2 = fetch_timetable_for_url(url_d2)
        if data_d2:
            station_result["d2"] = data_d2
        else:
             print("  No data for d2")

        # Save to main dict
        all_data[s_id] = station_result
        
        # Be polite
        time.sleep(0.5)

    # Save to file
    with open('keisei_full_timetable.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print("Done! Saved to keisei_full_timetable.json")

if __name__ == "__main__":
    main()