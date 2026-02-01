import requests
from bs4 import BeautifulSoup
import json
import re

# 京成電鉄 江戸川駅 (成田空港・ちはら台方面)
URL = "https://keisei.ekitan.com/search/timetable/station/254-11/d2"

# 表示色を決めるための種別マッピング
TYPE_Mapping = {
    "普通": "type-local",
    "快速": "type-rapid",
    "通勤特急": "type-express",
    "特急": "type-express",
    "アクセス特急": "type-express",
    "快特": "type-express"
}

def fetch_data():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    timetable = {
        "weekday": [],
        "holiday": []
    }

    # HTML内の構造: 
    # 平日データ: <div v-show="isWeekday"> 内の <li class="ekltip">
    # 土休日データ: <div v-show="isWeekend"> 内の <li class="ekltip">
    
    # リスト表示エリアを取得
    list_view = soup.find('div', {'v-show': 'isList'})
    if not list_view:
        print("List view not found")
        return None

    # 平日と土休日のコンテナを特定
    # v-show属性はBeautifulSoupではそのまま属性として取れます
    containers = list_view.find_all('div', recursive=False)
    
    for container in containers:
        v_show = container.get('v-show')
        
        target_key = None
        if v_show == 'isWeekday':
            target_key = "weekday"
        elif v_show == 'isWeekend':
            target_key = "holiday"
        
        if target_key:
            # 電車リスト(li class="ekltip") を全て取得
            trains = container.find_all('li', class_='ekltip')
            
            for train in trains:
                # 時刻 (例: 5:07)
                time_str = train.find('span', class_='ekldeptime').text.strip()
                if ':' in time_str:
                    hour, minute = map(int, time_str.split(':'))
                else:
                    continue # 時刻が取得できない場合はスキップ

                # 種別 (例: 普通)
                type_raw = train.find('span', class_='ekltraintype').text.strip()
                
                # 行先 (例: 成田空港)
                dest = train.find('span', class_='ekldest').text.strip()
                
                # 両数 (このページには両数情報がないため空文字または仮定)
                # 詳細ページへのリンク引数には含まれている可能性がありますが、ここではスキップ
                car = "-" 

                # データ格納
                timetable[target_key].append({
                    "hour": hour,
                    "minute": minute,
                    "type_raw": type_raw,
                    "type_class": TYPE_Mapping.get(type_raw, "type-local"),
                    "dest": dest,
                    "car": car
                })

    return timetable

if __name__ == "__main__":
    data = fetch_data()
    if data:
        # 時刻順に念のためソート（通常はサイト側で整列済み）
        for key in data:
            data[key].sort(key=lambda x: (x['hour'] if x['hour'] >= 3 else x['hour'] + 24, x['minute']))

        with open('timetable.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Success: timetable.json created.")
    else:
        print("Failed to fetch data.")
        exit(1)