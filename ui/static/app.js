// ProspectaChile B2B Frontend Logic
let currentCompanies = [];
let selectedRouteCompanies = [];
let map = null;
let markersLayer = null;
let currentModalRut = null;
let currentPage = 0;
const pageSize = 50;
let totalResults = 0;

document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  initMap();
  loadStats();
  loadFilters();
  applyFilters();
  loadCorridors('PROVIDENCIA');
});

// INITIALIZE LEAFLET MAP
function initMap() {
  map = L.map('map').setView([-33.4372, -70.6300], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
  markersLayer = L.layerGroup().addTo(map);
}

function recenterMap() {
  if (markersLayer.getLayers().length > 0) {
    const group = new L.featureGroup(markersLayer.getLayers());
    map.fitBounds(group.getBounds().pad(0.1));
  } else {
    map.setView([-33.4372, -70.6300], 12);
  }
}

// SWITCH TABS
function switchTab(tabId) {
  ['explorer', 'routes', 'crm'].forEach(t => {
    document.getElementById(`view-${t}`).classList.add('hidden');
    const btn = document.getElementById(`tab-btn-${t}`);
    btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-sm');
    btn.classList.add('text-slate-300', 'hover:text-white', 'hover:bg-slate-800');
  });

  document.getElementById(`view-${tabId}`).classList.remove('hidden');
  const activeBtn = document.getElementById(`tab-btn-${tabId}`);
  activeBtn.classList.add('bg-indigo-600', 'text-white', 'shadow-sm');
  activeBtn.classList.remove('text-slate-300', 'hover:text-white', 'hover:bg-slate-800');

  if (tabId === 'explorer') {
    setTimeout(() => { map.invalidateSize(); }, 200);
  } else if (tabId === 'routes') {
    renderRoutesTab();
  } else if (tabId === 'crm') {
    renderCrmTab();
  }
}

// LOAD METRIC STATS
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('stat-total').innerText = data.total.toLocaleString();
    document.getElementById('stat-activas').innerText = data.activas.toLocaleString();
    document.getElementById('stat-pymes').innerText = Math.round(data.total * 0.72).toLocaleString();
    document.getElementById('stat-prospectos').innerText = data.prospectos_crm;
    document.getElementById('badge-crm-count').innerText = data.prospectos_crm;
  } catch (e) {
    console.error('Error loading stats:', e);
  }
}

// LOAD FILTER OPTIONS
async function loadFilters() {
  try {
    const res = await fetch('/api/filters');
    const data = await res.json();
    
    const comSelect = document.getElementById('filter-comuna');
    data.comunas.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.innerText = c;
      comSelect.appendChild(opt);
    });

    const rubroSelect = document.getElementById('filter-rubro');
    data.rubros.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r;
      opt.innerText = r;
      rubroSelect.appendChild(opt);
    });
  } catch (e) {
    console.error('Error loading filters:', e);
  }
}

// APPLY FILTERS & FETCH COMPANIES
async function applyFilters(page = 0) {
  currentPage = page;
  const q = document.getElementById('filter-q').value;
  const comuna = document.getElementById('filter-comuna').value;
  const rubro = document.getElementById('filter-rubro').value;
  const tramo = document.getElementById('filter-tramo').value;
  const trab = document.getElementById('filter-trabajadores').value;
  const activas = document.getElementById('filter-activas').checked;

  const params = new URLSearchParams({
    q: q,
    comuna: comuna,
    rubro: rubro,
    tramo_min: tramo,
    trabajadores_min: trab,
    solo_activas: activas ? 'true' : 'false',
    limit: pageSize,
    offset: currentPage * pageSize
  });

  document.getElementById('results-count').innerText = 'Filtrando universo...';
  
  try {
    const res = await fetch(`/api/companies?${params.toString()}`);
    const data = await res.json();
    currentCompanies = data.results;
    totalResults = data.total;

    document.getElementById('results-count').innerText = `${totalResults.toLocaleString()} empresas activas encontradas`;
    renderTable(currentCompanies);
    renderMapMarkers(currentCompanies);
    updatePagination();
    
    if (comuna) {
      loadCorridors(comuna);
    }
  } catch (e) {
    console.error('Error fetching companies:', e);
  }
}

