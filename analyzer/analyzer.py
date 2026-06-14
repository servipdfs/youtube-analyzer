import os
import json
import requests
from datetime import datetime

# Configuración
API_KEY = os.environ.get('YOUTUBE_API_KEY')
CHANNELS_FILE = 'channels.txt'
DATA_FILE = 'data/channels.json'

DEFAULT_CHANNELS = [
    'MrBeast',
    'PewDiePie',
    'Veritasium',
    'Marques Brownlee',
    'Linus Tech Tips'
]

def get_channel_data(channel_name):
    try:
        search_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&q={channel_name}&type=channel&key={API_KEY}&maxResults=1'
        search_response = requests.get(search_url)
        search_data = search_response.json()
        
        if 'items' not in search_data or len(search_data['items']) == 0:
            return None
        
        channel_id = search_data['items'][0]['id']['channelId']
        
        stats_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={channel_id}&key={API_KEY}'
        stats_response = requests.get(stats_url)
        stats_data = stats_response.json()
        
        if 'items' not in stats_data or len(stats_data['items']) == 0:
            return None
        
        stats = stats_data['items'][0]['statistics']
        snippet = stats_data['items'][0]['snippet']
        
        total_views = int(stats.get('viewCount', 0))
        monthly_views = total_views / 60
        estimated_revenue = (monthly_views * 3) / 1000
        
        return {
            'channel_id': channel_id,
            'name': snippet['title'],
            'description': snippet.get('description', ''),
            'thumbnail': snippet['thumbnails']['high']['url'],
            'subscribers': int(stats.get('subscriberCount', 0)),
            'total_views': total_views,
            'video_count': int(stats.get('videoCount', 0)),
            'estimated_monthly_revenue': round(estimated_revenue, 2),
            'last_updated': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f'Error analyzing {channel_name}: {e}')
        return None

def load_existing_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'channels': [], 'last_run': None}

def save_data(data):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print('🚀 Iniciando análisis de canales...')
    
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, 'r') as f:
            channels = [line.strip() for line in f if line.strip()]
    else:
        channels = DEFAULT_CHANNELS
    
    data = load_existing_data()
    
    updated_channels = []
    for channel_name in channels:
        print(f'📊 Analizando: {channel_name}')
        channel_data = get_channel_data(channel_name)
        
        if channel_data:
            existing = next((c for c in data['channels'] if c['channel_id'] == channel_data['channel_id']), None)
            
            if existing:
                if 'history' not in existing:
                    existing['history'] = []
                
                existing['history'].append({
                    'date': datetime.now().isoformat(),
                    'subscribers': channel_data['subscribers'],
                    'total_views': channel_data['total_views'],
                    'estimated_revenue': channel_data['estimated_monthly_revenue']
                })
                
                existing['history'] = existing['history'][-30:]
                existing.update(channel_data)
                updated_channels.append(existing)
            else:
                channel_data['history'] = [{
                    'date': datetime.now().isoformat(),
                    'subscribers': channel_data['subscribers'],
                    'total_views': channel_data['total_views'],
                    'estimated_revenue': channel_data['estimated_monthly_revenue']
                }]
                updated_channels.append(channel_data)
            
            print(f'✅ {channel_data["name"]}: {channel_data["subscribers"]} subs')
        else:
            print(f'❌ No se pudo analizar {channel_name}')
    
    data['channels'] = updated_channels
    data['last_run'] = datetime.now().isoformat()
    save_data(data)
    
    print(f'✅ Análisis completado. {len(updated_channels)} canales actualizados.')

if __name__ == '__main__':
    main()
