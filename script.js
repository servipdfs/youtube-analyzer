async function loadData() {
  try {
    const response = await fetch('data/channels.json');
    const data = await response.json();
    
    const lastUpdate = new Date(data.last_run);
    document.getElementById('lastUpdate').textContent = 
      'Última actualización: ' + lastUpdate.toLocaleString('es-ES');
    
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
  
  channels.sort((a, b) => b.subscribers - a.subscribers);
  
  channels.forEach(channel => {
    const card = document.createElement('div');
    card.className = 'channel-card';
    
    card.innerHTML = `
      <div class="channel-header">
        <img src="${channel.thumbnail}" alt="${channel.name}" class="channel-avatar">
        <div>
          <div class="channel-name">${channel.name}</div>
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
