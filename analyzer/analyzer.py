import os
import json
import requests
from datetime import datetime

# Configuración
API_KEY = os.environ.get('YOUTUBE_API_KEY')
DATA_FILE = 'data/channels.json'

def get_trending_channels(max_channels=10):
    """Obtiene los canales de los videos trending"""
    try:
        # Obtener videos trending
        trending_url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode=US&maxResults=50&key={API_KEY}'
        response = requests.get(trending_url)
        data = response.json()
        
        if 'items' not in data:
            return []
        
        # Extraer canales únicos
        channels = {}
        for video in data['items']:
            channel_id = video['snippet']['channelId']
            channel_name = video['snippet']['channelTitle']
            
            if channel_id not in channels:
                channels[channel_id] = {
                    'name': channel_name,
                    'id': channel_id
                }
        
        # Devolver los primeros N canales
        return list(channels.values())[:max_channels]
    
    except Exception as e:
        print(f'Error getting trending channels: {e}')
        return []

def get_channel_stats(channel_id):
    """Obtiene estadísticas de un canal"""
    try:
        stats_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={channel_id}&key={API_KEY}'
        response = requests.get(stats_url)
        data = response.json()
        
        if 'items' not in data or len(data['items']) == 0:
            return None
        
        stats = data['items'][0]['statistics']
        snippet = data['items'][0]['snippet']
        
        # Calcular ingresos estimados (CPM promedio de 3€)
        total_views = int(stats.get('viewCount', 0))
        monthly_views = total_views / 60  # Estimación: canal con 5 años de historia
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
        print(f'Error analyzing channel {channel_id}: {e}')
        return None

def load_existing_data():
    """Carga datos existentes"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'channels': [], 'last_run': None, 'trending_date': None}

def save_data(data):
    """Guarda los datos"""
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print('🚀 Iniciando análisis de canales trending...')
    
    # 1. Obtener canales trending
    print('📊 Obteniendo canales de tendencia...')
    trending_channels = get_trending_channels(max_channels=10)
    
    if not trending_channels:
        print('❌ No se pudieron obtener canales trending')
        return
    
    print(f'✅ Encontrados {len(trending_channels)} canales trending')
    
    # 2. Cargar datos existentes
    data = load_existing_data()
    
    # 3. Analizar cada canal
    updated_channels = []
    for channel in trending_channels:
        print(f'📊 Analizando: {channel["name"]}')
        channel_data = get_channel_stats(channel['id'])
        
        if channel_data:
            # Buscar si ya existe
            existing = next((c for c in data['channels'] if c['channel_id'] == channel_data['channel_id']), None)
            
            if existing:
                # Mantener historial
                if 'history' not in existing:
                    existing['history'] = []
                
                existing['history'].append({
                    'date': datetime.now().isoformat(),
                    'subscribers': channel_data['subscribers'],
                    'total_views': channel_data['total_views'],
                    'estimated_revenue': channel_data['estimated_monthly_revenue']
                })
                
                # Mantener solo últimas 30 mediciones
                existing['history'] = existing['history'][-30:]
                
                # Actualizar datos
                existing.update(channel_data)
                updated_channels.append(existing)
            else:
                # Canal nuevo
                channel_data['history'] = [{
                    'date': datetime.now().isoformat(),
                    'subscribers': channel_data['subscribers'],
                    'total_views': channel_data['total_views'],
                    'estimated_revenue': channel_data['estimated_monthly_revenue']
                }]
                updated_channels.append(channel_data)
            
            print(f'✅ {channel_data["name"]}: {channel_data["subscribers"]} subs')
        else:
            print(f'❌ No se pudo analizar {channel["name"]}')
    
    # 4. Guardar datos
    data['channels'] = updated_channels
    data['last_run'] = datetime.now().isoformat()
    data['trending_date'] = datetime.now().isoformat()
    save_data(data)
    
    print(f'✅ Análisis completado. {len(updated_channels)} canales actualizados.')

if __name__ == '__main__':
    main()
