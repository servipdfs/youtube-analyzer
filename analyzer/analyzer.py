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
    'health', 'fitness', 'workout', 'nutrition', 'wellness',
    'story', 'stories', 'animation', 'animated', 'cartoon',
    'timelapse', 'speed', 'fast', 'quick', 'short', 'clips',
    'reaction', 'reactions', 'commentary', 'explained', 'analysis',
    'meditation', 'sleep', 'nature', 'animals', 'pets', 'cute',
    'unbelievable', 'incredible', 'awesome', 'epic', 'ultimate',
    'compilation', 'mix', 'playlist', 'collection', 'archive',
    'news', 'updates', 'breaking', 'report', 'coverage',
    'podcast', 'audio', 'sound', 'beats', 'instrumental'
]

# Palabras clave que indican que NO es faceless (personas, grupos, etc.)
NON_FACELESS_KEYWORDS = [
    'official', 'channel', 'tv', 'show', 'live', 'stream',
    'vlog', 'vlogger', 'influencer', 'celebrity', 'star',
    'band', 'group', 'artist', 'singer', 'musician', 'rapper',
    'comedian', 'actor', 'actress', 'presenter', 'host',
    'gaming', 'gameplay', 'lets play', 'let\'s play', 'walkthrough',
    'twitch', 'streamer', 'youtuber', 'content creator',
    'personal', 'my channel', 'i am', 'i\'m', 'my name'
]

def get_recent_popular_videos(days=10, max_results=100):
    """Obtiene videos populares de los últimos N días"""
    try:
        published_after = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
        
        print(f'🔍 Buscando videos publicados después de: {published_after}')
        
        all_videos = []
        
        # Búsqueda por vistas
        search_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&order=viewCount&publishedAfter={published_after}&maxResults=50&key={API_KEY}'
        print(f'📡 Buscando por vistas...')
        
        response = requests.get(search_url)
        data = response.json()
        
        if 'items' in data:
            all_videos.extend(data['items'])
            print(f'✅ Obtenidos {len(data["items"])} videos por vistas')
        else:
            print(f'❌ Error en API: {data}')
        
        # Búsqueda por relevancia
        search_url2 = f'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&order=relevance&publishedAfter={published_after}&maxResults=50&key={API_KEY}'
        print(f'📡 Buscando por relevancia...')
        
        response2 = requests.get(search_url2)
        data2 = response2.json()
        
        if 'items' in data2:
            all_videos.extend(data2['items'])
            print(f'✅ Obtenidos {len(data2["items"])} videos por relevancia')
        
        # Eliminar duplicados
        seen = set()
        unique_videos = []
        for video in all_videos:
            video_id = video['id']['videoId']
            if video_id not in seen:
                seen.add(video_id)
                unique_videos.append(video)
        
        print(f'📊 Total videos únicos: {len(unique_videos)}')
        
        # Extraer canales únicos
        channels = {}
        for item in unique_videos:
            if 'channelId' in item['snippet']:
                channel_id = item['snippet']['channelId']
                channel_name = item['snippet']['channelTitle']
                
                if channel_id not in channels:
                    channels[channel_id] = {
                        'name': channel_name,
                        'id': channel_id
                    }
        
        print(f'🎯 Total canales únicos encontrados: {len(channels)}')
        return list(channels.values())
    
    except Exception as e:
        print(f'❌ Error getting recent videos: {e}')
        import traceback
        traceback.print_exc()
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
        monthly_views = total_views * 0.30 / 180
        estimated_revenue = (monthly_views * 3) / 1000
        
        # Detectar si es probablemente faceless
        is_likely_faceless, score, reasons = detect_faceless_channel(
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
            'faceless_score': score,
            'faceless_reasons': reasons,
            'last_updated': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f'  ❌ Error analyzing channel {channel_id}: {e}')
        return None

