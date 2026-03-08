// GitHub-Radar Visualization
// Renders a technology radar as SVG with interactive features

const QUADRANTS = [
  { name: 'AI Workflow & Orchestration', color: '#f78166', angle: 0 },
  { name: 'Libraries & Frameworks', color: '#d2a8ff', angle: 90 },
  { name: 'Developer Tools & Infra', color: '#58a6ff', angle: 180 },
  { name: 'Patterns & Methods', color: '#3fb950', angle: 270 }
];

const RINGS = [
  { name: 'Adopt', radius: 0.28, color: '#3fb950' },
  { name: 'Trial', radius: 0.52, color: '#d29922' },
  { name: 'Scout', radius: 0.78, color: '#58a6ff' },
  { name: 'Hold', radius: 1.0, color: '#8b949e' }
];

const CX = 400, CY = 400, MAX_R = 360;
let entries = [];
let activeFilter = 'all';
let activeRingFilter = 'all';
let searchQuery = '';
let sortColumn = 'quality';
let sortDesc = true;

// Seed-based pseudo-random for consistent dot placement
function seededRandom(seed) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = ((h << 5) - h + seed.charCodeAt(i)) | 0;
  }
  return function() {
    h = (h * 16807 + 0) % 2147483647;
    return (h & 0x7fffffff) / 2147483647;
  };
}

function polarToCartesian(angle, radius) {
  const rad = (angle - 90) * Math.PI / 180;
  return {
    x: CX + radius * Math.cos(rad),
    y: CY + radius * Math.sin(rad)
  };
}

function getQuadrantIndex(quadrant) {
  return QUADRANTS.findIndex(q => q.name === quadrant);
}

function getRingIndex(ring) {
  return RINGS.findIndex(r => r.name === ring);
}

function getEntryPosition(entry) {
  const qi = getQuadrantIndex(entry.quadrant);
  const ri = getRingIndex(entry.ring);
  if (qi < 0 || ri < 0) return null;

  const rng = seededRandom(entry.id);
  const innerR = ri === 0 ? 0 : RINGS[ri - 1].radius;
  const outerR = RINGS[ri].radius;
  const r = (innerR + (outerR - innerR) * (0.25 + rng() * 0.5)) * MAX_R;

  const baseAngle = qi * 90;
  const angle = baseAngle + 10 + rng() * 70;

  return polarToCartesian(angle, r);
}

function formatStars(n) {
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
  return n.toString();
}

