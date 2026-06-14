import os
import json
import requests
from datetime import datetime, timedelta

# Configuración
API_KEY = os.environ.get('YOUTUBE_API_KEY')
DATA_FILE = 'data/channels.json'

# Términos de búsqueda para contenido viral faceless
VIRAL_FACELESS_TERMS = [
    'top 10', 'top 5', 'compilation', 'satisfying', 'asmr',
    'lofi', 'relaxing music', 'meditation', 'gaming highlights',
    'funny moments', 'fail compilation', 'motivational video',
    'facts', 'did you know', 'unbelievable', 'amazing facts',
    'how to make money', 'passive income', 'make money online',
    'crypto', 'bitcoin', 'stock market', 'investing',
    'workout motivation', 'gym motivation', 'cooking recipe',
    'nature', 'animals', 'cute', 'scary stories', 'horror',
    'true crime', 'mystery', 'tech review', 'unboxing',
    'life hacks', 'diy', 'study music', 'focus music',
    'rain sounds', 'white noise', 'sleep music',
    'reddit stories', 'storytime animation', 'animated'
]

def get_viral_videos(days=5, max_results=100):
    """Obtiene videos virales de canales faceless de los últimos días"""
    try:
        published_after = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
        
        all_videos = []
        
        print(f'🔍 Buscando videos publicados después de: {published_after}')
        
        # Buscar por cada término
        for term in VIRAL_FACELESS_TERMS:
            print(f'\n📺 Buscando: "{term}"')
            
            search_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&order=viewCount&publishedAfter={published_after}&q={term.replace(" ", "+")}&maxResults=25&key={API_KEY}'
            
            try:
                response = requests.get(search_url)
                data = response.json()
                
                if 'items' in data:
                    for item in data['items']:
                        video_id = item['id']['videoId']
                        video_title = item['snippet']['title']
                        channel_id = item['snippet']['channelId']
                        channel_name = item['snippet']['channelTitle']
                        published_at = item['snippet']['publishedAt']
                        
                        all_videos.append({
                            'video_id': video_id,
                            'title': video_title,
                            'channel_id': channel_id,
                            'channel_name': channel_name,
                            'published_at': published_at,
                            'search_term': term
                        })
                    
                    print(f'  ✅ {len(data["items"])} videos encontrados')
            
            except Exception as e:
                print(f'  ⚠️ Error: {e}')
                continue
        
        # Eliminar duplicados
        seen = set()
        unique_videos = []
        for video in all_videos:
            if video['video_id'] not in seen:
                seen.add(video['video_id'])
                unique_videos.append(video)
        
        print(f'\n📊 Total videos únicos: {len(unique_videos)}')
        return unique_videos
    
    except Exception as e:
        print(f'❌ Error: {e}')
        return []

def get_video_stats(video_id, channel_id):
    """Obtiene estadísticas del video y canal"""
    try:
        # Obtener stats del video
        video_url = f'https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id={video_id}&key={API_KEY}'
        response = requests.get(video_url)
        video_data = response.json()
        
        if 'items' not in video_data or len(video_data['items']) == 0:
            return None
        
        video_stats = video_data['items'][0]['statistics']
        video_snippet = video_data['items'][0]['snippet']
        
        # Obtener stats del canal
        channel_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={channel_id}&key={API_KEY}'
        channel_response = requests.get(channel_url)
        channel_data = channel_response.json()
        
        if 'items' not in channel_data or len(channel_data['items']) == 0:
            return None
        
        channel_stats = channel_data['items'][0]['statistics']
        channel_snippet = channel_data['items'][0]['snippet']
        
        views = int(video_stats.get('viewCount', 0))
        likes = int(video_stats.get('likeCount', 0))
        comments = int(video_stats.get('commentCount', 0))
        
        subscribers = int(channel_stats.get('subscriberCount', 0))
        channel_total_views = int(channel_stats.get('viewCount', 0))
        
        # Calcular ingresos del video (CPM promedio 3€)
        video_revenue = (views * 3) / 1000
        
        # Calcular ratio de engagement
        engagement_rate = ((likes + comments) / views * 100) if views > 0 else 0
        
        # Detectar si el canal es faceless
        is_faceless = detect_faceless_channel(
            channel_snippet['title'],
            channel_snippet.get('description', ''),
            subscribers,
            channel_total_views,
            int(channel_stats.get('videoCount', 0))
        )
        
        # Calcular días desde publicación
        published_at = datetime.fromisoformat(video_snippet['publishedAt'].replace('Z', '+00:00'))
        days_old = (datetime.now(published_at.tzinfo) - published_at).days
        
        # Calcular vistas por día
        views_per_day = views / days_old if days_old > 0 else views
        
        return {
            'video_id': video_id,
            'title': video_snippet['title'],
            'description': video_snippet.get('description', '')[:200],
            'thumbnail': video_snippet['thumbnails']['high']['url'],
            'channel_id': channel_id,
            'channel_name': channel_snippet['title'],
            'channel_thumbnail': channel_snippet['thumbnails']['default']['url'],
            'views': views,
            'likes': likes,
            'comments': comments,
            'subscribers': subscribers,
            'video_revenue': round(video_revenue, 2),
            'engagement_rate': round(engagement_rate, 3),
            'published_at': video_snippet['publishedAt'],
            'days_old': days_old,
            'views_per_day': round(views_per_day, 0),
            'is_faceless': is_faceless,
            'last_updated': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f'  ❌ Error: {e}')
        return None

