const app = document.querySelector('#app');

const state = {
  role: null,
  route: location.hash.replace('#/', '') || 'landing',
  horizon: 'now',
  city: 'Mumbai',
  station: 'Borivali East',
  citizenTab: 'home',
  layers: { traffic: true, construction: true, industry: true, fire: true, wind: true },
  actions: { traffic: true, construction: true, health: true },
  alertLanguage: 'English',
  forecast: { pollutant: 'PM2.5', horizon: '72', aggregation: 'Hourly', confidence: true, thresholds: true, mapHour: '24', scenarioPackage: 'targeted', trafficReduction: 25, constructionControl: true, industryReduction: 10 },
  plan: { department: 'Ward Environment Team', priority: 'High', owner: 'Ward Response Officer', deadline: '2026-09-18T06:00', status: 'Draft', reportId: 'AQIS-MUM-2026-0917-01' },
  backend: { loading: true, connected: false, liveConnected: false, mode: 'frontend-fallback', stations: [], stationId: 'Borivali_East_Mumbai_-_MPCB', intelligence: null, live: null, metrics: null }
};

function intelligence() { return state.backend.intelligence?.data || null; }
function cachedForecast(horizon) { return state.backend.live?.forecast?.[`${horizon}h`] || intelligence()?.forecast?.[`${horizon}h`] || null; }
function pm25ToAqi(value) {
  const ranges = [[0,30,0,50],[31,60,51,100],[61,90,101,200],[91,120,201,300],[121,250,301,400],[251,500,401,500]];
  const [cLow,cHigh,iLow,iHigh] = ranges.find(([low,high]) => value >= low && value <= high) || ranges[ranges.length-1];
  return Math.round(((iHigh-iLow)/(cHigh-cLow))*(Math.min(value,cHigh)-cLow)+iLow);
}
function backendStatusText() {
  if(state.backend.loading) return 'Connecting model service…';
  if(state.backend.liveConnected) return 'Live air data · Open-Meteo';
  if(!state.backend.connected) return 'Frontend fallback data';
  const date = intelligence()?.timestamp?.split(' ')[0];
  return `Model cache connected${date ? ` · ${date}` : ''}`;
}

const fallbackStations = {
  mumbai: [{ id:'Borivali_East_Mumbai_-_MPCB', name:'Borivali East, Mumbai - MPCB', latitude:19.229, longitude:72.8649 }],
  delhi: [{ id:'Anand_Vihar_Delhi_-_DPCC', name:'Anand Vihar, Delhi - DPCC', latitude:28.6469, longitude:77.3160 }]
};

function selectedStation() {
  return state.backend.stations.find(station => station.id === state.backend.stationId) || state.backend.stations[0] || fallbackStations[state.city.toLowerCase()][0];
}

function categoryForPm25(pm25) {
  const aqi = pm25ToAqi(pm25);
  return aqi <= 50 ? 'Good' : aqi <= 100 ? 'Satisfactory' : aqi <= 200 ? 'Moderate' : aqi <= 300 ? 'Poor' : aqi <= 400 ? 'Very Poor' : 'Severe';
}