def detect_faceless_channel(name, subscribers, total_views, video_count, description):
    """Detecta si un canal es probablemente faceless basado en heurísticas mejoradas"""
    score = 0
    reasons = []
    
    name_lower = name.lower()
    description_lower = description.lower()
    combined_text = name_lower + ' ' + description_lower
    
    # CRITERIO 1: Verificar si tiene keywords de NO faceless (descartar inmediatamente)
    non_faceless_matches = [kw for kw in NON_FACELESS_KEYWORDS if kw in combined_text]
    if len(non_faceless_matches) >= 2:
        return False, 0, [f'Descartado: contiene keywords no-faceless: {non_faceless_matches}']
    
    # CRITERIO 2: Nombre genérico con keywords típicos de faceless
    faceless_matches = [kw for kw in FACELESS_KEYWORDS if kw in combined_text]
    if len(faceless_matches) >= 3:
        score += 4
        reasons.append(f'✅ Nombre/descripción con {len(faceless_matches)} keywords faceless')
    elif len(faceless_matches) >= 2:
        score += 2
        reasons.append(f'✅ Nombre/descripción con {len(faceless_matches)} keywords faceless')
    elif len(faceless_matches) >= 1:
        score += 1
        reasons.append(f'⚠️ Nombre/descripción con {len(faceless_matches)} keyword faceless')
    
    # CRITERIO 3: Ratio vistas/suscriptores muy alto (contenido viral sin personalidad)
    if subscribers > 0:
        views_per_sub = total_views / subscribers
        if views_per_sub > 500:
            score += 4
            reasons.append(f'✅ Ratio vistas/sub muy alto: {views_per_sub:.1f}')
        elif views_per_sub > 200:
            score += 3
            reasons.append(f'✅ Ratio vistas/sub alto: {views_per_sub:.1f}')
        elif views_per_sub > 100:
            score += 2
            reasons.append(f'⚠️ Ratio vistas/sub moderado: {views_per_sub:.1f}')
    
    # CRITERIO 4: Pocos videos pero muchas vistas (contenido automatizado)
    if video_count < 30 and total_views > 5000000:
        score += 4
        reasons.append(f'✅ Muy pocos videos ({video_count}) con muchas vistas')
    elif video_count < 100 and total_views > 1000000:
        score += 3
        reasons.append(f'✅ Pocos videos ({video_count}) con buenas vistas')
    elif video_count < 200 and total_views > 500000:
        score += 1
        reasons.append(f'⚠️ Videos moderados ({video_count})')
    
    # CRITERIO 5: Canal nuevo con crecimiento rápido
    if subscribers > 50000 and video_count < 50:
        score += 3
        reasons.append(f'✅ Canal nuevo con crecimiento rápido')
    elif subscribers > 10000 and video_count < 100:
        score += 2
        reasons.append(f'✅ Canal con buen crecimiento')
    
    # CRITERIO 6: Nombre con patrones genéricos (números, "TV", "Official", etc.)
    has_numbers = any(char.isdigit() for char in name)
    has_generic_terms = any(term in name_lower for term in ['tv', 'official', 'channel', 'hub', 'zone', 'world'])
    
    if has_numbers and len(name) < 25:
        score += 2
        reasons.append(f'✅ Nombre con números (patrón genérico)')
    if has_generic_terms:
        score += 1
        reasons.append(f'⚠️ Nombre con términos genéricos')
    
    # CRITERIO 7: Descripción corta o genérica
    if len(description) < 100:
        score += 1
        reasons.append(f'⚠️ Descripción muy corta')
    
    # Umbral estricto: score >= 6 para considerar faceless
    is_faceless = score >= 6
    
    return is_faceless, score, reasons

def load_existing_data():
    """Carga datos existentes"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'channels': [], 'last_run': None}

def save_data(data):
    """Guarda los datos"""
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'💾 Datos guardados en {DATA_FILE}')

def main():
    print('='*60)
    print('🚀 ANÁLISIS DE CANALES FACELESS (ESTRICTO)')
    print('📅 Últimos 10 días | 💰 Más de 1000€/mes')
    print('='*60)
    
    # 1. Obtener canales de videos recientes
    print('\n📊 PASO 1: Buscando videos populares de los últimos 10 días...')
    recent_channels = get_recent_popular_videos(days=10, max_results=100)
    
    if not recent_channels:
        print('❌ No se pudieron obtener canales recientes')
        return
    
    print(f'\n✅ Encontrados {len(recent_channels)} canales únicos para analizar\n')
    
    # 2. Cargar datos existentes
    data = load_existing_data()
    
    # 3. Analizar cada canal
    all_faceless_channels = []
    faceless_count = 0
    non_faceless_count = 0
    
    for i, channel in enumerate(recent_channels, 1):
        print(f'\n[{i}/{len(recent_channels)}] Analizando: {channel["name"]}')
        channel_data = get_channel_stats(channel['id'])
        
        if channel_data:
            if channel_data['is_likely_faceless']:
                faceless_count += 1
                print(f'  ✅ FACELESS DETECTADO (Score: {channel_data["faceless_score"]})')
                print(f'     📊 Vistas: {channel_data["total_views"]:,}')
                print(f'     💰 Ingresos: {channel_data["estimated_monthly_revenue"]}€')
                print(f'     👥 Subs: {channel_data["subscribers"]:,}')
                print(f'     📝 Razones: {", ".join(channel_data["faceless_reasons"][:3])}')
                
                all_faceless_channels.append(channel_data)
            else:
                non_faceless_count += 1
                print(f'  ❌ NO es faceless (Score: {channel_data["faceless_score"]})')
                if channel_data['faceless_reasons']:
                    print(f'     Razón: {channel_data["faceless_reasons"][0]}')
        else:
            print(f'  ❌ No se pudo analizar')
    
    # 4. Ordenar por visualizaciones totales (mayor a menor)
    print(f'\n📊 Ordenando {len(all_faceless_channels)} canales faceless por visualizaciones...')
    all_faceless_channels.sort(key=lambda x: x['total_views'], reverse=True)
    
    # 5. Tomar solo los 100 primeros
    top_100 = all_faceless_channels[:100]
    
    print(f'\n🏆 TOP 10 CANALES FACELESS:')
    for i, channel in enumerate(top_100[:10], 1):
        print(f'  #{i} {channel["name"]}')
        print(f'      Vistas: {channel["total_views"]:,} | Ingresos: {channel["estimated_monthly_revenue"]}€ | Score: {channel["faceless_score"]}')
    
    if len(top_100) > 10:
        print(f'  ... y {len(top_100) - 10} canales más')
    
    # 6. Guardar datos
    data['channels'] = top_100
    data['last_run'] = datetime.now().isoformat()
    save_data(data)
    
    print(f'\n' + '='*60)
    print('✅ ANÁLISIS COMPLETADO')
    print('='*60)
    print(f'📊 Total canales analizados: {len(recent_channels)}')
    print(f'🎭 Canales faceless encontrados: {faceless_count}')
    print(f'🚫 Canales NO faceless: {non_faceless_count}')
    print(f'🏆 Top 100 guardados: {len(top_100)}')
    print(f'⏰ Última ejecución: {data["last_run"]}')
    print('='*60)

if __name__ == '__main__':
    main()
