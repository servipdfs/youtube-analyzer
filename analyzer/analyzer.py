import os
import json
import requests
from datetime import datetime, timedelta

# Configuración
API_KEY = os.environ.get('YOUTUBE_API_KEY')
DATA_FILE = 'data/channels.json'

def get_trending_channels(max_channels=10):
    """Obtiene los canales de los videos trending"""
    try:
        # Obtener videos trending
        trending_url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode=US&maxResults=50&key={API_KEY}'
        response = requests.get(trending_url)
        response.raise_for_status()  # Verificar errores HTTP
        data = response.json()
        
        if 'items' not in data:
            print(f'❌ Error en la respuesta de YouTube: {data.get("error", {}).get("message", "Unknown error")}')
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
    
    except requests.exceptions.RequestException as e:
        print(f'❌ Error de conexión: {e}')
        return []
    except json.JSONDecodeError as e:
        print(f'❌ Error al decodificar JSON: {e}')
        return []

def get_channel_stats(channel_id):
    """Obtiene estadísticas de un canal"""
    try:
        stats_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={channel_id}&key={API_KEY}'
        response = requests.get(stats_url)
        response.raise_for_status()
        data = response.json()
        
        if 'items' not in data or len(data['items']) == 0:
            print(f'❌ Canal {channel_id} no encontrado')
            return None
        
        stats = data['items'][0]['statistics']
        snippet = data['items'][0]['snippet']
        
        # Calcular ingresos estimados (CPM promedio de 3€)
        total_views = int(stats.get('viewCount', 0))
        # Estimación más realista basada en los últimos 30 días
        monthly_views = total_views / 60  # Estimación: canal con 5 años de historia
        estimated_revenue = (monthly_views * 3) / 1000
        
        return {
            'channel_id': channel_id,
            'name': snippet['title'],
            'description': snippet.get('description', ''),
            'thumbnail': snippet['thumbnails']['high']['url'] if 'high' in snippet.get('thumbnails', {}) else snippet['thumbnails']['default']['url'],
            'subscribers': int(stats.get('subscriberCount', 0)),
            'total_views': total_views,
            'video_count': int(stats.get('videoCount', 0)),
            'estimated_monthly_revenue': round(estimated_revenue, 2),
            'last_updated': datetime.now().isoformat()
        }
    
    except requests.exceptions.RequestException as e:
        print(f'❌ Error de conexión al analizar canal {channel_id}: {e}')
        return None
    except (KeyError, ValueError) as e:
        print(f'❌ Error al procesar datos del canal {channel_id}: {e}')
        return None

def load_existing_data():
    """Carga datos existentes"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Verificar estructura
                if 'channels' not in data:
                    data['channels'] = []
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f'⚠️ Error al cargar datos existentes: {e}')
    
    return {'channels': [], 'last_run': None, 'trending_date': None}

def save_data(data):
    """Guarda los datos"""
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print('🚀 Iniciando análisis de canales trending...')
    
    if not API_KEY:
        print('❌ ERROR: YOUTUBE_API_KEY no está configurada')
        return
    
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
    for i, channel in enumerate(trending_channels, 1):
        print(f'📊 [{i}/{len(trending_channels)}] Analizando: {channel["name"]}')
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
                if len(existing['history']) > 30:
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
            
            print(f'  ✅ {channel_data["name"]}: {channel_data["subscribers"]:,} subs | {channel_data["total_views"]:,} views')
        else:
            print(f'  ❌ No se pudo analizar {channel["name"]}')
    
    # 4. Guardar datos
    if updated_channels:
        data['channels'] = updated_channels
        data['last_run'] = datetime.now().isoformat()
        data['trending_date'] = datetime.now().isoformat()
        save_data(data)
        
        print(f'\n✅ Análisis completado exitosamente.')
        print(f'📈 {len(updated_channels)} canales actualizados.')
    else:
        print('\n❌ No se actualizó ningún canal.')

if __name__ == '__main__':
    main()
