def main():
    print('🚀 Iniciando análisis de canales de los últimos 5 días...')
    
    # 1. Obtener canales de videos recientes
    print('📊 Buscando videos populares de los últimos 5 días...')
    recent_channels = get_recent_popular_videos(days=5, max_results=200)
    
    if not recent_channels:
        print('❌ No se pudieron obtener canales recientes')
        return
    
    print(f'✅ Encontrados {len(recent_channels)} canales únicos')
    
    # 2. Cargar datos existentes
    data = load_existing_data()
    
    # 3. Analizar cada canal
    all_channels = []
    faceless_count = 0
    total_analyzed = 0
    
    for channel in recent_channels:
        print(f'📊 Analizando: {channel["name"]}')
        channel_data = get_channel_stats(channel['id'])
        
        if channel_data:
            total_analyzed += 1
            
            # Detectar si es faceless
            if channel_data['is_likely_faceless']:
                faceless_count += 1
                channel_data['badge'] = '🎭 FACELESS'
                print(f'✅ FACELESS: {channel_data["name"]} - {channel_data["total_views"]:,} vistas')
            else:
                channel_data['badge'] = '👤 Personal'
                print(f'👤 {channel_data["name"]} - {channel_data["total_views"]:,} vistas')
            
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
                all_channels.append(existing)
            else:
                channel_data['history'] = [{
                    'date': datetime.now().isoformat(),
                    'subscribers': channel_data['subscribers'],
                    'total_views': channel_data['total_views'],
                    'estimated_revenue': channel_data['estimated_monthly_revenue']
                }]
                all_channels.append(channel_data)
        else:
            print(f'❌ No se pudo analizar {channel["name"]}')
    
    # 4. Ordenar por visualizaciones totales (mayor a menor)
    all_channels.sort(key=lambda x: x['total_views'], reverse=True)
    
    # 5. Tomar solo los 100 primeros (MIXTOS: faceless y personales)
    top_100 = all_channels[:100]
    
    # 6. Guardar datos
    data['channels'] = top_100
    data['last_run'] = datetime.now().isoformat()
    save_data(data)
    
    print(f'\n✅ Análisis completado.')
    print(f'📊 Total canales analizados: {total_analyzed}')
    print(f'🎭 Canales faceless encontrados: {faceless_count}')
    print(f'👤 Canales personales: {total_analyzed - faceless_count}')
    print(f'🏆 Top 100 guardados (ordenados por visualizaciones)')
    
    # Mostrar resumen
    faceless_in_top100 = sum(1 for c in top_100 if c.get('is_likely_faceless', False))
    print(f'\n📈 En el TOP 100:')
    print(f'   🎭 Faceless: {faceless_in_top100}')
    print(f'   👤 Personales: {100 - faceless_in_top100}')