// RENDER COMPANY TABLE
function renderTable(companies) {
  const tbody = document.getElementById('company-table-body');
  tbody.innerHTML = '';

  if (companies.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-8 text-slate-400">No se encontraron empresas con los filtros seleccionados.</td></tr>`;
    return;
  }

  companies.forEach(comp => {
    const inRoute = selectedRouteCompanies.some(r => r.rut === comp.rut);
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-indigo-50/40 transition cursor-pointer';

    const tramoBadge = comp.tramo_ventas >= 8 ? 
      '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">Mediana (Tramo ' + comp.tramo_ventas + ')</span>' :
      '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">PyME (Tramo ' + comp.tramo_ventas + ')</span>';

    const crmBadge = comp.crm_estado !== 'Nuevo' ?
      `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-100 text-purple-800">${comp.crm_estado}</span>` :
      `<span class="text-slate-400 text-[10px]">Sin contactar</span>`;

    tr.innerHTML = `
      <td class="p-3" onclick="openModal('${comp.rut}')">
        <div class="font-bold text-slate-900 hover:text-indigo-600">${comp.razon_social}</div>
        <div class="text-[10px] text-slate-400 font-mono">${comp.rut}-${comp.dv} &bull; ${comp.rubro.substring(0, 32)}...</div>
      </td>
      <td class="p-3" onclick="openModal('${comp.rut}')">
        <div class="font-medium text-slate-800">${comp.calle} ${comp.numero || ''} ${comp.depto || ''}</div>
        <div class="text-[10px] text-slate-400">${comp.comuna}</div>
      </td>
      <td class="p-3 text-center" onclick="openModal('${comp.rut}')">
        <div>${tramoBadge}</div>
        <div class="text-[10px] text-slate-500 mt-0.5">${comp.trabajadores} trabajadores</div>
      </td>
      <td class="p-3 text-center" onclick="openModal('${comp.rut}')">
        ${crmBadge}
      </td>
      <td class="p-3 text-right">
        <button onclick="event.stopPropagation(); toggleRouteItem('${comp.rut}')" 
                class="px-2.5 py-1 rounded text-xs font-semibold transition ${inRoute ? 'bg-rose-50 text-rose-600 border border-rose-200' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200'}">
          ${inRoute ? 'Quitar' : '+ Ruta'}
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  lucide.createIcons();
}

// RENDER MAP MARKERS
function renderMapMarkers(companies) {
  markersLayer.clearLayers();
  
  companies.forEach(comp => {
    if (!comp.lat || !comp.lon) return;

    const isMediana = comp.tramo_ventas >= 8;
    const marker = L.circleMarker([comp.lat, comp.lon], {
      radius: 6,
      fillColor: isMediana ? '#10b981' : '#3b82f6',
      color: '#ffffff',
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.85
    });

    marker.bindPopup(`
      <div class="text-xs space-y-1">
        <strong class="text-slate-900 block font-bold">${comp.razon_social}</strong>
        <div class="text-slate-600">${comp.calle} ${comp.numero || ''}, ${comp.comuna}</div>
        <div class="text-[11px] font-semibold text-indigo-600">Tramo Venta: ${comp.tramo_ventas} &bull; ${comp.trabajadores} Empleados</div>
        <div class="pt-1.5 flex gap-2">
          <button onclick="openModal('${comp.rut}')" class="text-xs bg-indigo-600 text-white px-2 py-0.5 rounded font-medium">Ver Ficha</button>
          <button onclick="toggleRouteItem('${comp.rut}')" class="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">+ Ruta</button>
        </div>
      </div>
    `);

    markersLayer.addLayer(marker);
  });

  recenterMap();
}

// PAGINATION
function updatePagination() {
  const start = currentPage * pageSize + 1;
  const end = Math.min((currentPage + 1) * pageSize, totalResults);
  document.getElementById('pagination-info').innerText = totalResults > 0 ? `Mostrando ${start}-${end} de ${totalResults.toLocaleString()}` : '0 resultados';
  document.getElementById('btn-prev-page').disabled = currentPage === 0;
  document.getElementById('btn-next-page').disabled = end >= totalResults;
}

function prevPage() {
  if (currentPage > 0) applyFilters(currentPage - 1);
}

function nextPage() {
  if ((currentPage + 1) * pageSize < totalResults) applyFilters(currentPage + 1);
}

function resetFilters() {
  document.getElementById('filter-q').value = '';
  document.getElementById('filter-comuna').value = '';
  document.getElementById('filter-rubro').value = '';
  document.getElementById('filter-tramo').value = '4';
  document.getElementById('filter-trabajadores').value = '10';
  document.getElementById('filter-activas').checked = true;
  applyFilters(0);
}

// ROUTE PLANNER LOGIC
function toggleRouteItem(rut) {
  const comp = currentCompanies.find(c => c.rut === rut) || selectedRouteCompanies.find(c => c.rut === rut);
  if (!comp) return;

  const idx = selectedRouteCompanies.findIndex(r => r.rut === rut);
  if (idx > -1) {
    selectedRouteCompanies.splice(idx, 1);
  } else {
    selectedRouteCompanies.push(comp);
  }

  updateRouteBadge();
  renderTable(currentCompanies);
  updateModalRouteBtn(rut);
}

function addAllVisibleToRoute() {
  currentCompanies.forEach(c => {
    if (!selectedRouteCompanies.some(r => r.rut === c.rut)) {
      selectedRouteCompanies.push(c);
    }
  });
  updateRouteBadge();
  renderTable(currentCompanies);
}

function clearCurrentRoute() {
  selectedRouteCompanies = [];
  updateRouteBadge();
  renderRoutesTab();
  renderTable(currentCompanies);
}

function updateRouteBadge() {
  const badge = document.getElementById('badge-route-count');
  const count = selectedRouteCompanies.length;
  badge.innerText = count;
  if (count > 0) {
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

function renderRoutesTab() {
  const empty = document.getElementById('route-empty-state');
  const content = document.getElementById('route-content');
  const tbody = document.getElementById('route-table-body');
  
  if (selectedRouteCompanies.length === 0) {
    empty.classList.remove('hidden');
    content.classList.add('hidden');
    return;
  }

  empty.classList.add('hidden');
  content.classList.remove('hidden');
  tbody.innerHTML = '';

  selectedRouteCompanies.forEach((comp, idx) => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50 transition';
    tr.innerHTML = `
      <td class="p-3 text-center font-bold text-indigo-600 bg-indigo-50/50 w-16">#${idx + 1}</td>
      <td class="p-3">
        <div class="font-bold text-slate-900">${comp.razon_social}</div>
        <div class="text-[10px] text-slate-400 font-mono">${comp.rut}-${comp.dv}</div>
      </td>
      <td class="p-3">
        <div class="font-medium text-slate-800">${comp.calle} ${comp.numero || ''} ${comp.depto || ''}</div>
        <div class="text-[10px] text-slate-500">${comp.comuna}</div>
      </td>
      <td class="p-3 text-center text-xs">
        <span class="font-semibold">Tramo ${comp.tramo_ventas}</span> &bull; ${comp.trabajadores} empl.
      </td>
      <td class="p-3 text-right">
        <button onclick="toggleRouteItem('${comp.rut}'); renderRoutesTab();" class="text-rose-600 hover:text-rose-800 font-semibold text-xs">Quitar</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function openGoogleMapsRoute() {
  if (selectedRouteCompanies.length === 0) return;
  const addresses = selectedRouteCompanies.map(c => encodeURIComponent(`${c.calle} ${c.numero || ''}, ${c.comuna}, Chile`));
  const url = `https://www.google.com/maps/dir/${addresses.slice(0, 10).join('/')}`;
  window.open(url, '_blank');
}

// CORRIDOR CLUSTERS
async function loadCorridors(comuna) {
  try {
    const res = await fetch(`/api/clusters?comuna=${encodeURIComponent(comuna || 'PROVIDENCIA')}`);
    const data = await res.json();
    const container = document.getElementById('corridors-list');
    container.innerHTML = '';

    const entries = Object.entries(data).slice(0, 6);
    if (entries.length === 0) {
      container.innerHTML = `<p class="text-xs text-slate-400 col-span-3">No hay clusters suficientes en esta comuna.</p>`;
      return;
    }

    entries.forEach(([street, list]) => {
      const card = document.createElement('div');
      card.className = 'p-3 bg-slate-50 rounded-xl border border-slate-200 hover:border-indigo-300 transition space-y-1.5 cursor-pointer';
      card.onclick = () => {
        document.getElementById('filter-q').value = street;
        switchTab('explorer');
        applyFilters(0);
      };
      card.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="font-bold text-xs text-slate-900">${street}</span>
          <span class="text-[10px] font-bold bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">${list.length} oficinas</span>
        </div>
        <div class="text-[10px] text-slate-500">Haz clic para filtrar y planificar visitas a pie en este eje.</div>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    console.error('Error loading corridors:', e);
  }
}

// PIPELINE CRM LOGIC
async function renderCrmTab() {
  const cols = {
    'Por Contactar': { el: document.getElementById('crm-col-por-contactar'), count: document.getElementById('count-crm-por-contactar'), list: [] },
    'Visita Agendada': { el: document.getElementById('crm-col-visita'), count: document.getElementById('count-crm-visita'), list: [] },
    'En Negociación': { el: document.getElementById('crm-col-interesado'), count: document.getElementById('count-crm-interesado'), list: [] },
    'Cliente Ganado': { el: document.getElementById('crm-col-ganado'), count: document.getElementById('count-crm-ganado'), list: [] }
  };

  Object.values(cols).forEach(c => c.el.innerHTML = '');

  try {
    const res = await fetch('/api/companies?limit=200');
    const data = await res.json();
    const crmItems = data.results.filter(c => c.crm_estado && c.crm_estado !== 'Nuevo');

    crmItems.forEach(item => {
      const st = item.crm_estado;
      if (cols[st]) cols[st].list.push(item);
    });

    Object.entries(cols).forEach(([k, v]) => {
      v.count.innerText = v.list.length;
      if (v.list.length === 0) {
        v.el.innerHTML = '<div class="text-[11px] text-slate-400 text-center py-6">Sin prospectos</div>';
        return;
      }
      v.list.forEach(item => {
        const card = document.createElement('div');
        card.className = 'p-3 bg-white rounded-lg border border-slate-200 shadow-sm space-y-1 hover:border-indigo-400 transition cursor-pointer';
        card.onclick = () => openModal(item.rut);
        card.innerHTML = `
          <div class="font-bold text-xs text-slate-900">${item.razon_social}</div>
          <div class="text-[10px] text-slate-500">${item.comuna} &bull; Tramo ${item.tramo_ventas}</div>
          ${item.contacto_telefono ? `<div class="text-[10px] text-emerald-600 font-mono">Tel: ${item.contacto_telefono}</div>` : ''}
          ${item.crm_notas ? `<div class="text-[10px] text-slate-600 italic bg-slate-50 p-1.5 rounded mt-1 border border-slate-100">${item.crm_notas.substring(0, 60)}...</div>` : ''}
        `;
        v.el.appendChild(card);
      });
    });

  } catch (e) {
    console.error('Error rendering CRM:', e);
  }
}

// COMPANY MODAL & CONTACT ENRICHMENT
function openModal(rut) {
  const comp = currentCompanies.find(c => c.rut === rut) || selectedRouteCompanies.find(c => c.rut === rut);
  if (!comp) return;

  currentModalRut = rut;
  document.getElementById('modal-rut').innerText = `${comp.rut}-${comp.dv}`;
  document.getElementById('modal-razon').innerText = comp.razon_social;
  document.getElementById('modal-tramo').innerText = `Tramo ${comp.tramo_ventas} (${getTramoLabel(comp.tramo_ventas)})`;
  document.getElementById('modal-trabajadores').innerText = `${comp.trabajadores} dependientes`;
  document.getElementById('modal-comuna').innerText = `${comp.comuna}, ${comp.region}`;
  document.getElementById('modal-direccion').innerText = `${comp.calle} ${comp.numero || ''} ${comp.depto || ''}`;
  document.getElementById('modal-actividad').innerText = comp.actividad_economica || comp.rubro;

  // External links
  const qGoogle = `"${comp.razon_social}" ${comp.comuna} chile`;
  const qLinkedin = `"${comp.razon_social}" (contador OR finanzas OR "gerente general" OR GAF)`;
  document.getElementById('btn-google-search').href = `https://www.google.com/search?q=${encodeURIComponent(qGoogle)}`;
  document.getElementById('btn-linkedin-search').href = `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(qLinkedin)}`;

  // Reset MP enrichment box
  document.getElementById('mp-enrichment-result').classList.add('hidden');

  // CRM status
  document.getElementById('modal-crm-estado').value = comp.crm_estado || 'Nuevo';
  document.getElementById('modal-crm-tel').value = comp.contacto_telefono || '';
  document.getElementById('modal-crm-email').value = comp.contacto_email || '';
  document.getElementById('modal-crm-notas').value = comp.crm_notas || '';

  updateModalRouteBtn(rut);
  document.getElementById('company-modal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('company-modal').classList.add('hidden');
}

function updateModalRouteBtn(rut) {
  const inRoute = selectedRouteCompanies.some(r => r.rut === rut);
  const btn = document.getElementById('modal-btn-route');
  if (inRoute) {
    btn.innerHTML = `<i data-lucide="minus-circle" class="w-4 h-4 text-rose-600"></i> Quitar de Ruta`;
  } else {
    btn.innerHTML = `<i data-lucide="plus-circle" class="w-4 h-4 text-emerald-600"></i> Agregar a Ruta del Día`;
  }
  lucide.createIcons();
}

function toggleRouteItemFromModal() {
  if (currentModalRut) {
    toggleRouteItem(currentModalRut);
  }
}

async function enrichWithMercadoPublico() {
  if (!currentModalRut) return;
  const btn = document.getElementById('btn-enrich-mp');
  btn.classList.add('opacity-50');

  try {
    const res = await fetch('/api/enrich', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rut: currentModalRut })
    });
    const data = await res.json();
    const mp = data.mercadopublico;
    const resBox = document.getElementById('mp-enrichment-result');
    resBox.classList.remove('hidden');

    if (mp.encontrado) {
      document.getElementById('mp-email').innerText = mp.email || 'No especificado';
      document.getElementById('mp-tel').innerText = mp.telefono || 'No especificado';
      document.getElementById('mp-nombre').innerText = `${mp.contacto || ''} (${mp.nombre_fantasia || ''})`;
      
      if (mp.telefono) document.getElementById('modal-crm-tel').value = mp.telefono;
      if (mp.email) document.getElementById('modal-crm-email').value = mp.email;
      document.getElementById('modal-crm-estado').value = 'Por Contactar';
    } else {
      resBox.innerHTML = `<div class="text-slate-500 italic text-[11px]">${mp.mensaje}</div>`;
    }
  } catch (e) {
    console.error('Error enriching from MP:', e);
  } finally {
    btn.classList.remove('opacity-50');
  }
}

async function saveModalCrm() {
  if (!currentModalRut) return;
  const estado = document.getElementById('modal-crm-estado').value;
  const tel = document.getElementById('modal-crm-tel').value;
  const email = document.getElementById('modal-crm-email').value;
  const notas = document.getElementById('modal-crm-notas').value;

  try {
    await fetch('/api/crm/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rut: currentModalRut,
        estado: estado,
        telefono: tel,
        email: email,
        notas: notas
      })
    });

    // Update in memory
    const comp = currentCompanies.find(c => c.rut === currentModalRut);
    if (comp) {
      comp.crm_estado = estado;
      comp.contacto_telefono = tel;
      comp.contacto_email = email;
      comp.crm_notas = notas;
    }

    closeModal();
    loadStats();
    renderTable(currentCompanies);
  } catch (e) {
    console.error('Error saving CRM:', e);
  }
}

function exportCSV() {
  const comuna = document.getElementById('filter-comuna').value;
  const rubro = document.getElementById('filter-rubro').value;
  const tramo = document.getElementById('filter-tramo').value;
  window.location.href = `/api/export?comuna=${encodeURIComponent(comuna)}&rubro=${encodeURIComponent(rubro)}&tramo_min=${tramo}`;
}

function getTramoLabel(tramo) {
  const labels = {
    1: '0 UF', 2: '0-200 UF', 3: '200-600 UF', 4: 'Micro (600-2.4k UF)',
    5: 'Pequeña 1 (2.4k-5k UF)', 6: 'Pequeña 2 (5k-10k UF)', 7: 'Pequeña 3 (10k-25k UF)',
    8: 'Mediana 1 (25k-50k UF)', 9: 'Mediana 2 (50k-100k UF)', 10: 'Grande (+100k UF)'
  };
  return labels[tramo] || `Tramo ${tramo}`;
}