async function loadLiveAirQuality() {
  const station = selectedStation();
  if(!station) return;
  try {
    const url = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${station.latitude}&longitude=${station.longitude}&current=pm2_5,pm10,nitrogen_dioxide&hourly=pm2_5,pm10,nitrogen_dioxide&forecast_days=4&timezone=auto`;
    const response = await fetch(url);
    if(!response.ok) throw new Error('Live feed unavailable');
    const data = await response.json();
    const currentIndex = Math.max(0, data.hourly.time.findIndex(time => new Date(time) >= new Date()));
    const at = hours => Number(data.hourly.pm2_5[Math.min(currentIndex + hours, data.hourly.pm2_5.length - 1)]);
    const makeForecast = hours => ({ pm25: at(hours), aqi_category: categoryForPm25(at(hours)) });
    state.backend.live = {
      source:'Open-Meteo Air Quality API', observedAt:data.current?.time || new Date().toISOString(),
      current:{ pm25:Number(data.current?.pm2_5), pm10:Number(data.current?.pm10), no2:Number(data.current?.nitrogen_dioxide) },
      forecast:{ '24h':makeForecast(24), '48h':makeForecast(48), '72h':makeForecast(72) }
    };
    state.backend.liveConnected = true;
  } catch(error) {
    state.backend.liveConnected = false;
  }
}

const icons = {
  pulse: 'dashboard', forecast: 'trend', evidence: 'map', actions: 'clipboard', alerts: 'bell', model: 'database'
};

function iconSvg(name) {
  const paths = {
    dashboard: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    trend: '<path d="M3 17l6-6 4 4 8-9"/><path d="M15 6h6v6"/>',
    map: '<path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15M15 6v15"/>',
    clipboard: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2h6v2M9 12l2 2 4-5"/>',
    bell: '<path d="M18 8a6 6 0 10-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
    database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>'
  };
  return `<svg class="nav-svg" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.dashboard}</svg>`;
}

const adminNav = [
  ['pulse', 'City Pulse', icons.pulse],
  ['forecast', 'Forecast', icons.forecast],
  ['evidence', 'Evidence Explorer', icons.evidence],
  ['actions', 'Action Studio', icons.actions],
  ['alerts', 'Alert Composer', icons.alerts],
  ['model', 'Model Card', icons.model]
];

const citizenNav = [
  ['home', 'My Air'], ['plan', 'Plan & Alerts']
];

function brand(light = false) {
  return `<div class="brand"><div class="brand-mark">≋</div><div><div class="brand-name" style="${light ? 'color:white' : ''}">AQIS</div><div class="brand-sub" style="${light ? 'color:rgba(255,255,255,.7)' : ''}">Urban Air Intelligence</div></div></div>`;
}

function navigate(route) {
  location.hash = `/${route}`;
}

function toast(message) {
  const el = document.querySelector('#toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

function mapSvg(compact = false) {
  return `
  <svg viewBox="0 0 900 520" preserveAspectRatio="xMidYMid slice" aria-label="Interactive source evidence map">
    <defs>
      <pattern id="grid" width="55" height="55" patternUnits="userSpaceOnUse"><path d="M55 0H0V55" fill="none" stroke="#d5dfdc" stroke-width="1"/></pattern>
      <radialGradient id="hot"><stop offset="0" stop-color="#e85c4a" stop-opacity=".35"/><stop offset="1" stop-color="#e85c4a" stop-opacity="0"/></radialGradient>
    </defs>
    <rect width="900" height="520" fill="#edf3f1"/><rect width="900" height="520" fill="url(#grid)"/>
    <path d="M-20 100 C160 140,200 50,350 105 S610 155,920 70" fill="none" stroke="#c8d7d3" stroke-width="30"/>
    <path d="M-20 100 C160 140,200 50,350 105 S610 155,920 70" fill="none" stroke="#fff" stroke-width="20"/>
    <g class="map-layer layer-traffic" style="display:${state.layers.traffic ? 'block' : 'none'}">
      <path d="M120 540 C180 390,300 350,420 210 S630 80,790 -20" fill="none" stroke="#d84b45" stroke-width="9" stroke-linecap="round"/>
      <path d="M55 400 C250 390,390 430,570 520" fill="none" stroke="#d84b45" stroke-width="6" stroke-linecap="round"/>
    </g>
    <g class="map-layer layer-construction" style="display:${state.layers.construction ? 'block' : 'none'}" fill="#f2b84b" fill-opacity=".55" stroke="#d97706" stroke-width="2">
      <polygon points="540,255 630,236 650,305 565,325"/><polygon points="225,190 290,175 305,225 242,242"/>
    </g>
    <g class="map-layer layer-industry" style="display:${state.layers.industry ? 'block' : 'none'}" fill="#8065b6" fill-opacity=".42" stroke="#7157a8" stroke-width="2">
      <polygon points="670,340 785,328 802,420 690,434"/>
    </g>
    <g class="map-layer layer-fire" style="display:${state.layers.fire ? 'block' : 'none'}">
      <circle cx="720" cy="240" r="11" fill="#e66b2f"/><circle cx="745" cy="220" r="6" fill="#e66b2f"/>
    </g>
    <circle cx="430" cy="325" r="145" fill="url(#hot)"/>
    <circle cx="430" cy="325" r="106" fill="none" stroke="#0b6b63" stroke-width="2" stroke-dasharray="7 7" opacity=".7"/>
    <circle cx="430" cy="325" r="16" fill="#0b6b63" stroke="white" stroke-width="7"/>
    <g style="display:${state.layers.wind ? 'block' : 'none'}" stroke="#306e9c" stroke-width="3" fill="none" opacity=".8">
      <path d="M170 270 L310 300"/><path d="M295 288 L310 300 L291 306"/>
      <path d="M165 305 L300 335"/><path d="M285 323 L300 335 L281 341"/>
    </g>
    <g font-family="DM Sans" font-size="12" fill="#60706e"><text x="400" y="360">Borivali East station</text><text x="665" y="458">Industrial area</text><text x="542" y="345">Construction</text><text x="120" y="390">Western Express Highway</text></g>
  </svg>`;
}

function landing() {
  return `<main class="landing">
    <nav class="landing-nav">${brand()}<div class="nav-actions"><button class="btn btn-secondary" data-go="citizen-login">Citizen sign in</button><button class="btn btn-primary" data-go="admin-login">Administrator portal</button></div></nav>
    <section class="hero">
      <div class="hero-copy"><div class="eyebrow">Air intelligence for healthier cities</div><h1>Know what the air will do next.</h1><p>AQIS brings verified measurements, 72-hour forecasts and clear actions together—so residents can plan their day and city teams can respond earlier.</p>
        <div class="hero-actions"><button class="btn btn-primary" data-go="citizen-login">Check my local air →</button><button class="btn btn-secondary" data-go="admin-login">Open administrator portal</button></div>
        <div class="trust-row"><span>Verified station data</span><span>24–72 hour outlook</span><span>Transparent evidence</span></div>
      </div>
      <div class="hero-art"><div class="hero-photo"></div><div class="floating-aqi"><small>Borivali East · Updated 8 min ago</small><strong>168</strong><span class="aqi-label">Poor · Sensitive groups take care</span></div><div class="floating-forecast"><small>Tomorrow morning</small><h3 style="margin:6px 0">Risk increases</h3><small>PM2.5 may peak near 92 µg/m³</small><svg class="mini-line" viewBox="0 0 180 54"><path d="M2 45 C35 42,47 30,72 35 S115 9,178 14" fill="none" stroke="#9cf2e8" stroke-width="3"/><path d="M2 45 C35 42,47 30,72 35 S115 9,178 14" fill="none" stroke="rgba(255,255,255,.22)" stroke-width="12"/></svg></div></div>
    </section>
    <section class="role-section"><div class="section-heading"><h2>One platform, two clear experiences</h2><p>Choose the view designed for what you need to do.</p></div><div class="role-grid">
      <button class="role-card" data-go="citizen-login"><span class="role-icon">♡</span><span><h3>For residents</h3><p>Local air status, personal guidance and alerts.</p></span><span class="arrow">→</span></button>
      <button class="role-card admin" data-go="admin-login"><span class="role-icon">⌘</span><span><h3>For city teams</h3><p>Forecasts, evidence and coordinated response planning.</p></span><span class="arrow">→</span></button>
    </div></section>
  </main>`;
}

function loginPage(role) {
  const citizen = role === 'citizen';
  return `<main class="auth-page"><section class="auth-visual">${brand(true)}<div class="auth-message"><div class="eyebrow" style="color:#9cf2e8">${citizen ? 'Your neighbourhood, made clearer' : 'A focused workspace for city teams'}</div><h1>${citizen ? 'Plan your day around cleaner air.' : 'Turn forecasts into timely action.'}</h1><p>${citizen ? 'Save your location, personalize health guidance and receive alerts before air quality worsens.' : 'Review city risk, inspect supporting evidence and create a response plan without the noise.'}</p></div><div class="auth-stat"><div><strong>15</strong><span>stations connected</span></div><div><strong>72h</strong><span>forecast horizon</span></div><div><strong>3</strong><span>local languages</span></div></div></section>
  <section class="auth-panel"><form class="auth-box" data-login="${role}"><a href="#/landing" class="back-link">← Back to home</a><h2>${citizen ? 'Citizen sign in' : 'Administrator sign in'}</h2><p>${citizen ? 'Use any details for this frontend preview.' : 'Use your organization account or enter demo credentials.'}</p>
    ${citizen ? `<div class="field"><label>Mobile number or email</label><input required placeholder="+91 98765 43210" value="demo@aqis.in" /></div><div class="field"><label>City</label><select><option>Mumbai</option><option>Delhi</option></select></div>` : `<div class="field"><label>Work email</label><input required type="email" placeholder="officer@municipality.gov.in" value="admin@aqis.in" /></div><div class="field"><label>Password</label><input required type="password" value="demopreview" /></div><div class="field"><label>Organization</label><select><option>Mumbai Municipal Environment Cell</option><option>Delhi Pollution Control Committee</option><option>Research partner</option></select></div>`}
    <button class="btn btn-primary" type="submit">${citizen ? 'Continue to my air' : 'Open command centre'} →</button><button class="btn btn-secondary" type="button" data-demo="${role}">Continue with demo account</button><div class="auth-note">Frontend preview only. No personal information is stored.</div>
  </form></section></main>`;
}

function adminShell(page) {
  return `<div class="shell"><aside class="sidebar" id="sidebar">${brand()}<nav class="side-nav">${adminNav.map(([id,label,icon]) => `<button class="${page===id?'active':''}" data-admin="${id}"><span class="nav-icon">${iconSvg(icon)}</span>${label}</button>`).join('')}</nav><div class="sidebar-footer"><button class="btn btn-secondary btn-small" style="width:100%;margin-bottom:10px" data-go="landing">Sign out</button><div class="profile"><div class="avatar">KR</div><div><strong>Khushal</strong><small>Demo administrator</small></div></div></div></aside>
  <div class="workspace"><header class="topbar"><div class="topbar-left"><button class="btn btn-secondary btn-small mobile-menu" data-menu>☰</button><select id="citySelect" class="btn btn-secondary btn-small" data-city-select><option value="Mumbai" ${state.city==='Mumbai'?'selected':''}>Mumbai</option><option value="Delhi" ${state.city==='Delhi'?'selected':''}>Delhi</option></select><select class="top-search" data-station-select>${state.backend.stations.length ? state.backend.stations.map(s=>`<option value="${s.id}" ${state.backend.stationId===s.id?'selected':''}>${s.name.replace(/, (Mumbai|Delhi).*$/,'')}</option>`).join('') : '<option>Borivali East</option>'}</select></div><div class="topbar-actions"><span class="status-pill ${state.backend.connected||state.backend.liveConnected?'connected':''}">${backendStatusText()}</span><button class="btn btn-secondary btn-small" data-mode>${state.backend.liveConnected?'Live feed':state.backend.connected?'Cached model':'Fallback'}</button></div></header>${adminPage(page)}</div></div>`;
}

function pageHeading(title, subtitle, action='') {
  return `<div class="page-heading"><div><h1>${title}</h1><p>${subtitle}</p></div>${action}</div>`;
}

function kpis() {
  const forecast = cachedForecast(24);
  const pm25 = forecast ? Number(forecast.pm25) : 88;
  const aqi = forecast ? pm25ToAqi(pm25) : 168;
  const category = forecast?.aqi_category || 'Poor';
  return `<div class="grid kpi-grid"><div class="card kpi"><div class="kpi-label">${state.backend.connected?'24-hour forecast AQI':'Observed AQI'}</div><div class="kpi-value">${aqi}</div><span class="tag ${aqi>150?'tag-red':aqi>100?'tag-amber':'tag-green'}">${category}</span></div><div class="card kpi"><div class="kpi-label">Dominant pollutant</div><div class="kpi-value">PM2.5</div><span class="subtle tiny">${pm25.toFixed(1)} µg/m³ ${state.backend.connected?'predicted':'observed'}</span></div><div class="card kpi"><div class="kpi-label">24-hour risk</div><div class="kpi-value">${aqi>200?'High':aqi>100?'Elevated':'Low'}</div><span class="tag ${aqi>100?'tag-amber':'tag-green'}">${state.backend.connected?'Cached inference':'Peak 8 AM'}</span></div><div class="card kpi"><div class="kpi-label">Cached stations</div><div class="kpi-value">${state.backend.stations.length || '14'}</div><span class="tag tag-green">${state.backend.connected?'API connected':'Preview data'}</span></div></div>`;
}

function mapCard(showTooltip = true) {
  const station = selectedStation();
  return `<section class="card map-card"><div class="map-head"><div><strong>Live station map</strong><div class="tiny subtle">${station.name} · OpenStreetMap context</div></div><div class="map-head-actions"><span class="tag tag-green">Interactive OSM</span></div></div><div class="map-stage"><div class="leaflet-map" data-live-map="evidence"></div><div class="map-live-badge">${state.backend.liveConnected?'● Live air feed':'Cached fallback'} · ${Number(cachedForecast(24)?.pm25 || 0).toFixed(1)} µg/m³ PM2.5</div></div><div class="timeline"><strong class="tiny">Time</strong>${[['now','Now'],['24','+24h'],['48','+48h'],['72','+72h']].map(([id,label])=>`<button class="${state.horizon===id?'active':''}" data-horizon="${id}">${label}</button>`).join('')}</div></section>`;
}

function pulsePage() {
  return `<main class="page">${pageHeading('Mumbai City Pulse','A clear view of current conditions and the next 24 hours.', `<button class="btn btn-primary" data-admin="actions">Create response plan</button>`)}${kpis()}<div class="grid pulse-grid">${mapCard()}<div class="side-stack"><section class="card"><div class="card-title"><h2>Short forecast</h2><button class="btn btn-soft btn-small" data-admin="forecast">Full forecast</button></div><div class="forecast-strip"><div class="forecast-day"><span class="tiny subtle">Now</span><strong>88</strong><span class="tiny">µg/m³</span></div><div class="forecast-day"><span class="tiny subtle">+24h</span><strong>92</strong><span class="tiny">High</span></div><div class="forecast-day"><span class="tiny subtle">+48h</span><strong>74</strong><span class="tiny">Falling</span></div></div></section><section class="card"><div class="card-title"><h2>Likely source signals</h2></div>${sourceRows()}<button class="btn btn-secondary btn-small" style="width:100%;margin-top:10px" data-admin="evidence">Open Evidence Explorer</button></section><section class="card"><div class="card-title"><h2>Data quality</h2><span class="tag tag-green">Good</span></div><div class="quality-list"><div class="quality-item"><strong>8 min</strong><span class="tiny subtle">Data age</span></div><div class="quality-item"><strong>98.6%</strong><span class="tiny subtle">Coverage</span></div><div class="quality-item"><strong>0</strong><span class="tiny subtle">Active flags</span></div><div class="quality-item"><strong>v4.2</strong><span class="tiny subtle">Model</span></div></div></section></div></div></main>`;
}

function sourceRows() {
  const apiSources = intelligence()?.source_influence?.sources;
  const rows = apiSources?.length ? apiSources.slice(0,3).map((source,index)=>[
    ['#c2413b','#d97706','#306e9c'][index], source.name, source.contribution_percentage >= 40 ? 'High' : 'Medium'
  ]) : [['#c2413b','Traffic','High'],['#d97706','Construction','Medium'],['#306e9c','Regional background','Medium']];
  return rows.map(r=>`<div class="source-row"><span class="dot" style="background:${r[0]}"></span><strong>${r[1]}</strong><span class="tag ${r[2]==='High'?'tag-red':'tag-amber'}">${r[2]}</span></div>`).join('');
}

function pollutantData() {
  const api24 = cachedForecast(24)?.pm25;
  const api48 = cachedForecast(48)?.pm25;
  const api72 = cachedForecast(72)?.pm25;
  const apiValues = [api24, api24, api48, api72].map(Number);
  const apiAvailable = apiValues.every(Number.isFinite);
  const apiPeak = apiAvailable ? Math.max(...apiValues) : 92;
  const apiPeakIndex = apiAvailable ? apiValues.indexOf(apiPeak) : 1;
  const apiPath = apiAvailable ? apiValues.map((value,index)=>`${index===0?'M':'L'}${[60,330,600,870][index]} ${Math.max(45,260-(value/120)*205)}`).join(' ') : 'M60 228 C160 238,220 195,310 201 S430 105,530 132 S680 185,870 164';
  return {
    'PM2.5': { unit:'µg/m³', values:apiAvailable?apiValues:[88,92,78,69], peak:apiAvailable?apiPeak.toFixed(1):'92', time:apiAvailable?['Now','+24 hours','+48 hours','+72 hours'][apiPeakIndex]:'Tomorrow · 8 AM', change:apiAvailable?(state.backend.liveConnected?'Live forecast':'Cached inference'):'+4.5%', path:apiPath },
    'PM10': { unit:'µg/m³', values:[132,148,126,108], peak:'148', time:'Tomorrow · 10 AM', change:'+12.1%', path:'M60 214 C170 220,235 178,330 188 S455 86,555 112 S700 170,870 178' },
    'NO₂': { unit:'µg/m³', values:[46,61,52,42], peak:'61', time:'Tomorrow · 9 AM', change:'+32.6%', path:'M60 235 C165 230,230 205,325 214 S450 145,550 158 S700 205,870 218' }
  }[state.forecast.pollutant];
}

function chartSvg() {
  const d = pollutantData();
  const confidence = state.forecast.confidence ? `<path d="M60 210 C160 220,210 170,310 178 S430 82,530 108 S680 162,870 140 L870 190 C680 210,590 165,520 157 S410 125,320 220 S170 260,60 245 Z" fill="#dff3ee"/>` : '';
  const thresholds = state.forecast.thresholds ? `<line x1="60" y1="120" x2="870" y2="120" stroke="#d97706" stroke-dasharray="6 6"/><line x1="60" y1="50" x2="870" y2="50" stroke="#c2413b" stroke-dasharray="6 6"/><text x="750" y="112" fill="#d97706">CPCB category threshold</text>` : '';
  const endX = state.forecast.horizon === '24' ? 330 : state.forecast.horizon === '48' ? 600 : 870;
  return `<svg class="chart-svg" viewBox="0 0 900 310"><g stroke="#dce6e3" stroke-width="1"><line x1="60" y1="50" x2="870" y2="50"/><line x1="60" y1="120" x2="870" y2="120"/><line x1="60" y1="190" x2="870" y2="190"/><line x1="60" y1="260" x2="870" y2="260"/></g>${confidence}<path d="${d.path}" fill="none" stroke="#0b6b63" stroke-width="4"/>${thresholds}<line x1="${endX}" y1="38" x2="${endX}" y2="266" stroke="#0b6b63" stroke-dasharray="3 5" opacity=".45"/><g fill="#60706e" font-size="12" font-family="DM Sans"><text x="12" y="54">120</text><text x="20" y="124">90</text><text x="20" y="194">60</text><text x="20" y="264">30</text><text x="60" y="295">Now</text><text x="300" y="295">+24 hours</text><text x="550" y="295">+48 hours</text><text x="820" y="295">+72 hours</text></g><circle cx="310" cy="201" r="6" fill="#0b6b63"/><circle cx="530" cy="132" r="6" fill="#0b6b63"/></svg>`;
}

function scenarioResult() {
  const apiAqis = [24,48,72].map(h=>cachedForecast(h)).filter(Boolean).map(item=>pm25ToAqi(Number(item.pm25)));
  const baseline = apiAqis.length ? Math.max(...apiAqis) : 184;
  const trafficEffect = Math.round(state.forecast.trafficReduction * 0.48);
  const constructionEffect = state.forecast.constructionControl ? 7 : 0;
  const industryEffect = Math.round(state.forecast.industryReduction * 0.22);
  const reduction = trafficEffect + constructionEffect + industryEffect;
  return { baseline, scenario: Math.max(0, baseline - reduction), reduction, range: `${Math.max(0, baseline-reduction-9)}–${Math.max(0, baseline-reduction+11)}` };
}

function spatialForecastMap() {
  const configs = {
    now: { main:168, north:154, east:139, south:126, color:'#e79b28', radius:92 },
    '24': { main:184, north:172, east:151, south:138, color:'#d84b45', radius:118 },
    '48': { main:156, north:149, east:132, south:121, color:'#e0792d', radius:98 },
    '72': { main:142, north:136, east:119, south:108, color:'#d6a125', radius:84 }
  };
  const apiHorizon = state.forecast.mapHour === 'now' ? 24 : Number(state.forecast.mapHour);
  const apiForecast = cachedForecast(apiHorizon);
  const apiAqi = apiForecast ? pm25ToAqi(Number(apiForecast.pm25)) : null;
  const fallback = configs[state.forecast.mapHour];
  const colorFor = value => value > 200 ? '#c2413b' : value > 100 ? '#e0792d' : value > 50 ? '#d6a125' : '#0b8b70';
  const m = apiAqi === null ? fallback : { main:apiAqi, north:Math.max(0,Math.round(apiAqi*.93)), east:Math.max(0,Math.round(apiAqi*.82)), south:Math.max(0,Math.round(apiAqi*.75)), color:colorFor(apiAqi), radius:Math.max(48,Math.min(118,48+apiAqi*.35)) };
  return `<div class="leaflet-map" data-live-map="forecast" data-aqi="${m.main}"></div>`;
}

function mountLiveMaps() {
  if(!window.L) return;
  const station = selectedStation();
  document.querySelectorAll('[data-live-map]').forEach(element => {
    if(element.dataset.mapReady) return;
    element.dataset.mapReady = 'true';
    const map = L.map(element).setView([station.latitude, station.longitude], element.dataset.liveMap === 'forecast' ? 12 : 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom:19, attribution:'&copy; OpenStreetMap contributors' }).addTo(map);
    const horizon = state.forecast.mapHour === 'now' ? 24 : Number(state.forecast.mapHour);
    const pm25 = Number(cachedForecast(horizon)?.pm25 || state.backend.live?.current?.pm25 || 0);
    const aqi = pm25ToAqi(pm25);
    const color = aqi <= 50 ? '#15803d' : aqi <= 100 ? '#d97706' : aqi <= 200 ? '#ea580c' : '#dc2626';
    L.circle([station.latitude, station.longitude], { radius:1800, color, fillColor:color, fillOpacity:.2, weight:2 }).addTo(map);
    L.circleMarker([station.latitude, station.longitude], { radius:10, color:'#fff', weight:4, fillColor:color, fillOpacity:1 }).addTo(map).bindPopup(`<strong>${station.name}</strong><br>${state.backend.liveConnected?'Live Open-Meteo':'Cached'} PM2.5: ${pm25.toFixed(1)} µg/m³<br>AQI estimate: ${aqi}`).openPopup();
    state.backend.stations.filter(item => item.id !== station.id).slice(0,8).forEach(item => L.circleMarker([item.latitude,item.longitude], { radius:5, color:'#0b6b63', fillColor:'#0b6b63', fillOpacity:.8 }).addTo(map).bindTooltip(item.name));
    setTimeout(() => map.invalidateSize(), 0);
  });
}

function forecastPage() {
  const d = pollutantData();
  const scenario = scenarioResult();
  const decisionNote = (state.backend.connected || state.backend.liveConnected) && scenario.baseline <= 100
    ? `${state.backend.liveConnected?'Live Open-Meteo':'Cached'} forecasts remain within the Good or Satisfactory AQI bands. Continue monitoring; no restrictive intervention is indicated.`
    : 'Tomorrow morning has the highest operational concern. Low wind and a shallow mixing layer may reduce dispersion. Confirm against the latest station QA flag before issuing an action.';
  return `<main class="page">
    ${pageHeading('Forecast Operations','Interrogate the forecast before using it for a city response.', `<button class="btn btn-secondary" data-download-forecast>Download CSV</button>`)}
    <section class="card forecast-controls"><div><label>Pollutant</label><div class="segmented">${['PM2.5','PM10','NO₂'].map(x=>`<button class="${state.forecast.pollutant===x?'active':''}" data-forecast-pollutant="${x}">${x}</button>`).join('')}</div></div><div><label>Horizon</label><div class="segmented">${['24','48','72'].map(x=>`<button class="${state.forecast.horizon===x?'active':''}" data-forecast-horizon="${x}">${x}h</button>`).join('')}</div></div><div class="field compact-field"><label>Aggregation</label><select data-forecast-aggregation><option ${state.forecast.aggregation==='Hourly'?'selected':''}>Hourly</option><option ${state.forecast.aggregation==='Daily'?'selected':''}>Daily</option></select></div><label class="control-check"><input type="checkbox" data-forecast-option="confidence" ${state.forecast.confidence?'checked':''}/> Confidence band</label><label class="control-check"><input type="checkbox" data-forecast-option="thresholds" ${state.forecast.thresholds?'checked':''}/> CPCB thresholds</label></section>
    <div class="grid forecast-layout"><section class="card chart-card"><div class="card-title"><div><h2>${state.forecast.pollutant} outlook · ${state.forecast.horizon} hours</h2><span class="tiny subtle">${state.forecast.aggregation} forecast · shaded region is the 80% prediction interval</span></div><span class="tag tag-blue">Model v4.2</span></div><div class="chart-wrap">${chartSvg()}</div></section><div class="side-stack"><section class="card"><div class="card-title"><h2>Operational summary</h2><span class="tag tag-amber">Review</span></div><div class="metric-list"><div class="metric-row"><span>Predicted peak</span><strong>${d.peak} ${d.unit}</strong></div><div class="metric-row"><span>Peak time</span><strong>${d.time}</strong></div><div class="metric-row"><span>vs current</span><strong>${d.change}</strong></div><div class="metric-row"><span>Model confidence</span><strong>Medium</strong></div></div></section><section class="card"><div class="card-title"><h2>Weather context</h2></div><div class="quality-list"><div class="quality-item"><strong>8 km/h</strong><span class="tiny subtle">Wind · WNW</span></div><div class="quality-item"><strong>78%</strong><span class="tiny subtle">Humidity</span></div><div class="quality-item"><strong>0 mm</strong><span class="tiny subtle">Rain</span></div><div class="quality-item"><strong>410 m</strong><span class="tiny subtle">Mixing height</span></div></div></section><section class="card"><div class="card-title"><h2>Decision note</h2></div><p class="subtle" style="line-height:1.6;margin:0">${decisionNote}</p></section></div></div>
    <div class="grid forecast-analysis-grid"><section class="card spatial-card"><div class="card-title"><div><h2>Spatial forecast</h2><span class="tiny subtle">Interactive station-area context on OpenStreetMap</span></div><span class="tag tag-green">OSM live</span></div><div class="spatial-map">${spatialForecastMap()}</div><div class="map-time-tabs">${[['now','Now'],['24','+24h'],['48','+48h'],['72','+72h']].map(([id,label])=>`<button class="${state.forecast.mapHour===id?'active':''}" data-forecast-map-horizon="${id}">${label}</button>`).join('')}</div><p class="tiny subtle map-caveat">Circle shows the selected station's forecast context, not street-level exposure.</p></section>
    <section class="card scenario-card"><div class="card-title"><div><h2>Intervention scenario</h2><span class="tiny subtle">Choose operational packages while weather remains fixed</span></div><span class="tag tag-amber">Planning sensitivity</span></div><div class="scenario-results"><div><span>Baseline peak</span><strong>${scenario.baseline}</strong><small>AQI</small></div><div class="scenario-arrow">→</div><div class="scenario-improved"><span>Scenario peak</span><strong>${scenario.scenario}</strong><small>AQI · range ${scenario.range}</small></div></div>
      ${policyLever('trend','Traffic management','Changes high-emitting vehicle activity; road infrastructure remains unchanged.','trafficReduction',[[0,'No change','0%'],[25,'Targeted','−25%'],[40,'Strong','−40%']])}
      ${policyLever('clipboard','Construction enforcement','Assumes compliance with watering, covers and on-site dust controls.','constructionControl',[[false,'Standard','Existing checks'],[true,'Enhanced','Daily enforcement']])}
      ${policyLever('database','Industrial measures','Short-term operational reduction, not permanent closure.','industryReduction',[[0,'No change','0%'],[10,'Advisory','−10%'],[20,'Restriction','−20%']])}
      <div class="scenario-impact"><strong>Estimated change: −${scenario.reduction} AQI points</strong><span>Relative sensitivity under the selected policy package</span></div><p class="tiny subtle scenario-disclaimer">This is a counterfactual screening tool, not a causal guarantee. Final policy decisions require calibrated emission inventories and field verification.</p></section></div>
  </main>`;
}

function policyLever(icon, title, description, key, options) {
  const current = state.forecast[key];
  return `<div class="policy-lever"><div class="policy-title"><span class="policy-icon">${iconSvg(icon)}</span><div><strong>${title}</strong><small>${description}</small></div></div><div class="policy-options">${options.map(([value,label,detail]) => `<button class="${String(current)===String(value)?'active':''}" data-policy-key="${key}" data-policy-value="${value}"><strong>${label}</strong><span>${detail}</span></button>`).join('')}</div></div>`;
}

function evidencePage() {
  return `<main class="page">${pageHeading('Evidence Explorer','See what supports the forecast—without confusing correlation with causation.', `<button class="btn btn-secondary" data-admin="actions">Use in Action Studio</button>`)}<div class="grid evidence-layout"><div>${mapCard(false)}<div class="grid driver-grid"><div class="driver"><strong>Yesterday’s PM2.5</strong><span class="tiny subtle">Raised the forecast</span></div><div class="driver"><strong>Low wind</strong><span class="tiny subtle">Reduced dispersion</span></div><div class="driver"><strong>Humidity</strong><span class="tiny subtle">Moderate influence</span></div></div></div><section class="card"><div class="card-title"><h2>Source hypotheses</h2><span class="tag tag-blue">Screening</span></div>${hypothesis('Traffic','High','Major road 364 m away and directly upwind. NO₂/CO pattern supports combustion activity.','Road proximity','Wind alignment','Pollutant pattern')}${hypothesis('Construction','Medium','Two mapped construction zones are inside the 5 km context area.','Land-use map','PM ratio')}${hypothesis('Regional background','Medium','Low wind may allow broader urban pollution to accumulate.','Wind speed','Seasonal baseline')}${hypothesis('Industry','Low','Industrial land is present but mostly outside the direct upwind sector.','Land-use map')}<p class="tiny subtle" style="line-height:1.5;margin:14px 0 0">These are evidence-based hypotheses for field verification—not chemical source apportionment.</p></section></div></main>`;
}

function hypothesis(name, level, text, ...chips) {
  return `<article class="hypothesis"><div class="hypothesis-head"><strong>${name}</strong><span class="tag ${level==='High'?'tag-red':level==='Medium'?'tag-amber':'tag-blue'}">${level} likelihood</span></div><p>${text}</p><div class="evidence-chips">${chips.map(c=>`<span>${c}</span>`).join('')}</div></article>`;
}

function actionsPage() {
  const included = Object.entries(state.actions).filter(([,v])=>v).map(([k])=>({traffic:'Reroute heavy vehicles during the morning peak.',construction:'Inspect nearby construction dust controls.',health:'Publish guidance for sensitive residents.'}[k]));
  const p = state.plan;
  const statusClass = p.status === 'Draft' ? 'tag-blue' : 'tag-amber';
  const forecast = cachedForecast(24);
  const predictedPm25 = forecast ? Number(forecast.pm25).toFixed(1) : '92';
  const expectedCategory = forecast?.aqi_category || 'Poor';
  const location = intelligence()?.location?.replace(/, (Mumbai|Delhi).*$/,'') || 'Borivali East';
  return `<main class="page">${pageHeading('Action Studio','Convert a reviewed forecast into a traceable municipal response report.', `<button class="btn btn-secondary" data-admin="evidence">Review evidence</button>`)}<div class="event-banner"><div><small>Event ID</small><strong>${p.reportId}</strong></div><div><small>Location</small><strong>${location}</strong></div><div><small>Risk window</small><strong>Next 24 hours</strong></div><div><small>Expected category</small><strong>${expectedCategory}</strong></div><div><small>Evidence status</small><strong>${state.backend.connected?'Model cache loaded':'Preview'} · 3 signals</strong></div></div><div class="grid action-layout"><section><div class="card"><div class="card-title"><h2>1. Select interventions</h2><span class="tiny subtle">Evidence-linked recommendations</span></div>${actionOption('traffic','Traffic management','Reroute heavy vehicles and run roadside emission checks.','High evidence')}${actionOption('construction','Construction dust control','Inspect active sites and verify sprinkling and material covers.','Medium evidence')}${actionOption('health','Public health communication','Notify sensitive groups before the morning peak.','Recommended')}</div><div class="card" style="margin-top:16px"><div class="card-title"><h2>2. Assign ownership</h2><span class="tag tag-green">Live preview</span></div><div class="form-grid"><div class="field"><label>Responsible department</label><select data-plan-field="department"><option ${p.department==='Ward Environment Team'?'selected':''}>Ward Environment Team</option><option ${p.department==='Traffic Police'?'selected':''}>Traffic Police</option><option ${p.department==='Public Health Cell'?'selected':''}>Public Health Cell</option></select></div><div class="field"><label>Priority</label><select data-plan-field="priority"><option ${p.priority==='High'?'selected':''}>High</option><option ${p.priority==='Medium'?'selected':''}>Medium</option><option ${p.priority==='Low'?'selected':''}>Low</option></select></div><div class="field"><label>Accountable officer</label><input data-plan-field="owner" value="${p.owner}" /></div><div class="field"><label>Response deadline</label><input data-plan-field="deadline" type="datetime-local" value="${p.deadline}" /></div></div></div></section><aside class="card plan"><div class="card-title"><div><h2>3. Response report</h2><span class="tiny subtle">Auto-generated from reviewed inputs</span></div><span class="tag ${statusClass}">${p.status}</span></div><div class="report-meta"><span>Report ${p.reportId}</span><span>Version 1.0</span><span>Prepared 17 Sep 2026 · 21:45 IST</span></div><div class="plan-paper" id="responseReport"><h3>Municipal Air Quality Response Report</h3><div class="report-summary"><p><strong>Area:</strong> ${location}<br><strong>Forecast window:</strong> Next 24 hours<br><strong>Expected category:</strong> ${expectedCategory}<br><strong>Priority:</strong> ${p.priority}</p><p><strong>Predicted PM2.5:</strong> ${predictedPm25} µg/m³<br><strong>Model:</strong> AQIS v4.2 · 24h horizon<br><strong>Inference mode:</strong> ${state.backend.connected?'Precomputed cache':'Frontend preview'}<br><strong>Timestamp:</strong> ${intelligence()?.timestamp || 'Preview'}</p></div><h4>Recommended interventions</h4><ol>${included.map(x=>`<li>${x}</li>`).join('') || '<li>No intervention selected.</li>'}</ol><h4>Evidence basis</h4><p>Forecast, SHAP drivers and mapped source signals. Source signals are screening hypotheses and require field verification.</p><h4>Accountability</h4><p><strong>Department:</strong> ${p.department}<br><strong>Officer:</strong> ${p.owner}<br><strong>Deadline:</strong> ${p.deadline.replace('T',' · ')}</p><div class="approval-line"><span>Prepared by<br><strong>AQIS Duty Officer</strong></span><span>Reviewed by<br><strong>Pending</strong></span><span>Approval<br><strong>Pending</strong></span></div></div><div class="report-note"><strong>Audit trail</strong><span>Created from forecast v4.2 · Inputs timestamped · No approval signature recorded</span></div><div class="action-bar"><button class="btn btn-secondary btn-small" data-save-report>Save draft</button><button class="btn btn-secondary btn-small" data-export-report>Download report</button><button class="btn btn-primary btn-small" data-submit-report>Submit for approval</button></div></aside></div></main>`;
}

function actionOption(id,title,text,badge) {
  return `<label class="action-card"><input type="checkbox" data-action="${id}" ${state.actions[id]?'checked':''}/><span><span class="tag ${badge.startsWith('High')?'tag-red':'tag-amber'}" style="float:right">${badge}</span><h3>${title}</h3><p>${text}</p></span></label>`;
}

function alertsPage() {
  const messages = { English:'Air quality in Borivali East may become Poor tomorrow morning. Children, older adults and people with breathing or heart conditions should reduce prolonged outdoor activity.', Hindi:'बोरीवली ईस्ट में कल सुबह वायु गुणवत्ता खराब हो सकती है। बच्चों, बुजुर्गों और सांस या हृदय संबंधी समस्या वाले लोगों को लंबे समय तक बाहर रहने से बचना चाहिए।', Marathi:'बोरिवली पूर्व येथे उद्या सकाळी हवेची गुणवत्ता खराब होण्याची शक्यता आहे. लहान मुले, ज्येष्ठ नागरिक आणि श्वसन किंवा हृदयविकार असलेल्या व्यक्तींनी दीर्घकाळ बाहेर राहणे टाळावे.' };
  return `<main class="page">${pageHeading('Alert Composer','Prepare a clear public message without technical jargon.', `<span class="tag tag-green">Draft</span>`)}<div class="grid composer-layout"><section class="card"><div class="field"><label>Affected location</label><input value="Borivali East and nearby wards" /></div><div class="form-grid"><div class="field"><label>Audience</label><select><option>Sensitive groups</option><option>General public</option></select></div><div class="field"><label>Channel</label><select><option>WhatsApp + SMS</option><option>Web notification</option></select></div></div><div class="field"><label>Language</label><div class="segmented">${Object.keys(messages).map(l=>`<button type="button" class="${state.alertLanguage===l?'active':''}" data-language="${l}">${l}</button>`).join('')}</div></div><div class="field"><label>Editable message</label><textarea id="alertText">${messages[state.alertLanguage]}</textarea></div><div class="action-bar"><button class="btn btn-secondary" data-save>Save draft</button><button class="btn btn-primary" data-publish>Publish demo alert</button></div><p class="tiny subtle">Preview only. No live messaging provider is connected.</p></section><section class="card"><div class="card-title"><h2>Citizen preview</h2><span class="tiny subtle">WhatsApp</span></div><div class="phone-preview"><div class="phone-screen"><strong>AQIS Mumbai Alerts</strong><div class="message" id="messagePreview">${messages[state.alertLanguage]}<div class="tiny subtle" style="text-align:right;margin-top:8px">10:24 AM ✓✓</div></div></div></div></section></div></main>`;
}

function modelPage() {
  return `<main class="page">${pageHeading('Model & Data Card','Technical evidence for deciding whether this forecast is fit for operational use.', `<div class="version-lock"><span class="tag tag-green">Operational candidate</span><strong>v4.2</strong></div>`)}<div class="model-summary"><div><span>Model family</span><strong>Gradient-boosted time-series ensemble</strong></div><div><span>Target</span><strong>Station-level PM2.5</strong></div><div><span>Last evaluation</span><strong>15 Sep 2026</strong></div><div><span>Owner</span><strong>AQIS Forecasting Team</strong></div></div><section class="card" style="margin-top:16px"><div class="card-title"><div><h2>Dataset registry</h2><span class="tiny subtle">Every production input must have provenance and a quality check</span></div><span class="tag tag-blue">4 registered sources</span></div><div class="table-scroll"><table class="metric-table dataset-table"><thead><tr><th>Dataset</th><th>Purpose</th><th>Coverage</th><th>Update</th><th>Quality controls</th><th>Status</th></tr></thead><tbody><tr><td><strong>CPCB / MPCB station observations</strong><small>Regulatory monitoring feed</small></td><td>Targets and pollutant lags</td><td>Mumbai stations · 2019–2026</td><td>Hourly</td><td>Range, missingness, spike and station-status checks</td><td><span class="tag tag-green">Primary</span></td></tr><tr><td><strong>OpenAQ harmonized feed</strong><small>Access and schema normalization</small></td><td>Ingestion fallback</td><td>Station dependent</td><td>Hourly</td><td>Duplicate removal and CPCB identifier matching</td><td><span class="tag tag-blue">Fallback</span></td></tr><tr><td><strong>Open-Meteo forecast/archive</strong><small>Meteorological covariates</small></td><td>Wind, rain, humidity, temperature</td><td>Station coordinates</td><td>Hourly</td><td>Timestamp alignment and physical-range checks</td><td><span class="tag tag-green">Active</span></td></tr><tr><td><strong>OpenStreetMap</strong><small>Geospatial context only</small></td><td>Road and land-use proximity</td><td>5 km station buffer</td><td>On refresh</td><td>Geometry validity and feature recency check</td><td><span class="tag tag-amber">Planned</span></td></tr></tbody></table></div><p class="tiny subtle model-disclaimer">Record counts and data hashes will be populated by the production ingestion pipeline; they are intentionally not fabricated in this frontend prototype.</p></section><div class="grid model-evidence-grid"><section class="card"><div class="card-title"><div><h2>Validation design</h2><span class="tiny subtle">Designed to prevent future information leaking into training</span></div><span class="tag tag-green">Time-aware</span></div><div class="validation-steps"><div><strong>1</strong><span><b>Training window</b>Historical observations through the cutoff date</span></div><div><strong>2</strong><span><b>Rolling-origin validation</b>Forecasts evaluated only on later, unseen periods</span></div><div><strong>3</strong><span><b>Baselines</b>Compared with persistence at every horizon</span></div><div><strong>4</strong><span><b>Station audit</b>Metrics reviewed per station, season and AQI band</span></div></div></section><section class="card"><div class="card-title"><h2>Evaluation scope</h2><span class="tag tag-amber">Reproducibility pending</span></div><div class="quality-list"><div class="quality-item"><strong>Chronological</strong><span class="tiny subtle">Split strategy</span></div><div class="quality-item"><strong>24 / 48 / 72h</strong><span class="tiny subtle">Horizons</span></div><div class="quality-item"><strong>RMSE · MAE</strong><span class="tiny subtle">Primary metrics</span></div><div class="quality-item"><strong>Persistence</strong><span class="tiny subtle">Baseline</span></div></div><p class="tiny subtle" style="line-height:1.55;margin-top:12px">Before deployment, attach the evaluation script version, exact cutoff dates, station list, row counts and dataset hashes.</p></section></div><section class="card" style="margin-top:16px"><div class="card-title"><div><h2>Held-out performance</h2><span class="tiny subtle">PM2.5 · units in µg/m³ · lower is better</span></div><span class="tag tag-blue">Project evaluation snapshot</span></div><div class="table-scroll"><table class="metric-table"><thead><tr><th>Horizon</th><th>Model RMSE</th><th>Persistence RMSE</th><th>Improvement</th><th>Operational interpretation</th></tr></thead><tbody><tr><td><strong>24 hours</strong></td><td>35.58</td><td>47.82</td><td class="positive">25.59%</td><td>Best-supported horizon for response planning</td></tr><tr><td><strong>48 hours</strong></td><td>50.87</td><td>58.77</td><td class="positive">13.45%</td><td>Use with confidence band and daily review</td></tr><tr><td><strong>72 hours</strong></td><td>56.14</td><td>61.70</td><td class="positive">9.00%</td><td>Planning signal only; do not treat as precise</td></tr></tbody></table></div></section><div class="grid model-evidence-grid" style="margin-top:16px"><section class="card"><div class="card-title"><h2>Known limitations</h2></div><ul class="limitations"><li>Accuracy degrades during extreme or previously unseen pollution events.</li><li>Missing station observations can widen uncertainty or suppress a forecast.</li><li>Road and land-use evidence indicates correlation, not chemical source apportionment.</li><li>Station forecasts should not be presented as street-level exposure estimates.</li></ul></section><section class="card"><div class="card-title"><h2>Deployment gates</h2></div><div class="gate"><span>✓</span><div><strong>Baseline improvement</strong><small>Passed at all reported horizons</small></div></div><div class="gate"><span>✓</span><div><strong>Chronological validation</strong><small>Reported in project evaluation</small></div></div><div class="gate pending"><span>!</span><div><strong>Reproducibility bundle</strong><small>Dataset hashes and evaluation artifact required</small></div></div><div class="gate pending"><span>!</span><div><strong>Live drift monitoring</strong><small>Connect after backend integration</small></div></div></section></div></main>`;
}

function adminPage(page) {
  return ({pulse:pulsePage,forecast:forecastPage,evidence:evidencePage,actions:actionsPage,alerts:alertsPage,model:modelPage}[page] || pulsePage)();
}

function citizenShell(tab) {
  const activeTab = tab === 'map' ? 'home' : tab;
  return `<div class="citizen-shell"><header class="citizen-nav">${brand()}<nav class="citizen-links">${citizenNav.map(([id,label])=>`<button class="${activeTab===id?'active':''}" data-citizen="${id}">${label}</button>`).join('')}</nav><div style="display:flex;gap:8px"><button class="btn btn-secondary btn-small">EN</button><button class="btn btn-secondary btn-small" data-go="landing">Sign out</button></div></header><main class="citizen-main">${citizenPage(tab)}</main></div>`;
}

function citizenPage(tab) {
  if(tab === 'map') return `${pageHeading('Air near you','Explore monitoring stations and neighbourhood conditions.')}${mapCard(false)}`;
  if(['plan','forecast','guidance','alerts'].includes(tab)) return citizenPlan();
  return citizenHome();
}

function citizenPlan() {
  return `${pageHeading('Plan & Alerts','One place to check what is coming, protect your health and choose when AQIS should notify you.')}<div class="citizen-plan-stack">
    <section class="card chart-card"><div class="card-title"><div><h2>72-hour forecast</h2><span class="tiny subtle">PM2.5 · Borivali East</span></div><span class="tag tag-amber">Morning peak expected</span></div><div class="chart-wrap">${chartSvg()}</div><div class="alert-box"><span style="font-size:22px">◷</span><div><strong>Best outdoor window</strong><div class="tiny subtle">Tomorrow after 4 PM, when pollution is expected to begin falling.</div></div></div></section>
    <section class="card"><div class="card-title"><div><h2>Health guidance</h2><span class="tiny subtle">Matched to the current Poor category</span></div><span class="tag tag-green">Personal guidance</span></div><div class="guidance"><div class="guidance-item"><span>⌂</span><strong>This morning</strong><p class="tiny subtle">Sensitive people should reduce prolonged outdoor activity.</p></div><div class="guidance-item"><span>◷</span><strong>Plan for later</strong><p class="tiny subtle">Move exercise or outdoor errands to after 4 PM.</p></div><div class="guidance-item"><span>♡</span><strong>Be prepared</strong><p class="tiny subtle">Keep prescribed reliever medication available.</p></div></div></section>
    <section class="card alert-settings"><div><span class="tag tag-blue">Optional</span><h2>Get an air-quality alert</h2><p class="subtle">We will notify you when conditions near your saved location worsen.</p></div><div class="alert-form"><div class="field"><label>Notify me when</label><select><option>AQI becomes Poor</option><option>AQI becomes Very Poor</option><option>Any forecast worsens</option></select></div><div class="field"><label>Channel</label><select><option>WhatsApp</option><option>SMS</option><option>Email</option></select></div><button class="btn btn-primary" data-citizen-alert>Save alert</button></div><div class="tiny subtle saved-location">Saved location: Borivali East, Mumbai</div></section>
  </div>`;
}

function citizenHome() {
  const forecasts = [24,48,72].map(h => cachedForecast(h));
  const fallback = [{pm25:88,aqi_category:'Poor'},{pm25:92,aqi_category:'Poor'},{pm25:74,aqi_category:'Moderately Polluted'}];
  const values = forecasts.map((forecast,index)=>forecast || fallback[index]);
  const aqiValues = values.map(item=>pm25ToAqi(Number(item.pm25)));
  const station = intelligence()?.location?.replace(/, (Mumbai|Delhi).*$/,'') || 'Borivali East';
  const connected = state.backend.connected || state.backend.liveConnected;
  return `<section class="citizen-hero"><div><div class="eyebrow" style="color:#9cf2e8">${station} · ${state.backend.liveConnected?'LIVE AIR FEED':'MODEL CACHE CONNECTED'}</div><h1>${connected?`Tomorrow’s forecast is ${values[0].aqi_category}.`:'Your air is Poor right now.'}</h1><p>${state.backend.liveConnected?'Live PM2.5 conditions and the next 72 hours are supplied by Open-Meteo/CAMS for the selected coordinates.':'This forecast uses the project’s precomputed XGBoost inference.'}</p><div style="display:flex;gap:10px;flex-wrap:wrap"><button class="btn btn-secondary" data-citizen="plan">View health guidance</button><button class="btn btn-soft" data-citizen="plan">Forecast & alerts</button></div></div><div class="citizen-aqi"><div class="aqi-ring"><div><span>${connected?'24H AQI':'AQI'}</span><strong>${aqiValues[0]}</strong><small>PM2.5 ${Number(values[0].pm25).toFixed(1)} µg/m³</small></div></div></div></section><div class="grid citizen-grid"><section class="card"><div class="card-title"><h2>Next 3 horizons</h2><button class="btn btn-soft btn-small" data-citizen="plan">Plan ahead</button></div><div class="forecast-strip">${values.map((item,index)=>`<div class="forecast-day"><span class="tiny subtle">+${[24,48,72][index]} hours</span><strong>${aqiValues[index]}</strong><span class="tag ${aqiValues[index]>150?'tag-red':aqiValues[index]>100?'tag-amber':'tag-green'}">${item.aqi_category}</span></div>`).join('')}</div><div class="alert-box"><span style="font-size:22px">◷</span><div><strong>${state.backend.liveConnected?'Live forecast':'Precomputed forecast'}</strong><div class="tiny subtle">${state.backend.liveConnected?`Updated ${state.backend.live.observedAt} · Open-Meteo/CAMS.`:`Model timestamp: ${intelligence()?.timestamp || 'cached demo'}.`}</div></div></div></section><section class="card"><div class="card-title"><h2>Nearby station</h2><span class="tag tag-green">${state.backend.liveConnected?'Live':'Model data'}</span></div><div class="citizen-map"><div class="leaflet-map" data-live-map="evidence"></div></div><button class="btn btn-secondary btn-small" style="width:100%;margin-top:12px" data-citizen="map">Explore map</button></section></div>`;
}

function downloadFile(filename, content, type = 'text/plain') {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function exportForecast() {
  const d = pollutantData();
  const rows = ['station,pollutant,horizon_hours,forecast_time,value,unit,model_version'];
  ['Now','+24h','+48h','+72h'].forEach((time,index) => rows.push(`Borivali East,${state.forecast.pollutant},${state.forecast.horizon},${time},${d.values[index]},${d.unit},4.2`));
  downloadFile(`aqis-${state.forecast.pollutant.replace(/[^a-z0-9]/gi,'').toLowerCase()}-forecast.csv`, rows.join('\n'), 'text/csv');
}

function exportResponseReport() {
  const report = document.querySelector('#responseReport');
  if(!report) return;
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>${state.plan.reportId}</title><style>body{font:15px Arial;max-width:850px;margin:40px auto;color:#172523;line-height:1.5}h1,h2,h3,h4{color:#075f57}li{margin:7px 0}.approval-line{display:flex;justify-content:space-between;border-top:1px solid #bbb;margin-top:30px;padding-top:20px}</style></head><body><p><strong>AQIS Urban Air Intelligence</strong></p>${report.innerHTML}<hr><small>Generated from the AQIS frontend prototype. Approval signatures must be completed by the responsible authority.</small></body></html>`;
  downloadFile(`${state.plan.reportId}.html`, html, 'text/html');
}