function renderRadar(filteredEntries) {
  const svg = document.getElementById('radar');
  svg.innerHTML = '';

  // Background
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.innerHTML = `
    <radialGradient id="bg-grad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#1a2030"/>
      <stop offset="100%" stop-color="#0d1117"/>
    </radialGradient>
  `;
  svg.appendChild(defs);

  // Rings (outer to inner)
  for (let i = RINGS.length - 1; i >= 0; i--) {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', CX);
    circle.setAttribute('cy', CY);
    circle.setAttribute('r', RINGS[i].radius * MAX_R);
    circle.setAttribute('fill', i === RINGS.length - 1 ? 'url(#bg-grad)' : 'none');
    circle.setAttribute('stroke', '#30363d');
    circle.setAttribute('stroke-width', '1');
    svg.appendChild(circle);
  }

  // Quadrant lines
  for (let i = 0; i < 4; i++) {
    const angle = i * 90;
    const end = polarToCartesian(angle, MAX_R);
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', CX);
    line.setAttribute('y1', CY);
    line.setAttribute('x2', end.x);
    line.setAttribute('y2', end.y);
    line.setAttribute('stroke', '#30363d');
    line.setAttribute('stroke-width', '1');
    svg.appendChild(line);
  }

  // Ring labels
  RINGS.forEach((ring, i) => {
    const y = CY - ring.radius * MAX_R + 16;
    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', CX + 4);
    label.setAttribute('y', y);
    label.setAttribute('fill', ring.color);
    label.setAttribute('font-size', '11');
    label.setAttribute('font-weight', '600');
    label.setAttribute('opacity', '0.6');
    label.textContent = ring.name;
    svg.appendChild(label);
  });

  // Quadrant labels
  QUADRANTS.forEach((q, i) => {
    const angle = i * 90 + 45;
    const pos = polarToCartesian(angle, MAX_R + 8);
    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', pos.x);
    label.setAttribute('y', pos.y);
    label.setAttribute('fill', q.color);
    label.setAttribute('font-size', '12');
    label.setAttribute('font-weight', '700');
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('opacity', '0.8');

    // Wrap long names
    const words = q.name.split(' & ');
    if (words.length > 1) {
      words.forEach((w, wi) => {
        const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
        tspan.setAttribute('x', pos.x);
        tspan.setAttribute('dy', wi === 0 ? '0' : '14');
        tspan.textContent = wi === 0 ? w + ' &' : w;
        label.appendChild(tspan);
      });
    } else {
      label.textContent = q.name;
    }
    svg.appendChild(label);
  });

  // Entry dots
  filteredEntries.forEach(entry => {
    const pos = getEntryPosition(entry);
    if (!pos) return;

    const qi = getQuadrantIndex(entry.quadrant);
    const color = QUADRANTS[qi].color;

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('class', 'entry-dot');
    g.setAttribute('data-id', entry.id);
    g.style.cursor = 'pointer';

    // Glow
    const glow = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    glow.setAttribute('cx', pos.x);
    glow.setAttribute('cy', pos.y);
    glow.setAttribute('r', entry.tested ? 10 : 7);
    glow.setAttribute('fill', color);
    glow.setAttribute('opacity', '0.15');
    g.appendChild(glow);

    // Dot
    const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dot.setAttribute('cx', pos.x);
    dot.setAttribute('cy', pos.y);
    dot.setAttribute('r', entry.tested ? 6 : 4);
    dot.setAttribute('fill', color);
    dot.setAttribute('stroke', entry.tested ? '#fff' : 'none');
    dot.setAttribute('stroke-width', entry.tested ? '1.5' : '0');
    g.appendChild(dot);

    // Label — hidden by default, visible on hover (always visible for Adopt)
    const isAdopt = entry.ring === 'Adopt';
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', pos.x);
    text.setAttribute('y', pos.y - 12);
    text.setAttribute('fill', '#e6edf3');
    text.setAttribute('font-size', '10');
    text.setAttribute('font-weight', '600');
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('class', 'dot-label');
    if (!isAdopt) text.setAttribute('opacity', '0');
    text.textContent = entry.name.length > 20 ? entry.name.substring(0, 18) + '..' : entry.name;
    g.appendChild(text);

    // Events
    g.addEventListener('mouseenter', (e) => {
      showTooltip(e, entry);
      if (!isAdopt) text.setAttribute('opacity', '1');
      glow.setAttribute('r', entry.tested ? 14 : 10);
      glow.setAttribute('opacity', '0.3');
    });
    g.addEventListener('mouseleave', () => {
      hideTooltip();
      if (!isAdopt) text.setAttribute('opacity', '0');
      glow.setAttribute('r', entry.tested ? 10 : 7);
      glow.setAttribute('opacity', '0.15');
    });
    g.addEventListener('click', () => showDetails(entry));

    svg.appendChild(g);
  });
}

function showTooltip(event, entry) {
  const tooltip = document.getElementById('tooltip');
  const ri = getRingIndex(entry.ring);
  const ringColor = RINGS[ri]?.color || '#fff';

  tooltip.innerHTML = `
    <div class="tt-name">${entry.name}</div>
    <div class="tt-desc">${entry.description}</div>
    <div class="tt-meta">
      <span style="color:${ringColor}">${entry.ring}</span> ·
      ${formatStars(entry.stars)} Stars ·
      ${entry.language} ·
      ${entry.tested ? 'Getestet' : 'Nicht getestet'}
    </div>
  `;
  tooltip.classList.add('visible');

  const rect = document.querySelector('.radar-container').getBoundingClientRect();
  const svgRect = document.getElementById('radar').getBoundingClientRect();
  const scale = svgRect.width / 800;

  tooltip.style.left = (event.clientX - rect.left + 15) + 'px';
  tooltip.style.top = (event.clientY - rect.top - 10) + 'px';
}

function hideTooltip() {
  document.getElementById('tooltip').classList.remove('visible');
}