def detect_faceless_channel(name, description, subscribers, total_views, video_count):
    """Detecta si el canal es faceless"""
    name_lower = name.lower()
    desc_lower = description.lower()
    combined = name_lower + ' ' + desc_lower
    
    # Palabras que indican NO faceless
    no_faceless = ['vlog', 'personal', 'official', 'band', 'singer', 'actor', 'twitch', 'streamer']
    for word in no_faceless:
        if word in combined:
            return False
    
    score = 0
    
    # Ratio vistas/sub alto
    if subscribers > 0 and (total_views / subscribers) > 100:
        score += 2
    
    # Pocos videos con muchas vistas
    if video_count < 100 and total_views > 1000000:
        score += 2
    
    # Nombre genérico
    generic = ['top', 'best', 'daily', 'facts', 'compilation', 'asmr', 'lofi', 'music', 'gaming']
    if any(g in name_lower for g in generic):
        score += 2
    
    return score >= 3

def load_existing_data():
    """Carga datos existentes"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'videos': [], 'last_run': None}

def save_data(data):
    """Guarda los datos"""
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'💾 Datos guardados en {DATA_FILE}')

def main():
    print('='*70)
    print('🎥 VIDEOS VIRALES FACELESS - Últimos 5 días')
    print('💰 Ordenados por ingresos generados')
    print('='*70)
    
    # 1. Obtener videos virales
    print('\n📊 Buscando videos virales...')
    viral_videos = get_viral_videos(days=5, max_results=100)
    
    if not viral_videos:
        print('❌ No se encontraron videos')
        return
    
    # 2. Analizar cada video
    print('\n📊 Analizando videos...')
    valid_videos = []
    
    for i, video in enumerate(viral_videos, 1):
        print(f'\n[{i}/{len(viral_videos)}] {video["title"][:60]}...')
        
        video_data = get_video_stats(video['video_id'], video['channel_id'])
        
        if video_data:
            # Filtrar: solo faceless con buenas vistas e ingresos
            if (video_data['is_faceless'] and 
                video_data['views'] >= 100000 and
                video_data['video_revenue'] >= 300):
                
                print(f'  ✅ VIRAL FACELESS')
                print(f'     👁️ {video_data["views"]:,} vistas')
                print(f'     💰 {video_data["video_revenue"]}€')
                print(f'     📅 {video_data["days_old"]} días')
                print(f'     📊 {video_data["views_per_day"]:,} vistas/día')
                
                valid_videos.append(video_data)
            else:
                if not video_data['is_faceless']:
                    print(f'  ❌ No es faceless')
                else:
                    print(f'  ⚠️ Pocas vistas o ingresos bajos')
    
    # 3. Ordenar por ingresos del video
    valid_videos.sort(key=lambda x: x['video_revenue'], reverse=True)
    
    # 4. Tomar top 100
    top_100 = valid_videos[:100]
    
    print(f'\n🏆 TOP 10 VIDEOS VIRALES FACELESS:')
    for i, v in enumerate(top_100[:10], 1):
        print(f'  #{i} {v["title"][:50]}...')
        print(f'      💰 {v["video_revenue"]}€ | 👁️ {v["views"]:,} | 📅 {v["days_old"]} días')
    
    # 5. Guardar
    data = load_existing_data()
    data['videos'] = top_100
    data['last_run'] = datetime.now().isoformat()
    save_data(data)
    
    print(f'\n✅ Completado: {len(top_100)} videos guardados')
    print('='*70)

if __name__ == '__main__':
    main()