async function loadBackendData() {
  state.backend.loading = true;
  try {
    const city = state.city.toLowerCase();
    const [healthResponse, stationsResponse, intelligenceResponse, metricsResponse] = await Promise.all([
      fetch('/api/health'),
      fetch(`/api/stations?city=${encodeURIComponent(city)}`),
      fetch(`/api/intelligence?city=${encodeURIComponent(city)}&station=${encodeURIComponent(state.backend.stationId)}`),
      fetch('/api/model/metrics')
    ]);
    if(!healthResponse.ok || !stationsResponse.ok || !intelligenceResponse.ok) throw new Error('Model service unavailable');
    const [health, stations, modelIntelligence, metrics] = await Promise.all([
      healthResponse.json(), stationsResponse.json(), intelligenceResponse.json(), metricsResponse.ok ? metricsResponse.json() : null
    ]);
    state.backend.connected = health.status === 'ok';
    state.backend.mode = health.mode;
    state.backend.stations = stations.stations || [];
    if(!state.backend.stations.some(station=>station.id===state.backend.stationId) && state.backend.stations.length) state.backend.stationId = state.backend.stations[0].id;
    state.backend.intelligence = modelIntelligence;
    state.backend.metrics = metrics;
    await loadLiveAirQuality();
    const peakAqi = Math.max(...[24,48,72].map(h=>cachedForecast(h)).filter(Boolean).map(item=>pm25ToAqi(Number(item.pm25))));
    if(Number.isFinite(peakAqi) && peakAqi <= 100) { state.forecast.trafficReduction = 0; state.forecast.constructionControl = false; state.forecast.industryReduction = 0; }
  } catch(error) {
    state.backend.connected = false;
    state.backend.mode = 'frontend-fallback';
    state.backend.stations = fallbackStations[state.city.toLowerCase()];
    state.backend.stationId = state.backend.stations[0].id;
    await loadLiveAirQuality();
  } finally {
    state.backend.loading = false;
    render();
  }
}