function showDetails(entry) {
  const panel = document.getElementById('details-panel');
  const content = document.getElementById('details-content');
  const ri = getRingIndex(entry.ring);
  const ringClass = entry.ring.toLowerCase();

  content.innerHTML = `
    <h3><a href="${entry.url}" target="_blank">${entry.name}</a> <span class="ring-badge ${ringClass}">${entry.ring}</span></h3>
    <div class="detail-row"><span class="detail-label">Quadrant</span><span class="detail-value">${entry.quadrant}</span></div>
    <div class="detail-row"><span class="detail-label">Stars</span><span class="detail-value">${formatStars(entry.stars)}</span></div>
    <div class="detail-row"><span class="detail-label">Sprache</span><span class="detail-value">${entry.language}</span></div>
    <div class="detail-row"><span class="detail-label">Lizenz</span><span class="detail-value">${entry.license}</span></div>
    <div class="detail-row"><span class="detail-label">Hinzugefuegt</span><span class="detail-value">${entry.added}</span></div>
    <div class="detail-section"><h4>Beschreibung</h4><p>${entry.description}</p></div>
    <div class="detail-section"><h4>Staerken</h4><p>${entry.strengths}</p></div>
    <div class="detail-section"><h4>Schwaechen</h4><p>${entry.weaknesses}</p></div>
    <div class="detail-section"><h4>Was ich gelernt habe</h4><p>${entry.learned}</p></div>
    ${entry.signals ? `
    <div class="detail-section signals-section">
      <h4>Quality Score: ${entry.quality_score}/10</h4>
      <div class="signal-bars">
        ${Object.entries(entry.signals).map(([key, val]) => {
          const labels = {notable_density:'Notable Density',bus_factor:'Bus Factor',freshness:'Freshness',issue_health:'Issue Health',star_velocity:'Star Velocity'};
          const barClass = val >= 7 ? 'bar-high' : val >= 4 ? 'bar-mid' : 'bar-low';
          return `<div class="signal-bar-row">
            <span class="signal-bar-label">${labels[key] || key}</span>
            <div class="signal-bar-track"><div class="signal-bar-fill ${barClass}" style="width:${val*10}%"></div></div>
            <span class="signal-bar-val">${val}</span>
          </div>`;
        }).join('')}
      </div>
      <div class="signal-details">
        Bus Factor: ${entry.bus_factor || '?'} · Letzter Commit: ${entry.days_since_commit != null ? (entry.days_since_commit === 0 ? 'heute' : entry.days_since_commit + 'd') : '?'} · Issues: ${entry.closed_issues || 0}/${(entry.open_issues||0)+(entry.closed_issues||0)} geschlossen · Forks: ${entry.forks || 0}
      </div>
    </div>` : ''}
    ${entry.notable_stargazers && entry.notable_stargazers.length > 0 ? `
    <div class="detail-section notable-section">
      <h4>Notable Stargazers <span class="signal-meta">Coverage: ${entry.notable_coverage_pct || '?'}%</span></h4>
      <ul class="notable-list">
        ${entry.notable_stargazers.map(u => `<li><a href="https://github.com/${u.login}" target="_blank">${u.label}</a> <span class="follower-count">${formatStars(u.followers)} Followers</span></li>`).join('')}
      </ul>
    </div>` : `<div class="detail-section notable-section"><h4>Notable Stargazers</h4><p class="no-notables">Keine (in Stichprobe von 200)</p></div>`}
  `;
  panel.classList.remove('hidden');
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function closeDetails() {
  document.getElementById('details-panel').classList.add('hidden');
}

function getSortValue(entry, col) {
  switch (col) {
    case 'name': return entry.name.toLowerCase();
    case 'quadrant': return entry.quadrant.toLowerCase();
    case 'ring': return ['Adopt','Trial','Scout','Hold'].indexOf(entry.ring);
    case 'stars': return entry.stars || 0;
    case 'language': return (entry.language || '').toLowerCase();
    case 'quality': return entry.quality_score || 0;
    case 'tested': return entry.tested ? 1 : 0;
    default: return 0;
  }
}

function renderTable(filteredEntries) {
  const tbody = document.querySelector('#entries-table tbody');
  tbody.innerHTML = '';

  const sorted = [...filteredEntries].sort((a, b) => {
    const va = getSortValue(a, sortColumn);
    const vb = getSortValue(b, sortColumn);
    const cmp = typeof va === 'string' ? va.localeCompare(vb) : va - vb;
    return sortDesc ? -cmp : cmp;
  });

  // Update sort arrows
  document.querySelectorAll('#entries-table th').forEach(th => {
    const arrow = th.querySelector('.sort-arrow');
    if (!arrow) return;
    if (th.dataset.sort === sortColumn) {
      arrow.textContent = sortDesc ? ' ↓' : ' ↑';
      th.classList.add('sorted');
    } else {
      arrow.textContent = '';
      th.classList.remove('sorted');
    }
  });

  sorted.forEach(entry => {
    const ringClass = entry.ring.toLowerCase();
    const tr = document.createElement('tr');
    tr.addEventListener('click', (e) => {
      if (e.target.tagName === 'A') e.preventDefault();
      showDetails(entry);
    });
    const qs = entry.quality_score || 0;
    const cov = entry.notable_coverage_pct || 0;
    const qClass = qs >= 7 ? 'signal-high' : qs >= 5 ? 'signal-mid' : qs > 0 ? 'signal-low' : 'signal-none';
    tr.innerHTML = `
      <td><a href="${entry.url}" target="_blank">${entry.name}</a></td>
      <td>${entry.quadrant}</td>
      <td><span class="ring-badge ${ringClass}">${entry.ring}</span></td>
      <td class="stars-cell">${formatStars(entry.stars)}</td>
      <td>${entry.language}</td>
      <td class="signal-cell ${qClass}">${qs > 0 ? `${qs.toFixed(1)}<span class="coverage-hint">${cov}%</span>` : '-'}</td>
      <td>${entry.tested ? 'Ja' : '-'}</td>
    `;
    tbody.appendChild(tr);
  });
}

function updateStats(filteredEntries) {
  document.getElementById('stat-total').textContent = filteredEntries.length;
  document.getElementById('stat-tested').textContent = filteredEntries.filter(e => e.tested).length;
  document.getElementById('stat-adopted').textContent = filteredEntries.filter(e => e.ring === 'Adopt').length;

  const dates = filteredEntries.map(e => e.added).sort().reverse();
  document.getElementById('stat-updated').textContent = dates[0] || '-';
}

function applyFilters() {
  const radarEntries = entries.filter(e => e.category !== 'landscape');
  let filtered = radarEntries;
  if (activeFilter !== 'all') {
    filtered = filtered.filter(e => e.quadrant === activeFilter);
  }
  if (activeRingFilter !== 'all') {
    filtered = filtered.filter(e => e.ring === activeRingFilter);
  }
  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    filtered = filtered.filter(e =>
      e.name.toLowerCase().includes(q) ||
      (e.description || '').toLowerCase().includes(q) ||
      (e.language || '').toLowerCase().includes(q) ||
      (e.quadrant || '').toLowerCase().includes(q) ||
      (e.ring || '').toLowerCase().includes(q) ||
      (e.strengths || '').toLowerCase().includes(q) ||
      (e.weaknesses || '').toLowerCase().includes(q)
    );
  }
  renderRadar(filtered);
  renderTable(filtered);
  updateStats(filtered);
  renderLandscape();
}

