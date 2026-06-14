import os
import json
import requests
from datetime import datetime, timedelta

# Configuración
API_KEY = os.environ.get('YOUTUBE_API_KEY')
DATA_FILE = 'data/channels.json'

# Palabras clave típicas de canales faceless
FACELESS_KEYWORDS = [
    'top', 'best', 'amazing', 'facts', 'daily', 'dose', 'compilation',
    'satisfying', 'asmr', 'relaxing', 'lofi', 'chill', 'music',
    'gaming', 'highlights', 'moments', 'fails', 'funny', 'viral',
    'tutorial', 'how to', 'guide', 'tips', 'tricks', 'hack',
    'motivation', 'inspiration', 'quotes', 'wisdom', 'success',
    'technology', 'tech', 'review', 'unboxing', 'gadgets',
    'cooking', 'recipe', 'food', 'diy', 'craft', 'art',
    'science', 'education', 'learning', 'documentary', 'history',
    'mystery', 'creepy', 'scary', 'horror', 'paranormal',
    'finance', 'money', 'investing', 'crypto', 'bitcoin',
    'health', 'fitness', 'workout', 'nutrition', 'wellness'
]

def get_recent_popular_videos(days=10, max_results=50):
    """Obtiene videos populares de los últimos N días"""
    try:
        published_after = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
        
        search_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&order=viewCount&publishedAfter={published_after}&maxResults={max_results}&key={API_KEY}'
        response = requests.get(search_url)
        data = response.json()
        
        if 'items' not in data:
            print(f'Error en search API: {data}')
            return []
        
        channels = {}
        for item in data['items']:
            if 'channelId' in item['snippet']:
                channel_id = item['snippet']['channelId']
                channel_name = item['snippet']['channelTitle']
                
                if channel_id not in channels:
                    channels[channel_id] = {
                        'name': channel_name,
                        'id': channel_id
                    }
        
        return list(channels.values())
    
    except Exception as e:
        print(f'Error getting recent videos: {e}')
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
        
        subscribers = int(stats.get('subscriberCount', 0))
        total_views = int(stats.get('viewCount', 0))
        video_count = int(stats.get('videoCount', 0))
        
        # Calcular ingresos estimados (CPM promedio de 3€)
        monthly_views = total_views * 0.20 / 60
        estimated_revenue = (monthly_views * 3) / 1000
        
        # Detectar si es probablemente faceless
        is_likely_faceless = detect_faceless_channel(
            snippet['title'],
            subscribers,
            total_views,
            video_count,
            snippet.get('description', '')
        )
        
        # Calcular ratio vistas/suscriptores
        views_per_sub = total_views / subscribers if subscribers > 0 else 0
        
        # Calcular días desde creación
        published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
        days_old = (datetime.now(published_at.tzinfo) - published_at).days
        
        return {
            'channel_id': channel_id,
            'name': snippet['title'],
            'description': snippet.get('description', ''),
            'thumbnail': snippet['thumbnails']['high']['url'],
            'subscribers': subscribers,
            'total_views': total_views,
            'video_count': video_count,
            'estimated_monthly_revenue': round(estimated_revenue, 2),
            'views_per_subscriber': round(views_per_sub, 2),
            'published_at': snippet['publishedAt'],
            'days_old': days_old,
            'is_likely_faceless': is_likely_faceless,
            'last_updated': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f'Error analyzing channel {channel_id}: {e}')
        return None

def detect_faceless_channel(name, subscribers, total_views, video_count, description):
    """Detecta si un canal es probablemente faceless basado en heurísticas"""
    score = 0
    
    # 1. Nombre genérico con keywords típicos de faceless
    name_lower = name.lower()
    description_lower = description.lower()
    combined_text = name_lower + ' ' + description_lower
    
    keyword_matches = sum(1 for kw in FACELESS_KEYWORDS if kw in combined_text)
    if keyword_matches >= 2:
        score += 3
    elif keyword_matches >= 1:
        score += 1
    
    # 2. Ratio vistas/suscriptores muy alto (típico de contenido viral sin personalidad)
    if subscribers > 0:
        views_per_sub = total_views / subscribers
        if views_per_sub > 100:
            score += 3
        elif views_per_sub > 50:
            score += 2
        elif views_per_sub > 20:
            score += 1
    
    # 3. Pocos videos pero muchas vistas (contenido automatizado)
    if video_count < 50 and total_views > 1000000:
        score += 2
    elif video_count < 100 and total_views > 500000:
        score += 1
    
    # 4. Canal nuevo con crecimiento rápido
    if subscribers > 10000 and video_count < 30:
        score += 2
    
    # 5. Nombre con números o patrones genéricos
    if any(char.isdigit() for char in name) and len(name) < 20:
        score += 1
    
    # Umbral: si el score es >= 4, es probablemente faceless
    return score >= 4

def load_existing_data():
    """Carga datos existentes"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'channels': [], 'last_run': None}

def save_data(data):
    """Guarda los datos"""
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print('🚀 Iniciando análisis de canales faceless de los últimos 10 días...')
    
    # 1. Obtener canales de videos recientes
    print('📊 Buscando videos populares de los últimos 10 días...')
    recent_channels = get_recent_popular_videos(days=10, max_results=50)
    
    if not recent_channels:
        print('❌ No se pudieron obtener canales recientes')
        return
    
    print(f'✅ Encontrados {len(recent_channels)} canales únicos')
    
    # 2. Cargar datos existentes
    data = load_existing_data()
    
    # 3. Analizar cada canal
    updated_channels = []
    faceless_count = 0
    
    for channel in recent_channels:
        print(f'📊 Analizando: {channel["name"]}')
        channel_data = get_channel_stats(channel['id'])
        
        if channel_data:
            # Filtrar: solo canales faceless con ingresos > 1000€
            if (channel_data['is_likely_faceless'] and 
                channel_data['estimated_monthly_revenue'] >= 1000):
                
                faceless_count += 1
                print(f'✅ FACELESS DETECTADO: {channel_data["name"]}')
                print(f'   Ingresos: {channel_data["estimated_monthly_revenue"]}€')
                print(f'   Ratio vistas/sub: {channel_data["views_per_subscriber"]}')
                
                # Buscar si ya existe
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
            else:
                if not channel_data['is_likely_faceless']:
                    print(f'⚠️ {channel_data["name"]}: No parece faceless (score bajo)')
                else:
                    print(f'⚠️ {channel_data["name"]}: Ingresos < 1000€ ({channel_data["estimated_monthly_revenue"]}€)')
        else:
            print(f'❌ No se pudo analizar {channel["name"]}')
    
    # 4. Ordenar por ingresos (mayor a menor)
    updated_channels.sort(key=lambda x: x['estimated_monthly_revenue'], reverse=True)
    
    # 5. Guardar datos
    data['channels'] = updated_channels
    data['last_run'] = datetime.now().isoformat()
    save_data(data)
    
    print(f'\n✅ Análisis completado.')
    print(f'📊 Total canales analizados: {len(recent_channels)}')
    print(f'🎭 Canales faceless con >1000€: {faceless_count}')

if __name__ == '__main__':
    main()