async function loadStationIntelligence() {
  try {
    const response = await fetch(`/api/intelligence?city=${encodeURIComponent(state.city.toLowerCase())}&station=${encodeURIComponent(state.backend.stationId)}`);
    if(!response.ok) throw new Error('Station not found');
    state.backend.intelligence = await response.json();
    state.backend.connected = true;
    await loadLiveAirQuality();
    const peakAqi = Math.max(...[24,48,72].map(h=>cachedForecast(h)).filter(Boolean).map(item=>pm25ToAqi(Number(item.pm25))));
    if(Number.isFinite(peakAqi) && peakAqi <= 100) { state.forecast.trafficReduction = 0; state.forecast.constructionControl = false; state.forecast.industryReduction = 0; }
    render();
  } catch(error) {
    toast('Could not load this station. Existing data remains visible.');
  }
}

async function submitResponseReport() {
  try {
    const response = await fetch('/api/reports', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ plan:state.plan, actions:state.actions, station:state.backend.stationId, intelligence:intelligence() }) });
    if(!response.ok) throw new Error('Save failed');
    const saved = await response.json();
    state.plan.status = 'Pending approval';
    state.plan.reportId = saved.id;
    render();
    toast(`Report ${saved.id} saved to the backend.`);
  } catch(error) { toast('Backend unavailable. Report was not submitted.'); }
}

