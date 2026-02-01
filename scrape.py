import requests
from bs4 import BeautifulSoup
import json
import time

# Base URL for the timetable pages
BASE_URL = "https://keisei.ekitan.com/search/timetable/station"

# --- 1. HARDCODED STATION DATA (Converted from your JS file) ---
# Format: { "Group_ID": { "TIMETABLE_ID": { metadata... } } }
RAW_STATION_DATA = {
    "1464": { # Aoto
        "254-8": { "name": "青砥", "line": "京成本線", "d1_name": "京成上野方面", "d2_name": "成田空港・ちはら台方面" },
        "258-5": { "name": "青砥", "line": "押上線", "d1_name": "押上・西馬込・京急線方面", "d2_name": "成田空港・北総線方面" } # Note: d2 inferred or handled generically
    },
    "1484": { # Akiyama
        "200-4": { "name": "秋山", "line": "北総線", "d1_name": "京成上野・押上方面", "d2_name": "印旛日本医大方面" }
    },
    "1580": { # Ichikawamama
        "254-13": { "name": "市川真間", "line": "京成本線", "d1_name": "京成上野方面", "d2_name": "成田空港方面" }
    },
    "1626": { # Inzai-Makinohara
        "200-13": { "name": "印西牧の原", "line": "北総線", "d1_name": "京成上野方面", "d2_name": "印旛日本医大方面" }
    },
    "1666": { # Edogawa
        "254-11": { "name": "江戸川", "line": "京成本線", "d1_name": "京成上野方面", "d2_name": "成田空港方面" }
    },
    "1699": { # Osakura
        "254-35": { "name": "大佐倉", "line": "京成本線", "d1_name": "京成上野方面", "d2_name": "成田空港方面" }
    },
    "1724": { # Omachi
        "200-7": { "name": "大町", "line": "北総線", "d1_name": "京成上野方面", "d2_name": "印旛日本医大方面" }
    },
    "1732": { # Omoridai
        "256-2": { "name": "大森台", "line": "千原線", "d1_name": "千葉中央方面", "d2_name": "ちはら台方面" }
    },
    "1752": { # Oshiage
        "222-19": { "name": "押上", "line": "都営浅草線", "d1_name": "西馬込方面", "d2_name": "" }, # Special case
        "258-0":  { "name": "押上", "line": "押上線", "d1_name": "青砥・成田空港方面", "d2_name": "" }
    },
    "1766": { "254-16": { "name": "鬼越", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "1769": { "254-7":  { "name": "お花茶屋", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "1783": { "256-4":  { "name": "おゆみ野", "line": "千原線", "d1_name": "千葉方面", "d2_name": "ちはら台方面" } },
    "1789": { "254-20": { "name": "海神", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "1849": { "254-30": { "name": "勝田台", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "1864": { "242-11": { "name": "鎌ケ谷大仏", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "1889": { "242-22": { "name": "上本郷", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "1929": { "256-3":  { "name": "学園前", "line": "千原線", "d1_name": "千葉方面", "d2_name": "ちはら台方面" } },
    "1953": { "200-3":  { "name": "北国分", "line": "北総線", "d1_name": "上野方面", "d2_name": "印旛方面" } },
    "1964": { "242-5":  { "name": "北習志野", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "1967": { "242-14": { "name": "北初富", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "1998": { 
        "254-41": { "name": "空港第２ビル", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田空港方面" },
        "682-6":  { "name": "空港第２ビル", "line": "スカイアクセス", "d1_name": "上野方面", "d2_name": "成田空港方面" }
    },
    "2014": { "242-15": { "name": "くぬぎ山", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "2058": { "255-4":  { "name": "京成稲毛", "line": "千葉線", "d1_name": "津田沼方面", "d2_name": "千葉方面" } },
    "2059": { "254-0":  { "name": "京成上野", "line": "京成本線", "d1_name": "", "d2_name": "成田空港方面" } }, # Terminus
    "2060": { "254-33": { "name": "京成臼井", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2061": { "254-26": { "name": "京成大久保", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2062": { "254-29": { "name": "京成大和田", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2063": { "257-2":  { "name": "京成金町", "line": "金町線", "d1_name": "高砂方面", "d2_name": "" } },
    "2064": { "254-10": { "name": "京成小岩", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2065": { "254-34": { "name": "京成佐倉", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2066": { "254-36": { "name": "京成酒々井", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2067": { "254-5":  { "name": "京成関屋", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2068": { 
        "200-0":  { "name": "京成高砂", "line": "北総線", "d1_name": "印旛方面", "d2_name": "" }, 
        "254-9":  { "name": "京成高砂", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" },
        "257-0":  { "name": "京成高砂", "line": "金町線", "d1_name": "金町方面", "d2_name": "" }
    },
    "2069": { "258-4":  { "name": "京成立石", "line": "押上線", "d1_name": "押上方面", "d2_name": "青砥方面" } },
    "2070": { "255-8":  { "name": "京成千葉", "line": "千葉線", "d1_name": "津田沼方面", "d2_name": "千葉中央方面" } },
    "2071": { 
        "242-0":  { "name": "京成津田沼", "line": "新京成線", "d1_name": "松戸方面", "d2_name": "" },
        "254-25": { "name": "京成津田沼", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" }
    },
    "2072": { "254-17": { "name": "京成中山", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2073": { "254-39": { "name": "京成成田", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田空港方面" } },
    "2074": { "254-19": { "name": "京成西船", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2075": { "258-1":  { "name": "京成曳舟", "line": "押上線", "d1_name": "押上方面", "d2_name": "青砥方面" } },
    "2076": { "254-21": { "name": "京成船橋", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2077": { "255-2":  { "name": "京成幕張", "line": "千葉線", "d1_name": "津田沼方面", "d2_name": "千葉方面" } },
    "2078": { "255-1":  { "name": "京成幕張本郷", "line": "千葉線", "d1_name": "津田沼方面", "d2_name": "千葉方面" } },
    "2079": { "254-15": { "name": "京成八幡", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2080": { "255-3":  { "name": "検見川", "line": "千葉線", "d1_name": "津田沼方面", "d2_name": "千葉方面" } },
    "2094": { "254-38": { "name": "公津の杜", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2098": { "254-12": { "name": "国府台", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2142": { "200-11": { "name": "小室", "line": "北総線", "d1_name": "上野方面", "d2_name": "印旛方面" } },
    "2157": { "242-17": { "name": "五香", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "2235": { "254-31": { "name": "志津", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2245": { "257-1":  { "name": "柴又", "line": "金町線", "d1_name": "高砂方面", "d2_name": "金町方面" } },
    "2300": { "200-10": { "name": "白井", "line": "北総線", "d1_name": "上野方面", "d2_name": "印旛方面" } },
    "2315": { 
        "200-8":  { "name": "新鎌ケ谷", "line": "北総線", "d1_name": "上野方面", "d2_name": "印旛方面" },
        "242-13": { "name": "新鎌ケ谷", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" }
    },
    "2332": { "200-1":  { "name": "新柴又", "line": "北総線", "d1_name": "上野方面", "d2_name": "印旛方面" } },
    "2344": { "255-7":  { "name": "新千葉", "line": "千葉線", "d1_name": "津田沼方面", "d2_name": "千葉方面" } },
    "2345": { "242-1":  { "name": "新津田沼", "line": "新京成線", "d1_name": "千葉方面", "d2_name": "松戸方面" } },
    "2364": { "254-2":  { "name": "新三河島", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2389": { "254-14": { "name": "菅野", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2421": { "254-4":  { "name": "千住大橋", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2431": { "254-37": { "name": "宗吾参道", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2456": { "242-6":  { "name": "高根木戸", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "2457": { "242-7":  { "name": "高根公団", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "2466": { "242-8":  { "name": "滝不動", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "2513": { "254-22": { "name": "大神宮下", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2531": { "256-5":  { "name": "ちはら台", "line": "千原線", "d1_name": "千葉方面", "d2_name": "" } },
    "2534": { 
        "255-9": { "name": "千葉中央", "line": "千葉線", "d1_name": "津田沼方面", "d2_name": "" },
        "256-0": { "name": "千葉中央", "line": "千原線", "d1_name": "", "d2_name": "ちはら台方面" }
    },
    "2535": { "256-1":  { "name": "千葉寺", "line": "千原線", "d1_name": "千葉方面", "d2_name": "ちはら台方面" } },
    "2536": { "200-12": { "name": "千葉ニュータウン中央", "line": "北総線", "d1_name": "上野方面", "d2_name": "印旛方面" } },
    "2607": { "242-18": { "name": "常盤平", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "2690": { "242-4":  { "name": "習志野", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "2692": { "254-42": { "name": "成田空港(第1)", "line": "京成本線", "d1_name": "上野方面", "d2_name": "" } },
    "2725": { "200-9":  { "name": "西白井", "line": "北総線", "d1_name": "上野方面", "d2_name": "印旛方面" } },
    "2740": { "255-6":  { "name": "西登戸", "line": "千葉線", "d1_name": "津田沼方面", "d2_name": "千葉方面" } },
    "2755": { "254-1":  { "name": "日暮里", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2812": { "242-12": { "name": "初富", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "2875": { "254-18": { "name": "東中山", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "2877": { "254-40": { "name": "東成田", "line": "京成本線", "d1_name": "上野方面", "d2_name": "" } },
    "2887": { "200-5":  { "name": "東松戸", "line": "北総線", "d1_name": "上野方面", "d2_name": "印旛方面" } },
    "2966": { "242-10": { "name": "二和向台", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "2977": { "254-23": { "name": "船橋競馬場", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "3005": { "254-6":  { "name": "堀切菖蒲園", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "3025": { "242-2":  { "name": "前原", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "3035": { "254-3":  { "name": "町屋", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "3041": { "242-23": { "name": "松戸", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "" } },
    "3042": { "242-21": { "name": "松戸新田", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "3046": { "200-6":  { "name": "松飛台", "line": "北総線", "d1_name": "上野方面", "d2_name": "印旛方面" } },
    "3060": { "242-9":  { "name": "三咲", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "3086": { "255-5":  { "name": "みどり台", "line": "千葉線", "d1_name": "津田沼方面", "d2_name": "千葉方面" } },
    "3124": { "242-20": { "name": "みのり台", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "3127": { "254-27": { "name": "実籾", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "3183": { "242-16": { "name": "元山", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "3200": { "200-2":  { "name": "矢切", "line": "北総線", "d1_name": "上野方面", "d2_name": "印旛方面" } },
    "3201": { "242-3":  { "name": "薬園台", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "3211": { "254-28": { "name": "八千代台", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "3214": { "254-24": { "name": "谷津", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "3221": { "242-19": { "name": "八柱", "line": "新京成線", "d1_name": "津田沼方面", "d2_name": "松戸方面" } },
    "3222": { "258-2":  { "name": "八広", "line": "押上線", "d1_name": "押上方面", "d2_name": "青砥方面" } },
    "3236": { "254-32": { "name": "ユーカリが丘", "line": "京成本線", "d1_name": "上野方面", "d2_name": "成田方面" } },
    "3269": { "258-3":  { "name": "四ツ木", "line": "押上線", "d1_name": "押上方面", "d2_name": "青砥方面" } },
    "8196": { "200-14": { "name": "印旛日本医大", "line": "北総線", "d1_name": "上野方面", "d2_name": "" } },
    "9640": { "682-5":  { "name": "成田湯川", "line": "スカイアクセス", "d1_name": "上野方面", "d2_name": "成田空港方面" } }
}

# Mapping Japanese train types to CSS classes
TYPE_MAPPING = {
    "普通": "type-local",
    "快速": "type-rapid",
    "通勤特急": "type-express",
    "特急": "type-express",
    "アクセス特急": "type-express",
    "快特": "type-express",
    "ライナー": "type-express"
}

def fetch_timetable_data(url):
    """
    Scrapes the timetable from a specific URL.
    Returns a dict with 'weekday' and 'holiday' lists.
    """
    print(f"  Fetching: {url}")
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"  Failed (Status {resp.status_code})")
            return None
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f"  Failed: {e}")
        return None

    # Check if list view exists
    list_view = soup.find('div', {'v-show': 'isList'})
    if not list_view:
        return None

    data = {"weekday": [], "holiday": []}

    containers = list_view.find_all('div', recursive=False)
    for container in containers:
        v_show = container.get('v-show')
        target_key = "weekday" if v_show == 'isWeekday' else "holiday" if v_show == 'isWeekend' else None
        
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

                data[target_key].append({
                    "hour": h,
                    "minute": m,
                    "type_raw": type_raw,
                    "type_class": TYPE_Mapping_Check(type_raw),
                    "dest": dest
                })
    
    # Sort
    for k in data:
        data[k].sort(key=lambda x: (x['hour'] if x['hour'] >= 3 else x['hour'] + 24, x['minute']))
        
    return data

def TYPE_Mapping_Check(raw_type):
    for key, value in TYPE_MAPPING.items():
        if key in raw_type:
            return value
    return "type-local"

def main():
    final_output = {}

    # Iterate through the hardcoded dictionary
    for group_id, lines_data in RAW_STATION_DATA.items():
        for timetable_id, info in lines_data.items():
            station_name = info['name']
            line_name = info['line']
            
            print(f"Processing {station_name} ({line_name}) [ID: {timetable_id}]...")
            
            # Create an entry in the final JSON
            # We use timetable_id (e.g., '254-8') as the key because it's unique per line per station
            entry = {
                "name": f"{station_name} ({line_name})",
                "station_name_only": station_name,
                "line_name": line_name,
                "d1": {},
                "d2": {}
            }

            # Fetch Direction 1
            if info.get('d1_name'):
                url_d1 = f"{BASE_URL}/{timetable_id}/d1"
                d1_data = fetch_timetable_data(url_d1)
                if d1_data:
                    entry['d1'] = d1_data
                    entry['d1']['name'] = info['d1_name']

            # Polite delay
            time.sleep(0.5)

            # Fetch Direction 2
            if info.get('d2_name'):
                url_d2 = f"{BASE_URL}/{timetable_id}/d2"
                d2_data = fetch_timetable_data(url_d2)
                if d2_data:
                    entry['d2'] = d2_data
                    entry['d2']['name'] = info['d2_name']
            
            # Polite delay
            time.sleep(0.5)

            final_output[timetable_id] = entry

    # Save to file
    with open('keisei_full_timetable.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print("Success! Data saved to keisei_full_timetable.json")

if __name__ == "__main__":
    main()