function renderLandscape() {
  const tbody = document.querySelector('#landscape-table tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const landscape = entries.filter(e => e.category === 'landscape');
  landscape.sort((a, b) => (b.quality_score || 0) - (a.quality_score || 0));
  landscape.forEach(entry => {
    const tr = document.createElement('tr');
    tr.addEventListener('click', () => showDetails(entry));
    tr.style.cursor = 'pointer';
    const qs = entry.quality_score || 0;
    const qClass = qs >= 7 ? 'signal-high' : qs >= 5 ? 'signal-mid' : 'signal-low';
    const reason = entry.ring === 'Hold' ? entry.learned || entry.weaknesses : (entry.weaknesses || '');
    const short = reason.length > 80 ? reason.substring(0, 77) + '...' : reason;
    tr.innerHTML = `
      <td><a href="${entry.url}" target="_blank">${entry.name}</a></td>
      <td class="stars-cell">${formatStars(entry.stars)}</td>
      <td class="signal-cell ${qClass}">${qs.toFixed(1)}</td>
      <td class="reason-cell">${short}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Quadrant filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const quadrant = btn.dataset.quadrant;
    activeFilter = btn.dataset.filter || quadrant;
    applyFilters();
  });
});

// Ring filter badges (in legend)
document.querySelectorAll('.legend .ring-badge').forEach(badge => {
  badge.style.cursor = 'pointer';
  badge.addEventListener('click', () => {
    const ring = badge.textContent.trim();
    if (activeRingFilter === ring) {
      activeRingFilter = 'all';
      document.querySelectorAll('.legend .ring-badge').forEach(b => b.classList.remove('ring-inactive'));
    } else {
      activeRingFilter = ring;
      document.querySelectorAll('.legend .ring-badge').forEach(b => {
        b.classList.toggle('ring-inactive', b.textContent.trim() !== ring);
      });
    }
    applyFilters();
  });
});

// Table sorting
document.querySelectorAll('#entries-table th[data-sort]').forEach(th => {
  th.style.cursor = 'pointer';
  th.addEventListener('click', () => {
    const col = th.dataset.sort;
    if (sortColumn === col) {
      sortDesc = !sortDesc;
    } else {
      sortColumn = col;
      sortDesc = ['stars', 'quality', 'tested'].includes(col);
    }
    applyFilters();
  });
});

// Search input
document.getElementById('search-input').addEventListener('input', (e) => {
  searchQuery = e.target.value.trim();
  applyFilters();
});

// Load data
async function init() {
  try {
    const response = await fetch('data/entries.json');
    entries = await response.json();
  } catch (e) {
    console.error('Could not load entries.json', e);
    return;
  }
  applyFilters();
}

init();