async function publishAlertRecord() {
  try {
    const response = await fetch('/api/alerts', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ station:state.backend.stationId, language:state.alertLanguage, message:document.querySelector('#alertText')?.value || '' }) });
    if(!response.ok) throw new Error('Save failed');
    const saved = await response.json();
    toast(`Alert ${saved.id} recorded. No external message was sent.`);
  } catch(error) { toast('Backend unavailable. Alert was not recorded.'); }
}

function render() {
  const route = location.hash.replace('#/', '') || 'landing';
  state.route = route;
  if(route === 'landing') { location.replace('./landing.html'); return; }
  else if(route === 'citizen-login') app.innerHTML = loginPage('citizen');
  else if(route === 'admin-login') app.innerHTML = loginPage('admin');
  else if(route.startsWith('admin/')) app.innerHTML = adminShell(route.split('/')[1] || 'pulse');
  else if(route.startsWith('citizen/')) app.innerHTML = citizenShell(route.split('/')[1] || 'home');
  else app.innerHTML = landing();
  requestAnimationFrame(mountLiveMaps);
  window.scrollTo(0,0);
}

window.addEventListener('hashchange', render);

document.addEventListener('click', (event) => {
  const go = event.target.closest('[data-go]'); if(go) return navigate(go.dataset.go);
  const admin = event.target.closest('[data-admin]'); if(admin) return navigate(`admin/${admin.dataset.admin}`);
  const citizen = event.target.closest('[data-citizen]'); if(citizen) return navigate(`citizen/${citizen.dataset.citizen}`);
  const demo = event.target.closest('[data-demo]'); if(demo) return navigate(`${demo.dataset.demo}/${demo.dataset.demo==='admin'?'pulse':'home'}`);
  const horizon = event.target.closest('[data-horizon]'); if(horizon) { state.horizon = horizon.dataset.horizon; return render(); }
  const layerToggle = event.target.closest('[data-layer-toggle]'); if(layerToggle) { document.querySelector('#layers')?.classList.toggle('hidden'); return; }
  const language = event.target.closest('[data-language]'); if(language) { state.alertLanguage = language.dataset.language; return render(); }
  const pollutant = event.target.closest('[data-forecast-pollutant]'); if(pollutant) { state.forecast.pollutant = pollutant.dataset.forecastPollutant; return render(); }
  const forecastHorizon = event.target.closest('[data-forecast-horizon]'); if(forecastHorizon) { state.forecast.horizon = forecastHorizon.dataset.forecastHorizon; return render(); }
  const forecastMapHorizon = event.target.closest('[data-forecast-map-horizon]'); if(forecastMapHorizon) { state.forecast.mapHour = forecastMapHorizon.dataset.forecastMapHorizon; return render(); }
  const policy = event.target.closest('[data-policy-key]'); if(policy) { const raw = policy.dataset.policyValue; state.forecast[policy.dataset.policyKey] = raw === 'true' ? true : raw === 'false' ? false : Number(raw); return render(); }
  if(event.target.closest('[data-download-forecast]')) { exportForecast(); return toast('Forecast CSV downloaded.'); }
  if(event.target.closest('[data-save-report]')) { localStorage.setItem('aqis-response-draft', JSON.stringify({ actions: state.actions, plan: state.plan })); return toast(`Draft ${state.plan.reportId} saved locally.`); }
  if(event.target.closest('[data-export-report]')) { exportResponseReport(); return toast('Response report downloaded as a printable HTML file.'); }
  if(event.target.closest('[data-submit-report]')) return submitResponseReport();
  if(event.target.closest('[data-save]')) toast('Draft saved in this frontend preview.');
  if(event.target.closest('[data-create-plan]')) toast('Response plan created and ready for export.');
  if(event.target.closest('[data-publish]')) return publishAlertRecord();
  if(event.target.closest('[data-citizen-alert]')) toast('Alert preference saved for this preview.');
  if(event.target.closest('[data-menu]')) document.querySelector('#sidebar')?.classList.toggle('open');
  if(event.target.closest('[data-mode]')) toast('Demo data is active. Live integration comes in the next phase.');
});

