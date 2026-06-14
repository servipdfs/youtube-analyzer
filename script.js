async function loadData() {
  try {
    // Cache busting: agregar timestamp único para evitar caché
    const timestamp = Date.now();
    const response = await fetch(`data/channels.json?t=${timestamp}`, {
      cache: 'no-store',
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    const lastUpdate = new Date(data.last_run);
    document.getElementById('lastUpdate').textContent = 
      'Última actualización: ' + lastUpdate.toLocaleString('es-ES') + 
      ' (Recargado: ' + new Date().toLocaleTimeString('es-ES') + ')';
    
    displayChannels(data.channels);
    document.getElementById('loading').style.display = 'none';
    
  } catch (error) {
    console.error('Error loading data:', error);
    document.getElementById('loading').innerHTML = 
      '<p style="color:#fff;">Error al cargar los datos. Intenta de nuevo más tarde.</p>';
  }
}

function displayChannels(channels) {
  const grid = document.getElementById('channelsGrid');
  grid.innerHTML = '';
  
  if (!channels || channels.length === 0) {
    grid.innerHTML = '<p style="color:#fff; text-align:center;">No hay datos disponibles aún.</p>';
    return;
  }
  
  channels.forEach((channel, index) => {
    const card = document.createElement('div');
    card.className = 'channel-card';
    
    card.innerHTML = `
      <div class="channel-header">
        <img src="${channel.thumbnail}" alt="${channel.name}" class="channel-avatar">
        <div>
          <div class="channel-name">#${index + 1} ${channel.name}</div>
          <a href="https://youtube.com/channel/${channel.channel_id}" 
             target="_blank" class="channel-link">
            Ver en YouTube →
          </a>
        </div>
      </div>
      
      <div class="metrics">
        <div class="metric">
          <div class="metric-value">${formatNumber(channel.subscribers)}</div>
          <div class="metric-label">Suscriptores</div>
        </div>
        <div class="metric">
          <div class="metric-value">${formatNumber(channel.total_views)}</div>
          <div class="metric-label">Vistas totales</div>
        </div>
        <div class="metric">
          <div class="metric-value">${channel.video_count}</div>
          <div class="metric-label">Videos</div>
        </div>
        <div class="metric revenue">
          <div class="metric-value">${channel.estimated_monthly_revenue}€</div>
          <div class="metric-label">Ingresos/mes</div>
        </div>
      </div>
      
      <div class="channel-info">
        <p><strong>Ratio vistas/sub:</strong> ${channel.views_per_subscriber}</p>
        <p><strong>Antigüedad:</strong> ${channel.days_old} días</p>
      </div>
    `;
    
    grid.appendChild(card);
  });
}

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

loadData();
