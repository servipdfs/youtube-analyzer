import os
import json
import requests
from datetime import datetime, timedelta

# Configuración
API_KEY = os.environ.get('YOUTUBE_API_KEY')
DATA_FILE = 'data/channels.json'

# Términos de búsqueda específicos para contenido faceless
FACELESS_SEARCH_TERMS = [
    'top 10', 'top 5', 'compilation', 'satisfying video', 'asmr',
    'lofi hip hop', 'relaxing music', 'meditation music',
    'gaming highlights', 'funny moments', 'fail compilation',
    'motivational video', 'facts you didnt know', 'did you know',
    'unbelievable facts', 'amazing facts', 'interesting facts',
    'how to make money', 'passive income', 'make money online',
    'crypto news', 'bitcoin news', 'stock market',
    'workout motivation', 'gym motivation', 'fitness tips',
    'cooking recipe', 'easy recipe', 'food compilation',
    'nature documentary', 'animal compilation', 'cute animals',
    'scary stories', 'creepy pasta', 'horror stories',
    'true crime', 'mystery', 'unsolved mysteries',
    'tech review', 'gadget review', 'unboxing',
    'life hacks', 'diy projects', 'craft ideas',
    'study music', 'focus music', 'sleep music',
    'rain sounds', 'white noise', 'calming sounds',
    'ai news', 'technology news', 'future technology',
    'money saving tips', 'investing for beginners',
    'storytime animation', 'animated story',
    'reddit stories', 'askreddit', 'entitled parents',
    'protonmail', 'instant regret', 'malicious compliance'
]

def search_faceless_videos(max_results=100):
    """Busca videos de canales faceless usando términos específicos"""
    try:
        published_after = (datetime.utcnow() - timedelta(days=10)).isoformat() + 'Z'
        
        all_channels = {}
        
        for term in FACELESS_SEARCH_TERMS:
            print(f'🔍 Buscando: "{term}"')
            
            search_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&order=viewCount&publishedAfter={published_after}&q={term.replace(" ", "+")}&maxResults=25&key={API_KEY}'
            
            try:
                response = requests.get(search_url)
                data = response.json()
                
                if 'items' in data:
                    for item in data['items']:
                        if 'channelId' in item['snippet']:
                            channel_id = item['snippet']['channelId']
                            channel_name = item['snippet']['channelTitle']
                            
                            if channel_id not in all_channels:
                                all_channels[channel_id] = {
                                    'name': channel_name,
                                    'id': channel_id,
                                    'search_term': term
                                }
            except Exception as e:
                print(f'  ⚠️ Error en búsqueda: {e}')
                continue
        
        print(f'\n✅ Encontrados {len(all_channels)} canales únicos')
        return list(all_channels.values())
    
    except Exception as e:
        print(f'❌ Error searching videos: {e}')
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
        
        # Calcular ingresos estimados
        monthly_views = total_views * 0.30 / 180
        estimated_revenue = (monthly_views * 3) / 1000
        
        # Calcular ratio vistas/suscriptores
        views_per_sub = total_views / subscribers if subscribers > 0 else 0
        
        # Calcular días desde creación
        published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
        days_old = (datetime.now(published_at.tzinfo) - published_at).days
        
        # Detectar si es faceless
        is_faceless = detect_faceless(
            snippet['title'],
            snippet.get('description', ''),
            subscribers,
            total_views,
            video_count,
            views_per_sub
        )
        
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
            'is_likely_faceless': is_faceless,
            'last_updated': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f'  ❌ Error: {e}')
        return None

def detect_faceless(name, description, subscribers, total_views, video_count, views_per_sub):
    """Detecta si es canal faceless con criterios estrictos"""
    
    name_lower = name.lower()
    desc_lower = description.lower()
    combined = name_lower + ' ' + desc_lower
    
    # Palabras que indican NO faceless
    no_faceless_words = [
        'official', 'vlog', 'personal', 'my life', 'daily vlog',
        'band', 'group', 'singer', 'artist', 'musician',
        'actor', 'actress', 'comedian', 'presenter',
        'twitch', 'streamer', 'lets play', 'gameplay'
    ]
    
    # Si tiene palabras de no-faceless, descartar
    for word in no_faceless_words:
        if word in combined:
            return False
    
    # Criterios para ser faceless:
    score = 0
    
    # 1. Ratio vistas/sub muy alto
    if views_per_sub > 200:
        score += 3
    elif views_per_sub > 100:
        score += 2
    
    # 2. Pocos videos con muchas vistas
    if video_count < 100 and total_views > 1000000:
        score += 2
    
    # 3. Nombre genérico
    generic_patterns = ['top', 'best', 'daily', 'facts', 'compilation', 'asmr', 'lofi', 'music', 'gaming', 'highlights']
    if any(pattern in name_lower for pattern in generic_patterns):
        score += 2
    
    # 4. Descripción corta o genérica
    if len(description) < 150:
        score += 1
    
    # Necesita al menos 4 puntos para ser faceless
    return score >= 4

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

def main():
    print('='*70)
    print('🎭 BUSCANDO CANALES FACELESS - Últimos 10 días')
    print('='*70)
    
    # 1. Buscar videos faceless
    print('\n📊 Buscando videos con términos faceless...')
    faceless_channels = search_faceless_videos(max_results=100)
    
    if not faceless_channels:
        print('❌ No se encontraron canales')
        return
    
    # 2. Analizar cada canal
    print('\n📊 Analizando canales...')
    valid_channels = []
    
    for i, channel in enumerate(faceless_channels, 1):
        print(f'\n[{i}/{len(faceless_channels)}] {channel["name"]}')
        
        channel_data = get_channel_stats(channel['id'])
        
        if channel_data:
            # Filtrar: solo faceless con > 1000€
            if (channel_data['is_likely_faceless'] and 
                channel_data['estimated_monthly_revenue'] >= 1000):
                
                print(f'  ✅ FACELESS - {channel_data["total_views"]:,} vistas - {channel_data["estimated_monthly_revenue"]}€')
                valid_channels.append(channel_data)
            else:
                if not channel_data['is_likely_faceless']:
                    print(f'  ❌ No es faceless')
                else:
                    print(f'  ⚠️ Ingresos bajos: {channel_data["estimated_monthly_revenue"]}€')
    
    # 3. Ordenar por vistas
    valid_channels.sort(key=lambda x: x['total_views'], reverse=True)
    
    # 4. Tomar top 100
    top_100 = valid_channels[:100]
    
    print(f'\n🏆 TOP 10 CANALES FACELESS:')
    for i, ch in enumerate(top_100[:10], 1):
        print(f'  #{i} {ch["name"]}: {ch["total_views"]:,} vistas - {ch["estimated_monthly_revenue"]}€')
    
    # 5. Guardar
    data = load_existing_data()
    data['channels'] = top_100
    data['last_run'] = datetime.now().isoformat()
    save_data(data)
    
    print(f'\n✅ Completado: {len(top_100)} canales guardados')

if __name__ == '__main__':
    main()