document.addEventListener('change', (event) => {
  if(event.target.matches('[data-layer]')) { state.layers[event.target.dataset.layer] = event.target.checked; render(); }
  if(event.target.matches('[data-action]')) { state.actions[event.target.dataset.action] = event.target.checked; render(); }
  if(event.target.matches('[data-forecast-option]')) { state.forecast[event.target.dataset.forecastOption] = event.target.checked; render(); }
  if(event.target.matches('[data-forecast-aggregation]')) { state.forecast.aggregation = event.target.value; render(); }
  if(event.target.matches('[data-plan-field]')) { state.plan[event.target.dataset.planField] = event.target.value; render(); }
  if(event.target.matches('[data-city-select]')) { state.city = event.target.value; state.backend.stationId = ''; loadBackendData(); }
  if(event.target.matches('[data-station-select]')) { state.backend.stationId = event.target.value; loadStationIntelligence(); }
  if(event.target.matches('[data-scenario="constructionControl"]')) { state.forecast.constructionControl = event.target.checked; render(); }
});

document.addEventListener('input', (event) => {
  if(event.target.id === 'alertText') document.querySelector('#messagePreview').childNodes[0].textContent = event.target.value;
  if(event.target.matches('[data-scenario="trafficReduction"], [data-scenario="industryReduction"]')) { state.forecast[event.target.dataset.scenario] = Number(event.target.value); render(); }
});

document.addEventListener('submit', (event) => {
  const form = event.target.closest('[data-login]');
  if(!form) return;
  event.preventDefault();
  navigate(`${form.dataset.login}/${form.dataset.login==='admin'?'pulse':'home'}`);
});

render();
loadBackendData();
