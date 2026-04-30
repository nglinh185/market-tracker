/* ============================================
   Market Intelligence Dashboard — app.js
   Today's Pulse: Winners, Risks, Deals, Alerts.
   ============================================ */

const CFG = window.APP_CONFIG || {};
const sb  = window.supabase.createClient(CFG.SUPABASE_URL, CFG.SUPABASE_ANON_KEY);

const CATEGORY_LABELS = {
  gaming_keyboard:        'Gaming Keyboards',
  true_wireless_earbuds:  'True Wireless Earbuds',
  portable_charger:       'Portable Chargers',
};
const CATEGORY_COLORS = {
  gaming_keyboard:        '#06b6d4',
  true_wireless_earbuds:  '#a855f7',
  portable_charger:       '#22c55e',
};
const ALERT_TYPE_LABEL = {
  price_drop:  'price drop',
  new_entrant: 'new entrant',
  exit:        'exit',
  bsr_spike:   'BSR spike',
  stockout:    'stockout',
};
const SEVERITY_COLOR = { high: 'bad', medium: 'warn', low: 'muted' };

const fmt = {
  num:    n => (n ?? 0).toLocaleString('en-US'),
  signed: n => (n > 0 ? '+' : '') + n.toFixed(2),
  pct:    n => (n >= 0 ? '+' : '') + n.toFixed(1) + '%',
  date:   d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  short:  (s, n = 38) => !s ? '—' : s.length > n ? s.slice(0, n - 1) + '…' : s,
};

function isoDaysAgo(n) {
  const d = new Date(); d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

// Cache shared across renderers
const STATE = {};

// ========== Boot ==========
async function main() {
  if (!CFG.SUPABASE_URL || CFG.SUPABASE_URL.includes('%%')) {
    return showConfigError();
  }
  try {
    // 1. Latest snapshot date (today's data window)
    STATE.today = await getLatestDate();
    STATE.weekAgo = isoDaysAgo(7);
    document.getElementById('last-updated').textContent =
      `Latest data: ${new Date(STATE.today).toLocaleDateString('en-US', { day:'2-digit', month:'short', year:'numeric' })}`;

    // 2. Parallel fetches (BMS + sentiment from separate tables, JOIN client-side)
    const [meta, todaySnap, weekAgoSnap, alertsToday, alertsWeek, bmsToday, sentToday] = await Promise.all([
      loadMeta(),
      loadSnapshots(STATE.today),
      loadSnapshots(STATE.weekAgo),
      loadAlertsByDate(STATE.today),
      loadAlertsSince(isoDaysAgo(7)),
      loadBms(STATE.today),
      loadSentiment(STATE.today),
    ]);

    // Merge BMS + sentiment into todaySnap rows (JOIN by ASIN)
    const bmsMap  = Object.fromEntries(bmsToday.map(r => [r.asin, r.bms_score]));
    const sentMap = Object.fromEntries(sentToday.map(r => [r.asin, r.avg_sentiment_score]));
    todaySnap.forEach(r => {
      if (r.bms_score == null)       r.bms_score       = bmsMap[r.asin]  ?? null;
      if (r.sentiment_score == null) r.sentiment_score = sentMap[r.asin] ?? null;
    });

    Object.assign(STATE, { meta, todaySnap, weekAgoSnap, alertsToday, alertsWeek });

    // 3. Render
    renderKpis();
    await renderBsrChart();
    renderSentimentChart();
    renderOpportunities();
    renderRisks();
    renderEventsFeed();
  } catch (err) {
    console.error('Dashboard error:', err);
    document.getElementById('last-updated').textContent = `Error: ${err.message}`;
  }
}

// ========== Loaders ==========
async function getLatestDate() {
  const { data } = await sb.from('daily_snapshots')
    .select('snapshot_date').order('snapshot_date', { ascending: false }).limit(1);
  return data?.[0]?.snapshot_date || new Date().toISOString().slice(0, 10);
}

async function loadMeta() {
  const { data } = await sb.from('asins').select('asin,product_name,brand,category');
  const map = {};
  (data || []).forEach(m => map[m.asin] = m);
  return map;
}

async function loadSnapshots(date) {
  const { data } = await sb.from('daily_snapshots')
    .select('asin,bsr,price,list_price,discount_pct,bms_score,sentiment_score,in_stock')
    .eq('snapshot_date', date);
  return data || [];
}

async function loadAlertsByDate(date) {
  const { data } = await sb.from('alerts')
    .select('asin,alert_type,severity,message,browse_node')
    .eq('snapshot_date', date);
  return data || [];
}

async function loadAlertsSince(date) {
  const { data } = await sb.from('alerts')
    .select('snapshot_date,asin,alert_type,severity,message,browse_node')
    .gte('snapshot_date', date)
    .order('snapshot_date', { ascending: false });
  return data || [];
}

async function loadBms(date) {
  const { data } = await sb.from('brand_momentum_daily')
    .select('asin,bms_score')
    .eq('snapshot_date', date);
  return data || [];
}

async function loadSentiment(date) {
  const { data } = await sb.from('review_sentiment_daily')
    .select('asin,avg_sentiment_score')
    .eq('snapshot_date', date);
  return data || [];
}

// ========== Helpers ==========
function metaOf(asin) {
  return STATE.meta[asin] || { product_name: asin, brand: '', category: '' };
}

function nameOf(asin) {
  const m = metaOf(asin);
  return fmt.short(m.product_name || asin, 38);
}

function brandOf(asin) {
  return metaOf(asin).brand || '';
}

function bsrDelta(asin) {
  const t = STATE.todaySnap.find(r => r.asin === asin);
  const p = STATE.weekAgoSnap.find(r => r.asin === asin);
  if (!t?.bsr || !p?.bsr) return null;
  return t.bsr - p.bsr;  // negative = better rank
}

// ========== KPI cards ==========
function renderKpis() {
  // Winner: biggest BSR improvement (most negative delta)
  let winner = null, winnerDelta = 0;
  let risk = null, riskDelta = 0;
  STATE.todaySnap.forEach(r => {
    const d = bsrDelta(r.asin);
    if (d === null) return;
    if (d < winnerDelta) { winnerDelta = d; winner = r; }
    if (d > riskDelta)   { riskDelta = d;   risk   = r; }
  });
  if (winner) setKpi('kpi-winner', nameOf(winner.asin), `↑ ${Math.abs(winnerDelta)} BSR ranks · BMS ${(winner.bms_score ?? 0).toFixed(2)}`);
  else        setKpi('kpi-winner', '—', 'Not enough data');
  if (risk)   setKpi('kpi-risk', nameOf(risk.asin), `↓ ${riskDelta} BSR ranks · BMS ${(risk.bms_score ?? 0).toFixed(2)}`);
  else        setKpi('kpi-risk', '—', 'Not enough data');

  // Best deal today: highest discount_pct
  const deals = STATE.todaySnap
    .filter(r => r.discount_pct && r.discount_pct > 0)
    .sort((a, b) => b.discount_pct - a.discount_pct);
  if (deals.length) {
    const d = deals[0];
    setKpi('kpi-deal', nameOf(d.asin), `${d.discount_pct.toFixed(0)}% off · $${(d.price ?? 0).toFixed(2)} (was $${(d.list_price ?? 0).toFixed(2)})`);
  } else {
    setKpi('kpi-deal', '—', 'No active discounts');
  }

  // Active alerts today
  const total = STATE.alertsToday.length;
  const high  = STATE.alertsToday.filter(a => a.severity === 'high').length;
  const med   = STATE.alertsToday.filter(a => a.severity === 'medium').length;
  setKpi('kpi-alerts', total, `${high} high · ${med} medium`);
}

function setKpi(id, value, sub) {
  const card = document.getElementById(id);
  if (!card) return;
  const v = card.querySelector('.kpi-value');
  v.textContent = value;
  if (typeof value === 'string' && value.length > 12) v.classList.add('text-xl');
  card.querySelector('.kpi-sub').textContent = sub ?? '';
}

// ========== Chart 1: BSR trend top 5 by BMS ==========
async function renderBsrChart() {
  // Pick top 5 ASINs by today's BMS
  const top5 = [...STATE.todaySnap]
    .filter(r => r.bms_score != null && r.bsr != null)
    .sort((a, b) => (b.bms_score ?? 0) - (a.bms_score ?? 0))
    .slice(0, 5);

  if (!top5.length) {
    document.getElementById('chart-bsr').innerHTML = '<div class="text-xs text-muted py-12 text-center">No BSR data.</div>';
    return;
  }

  const since = isoDaysAgo(14);
  const { data: trend } = await sb.from('daily_snapshots')
    .select('asin,snapshot_date,bsr')
    .in('asin', top5.map(r => r.asin))
    .gte('snapshot_date', since)
    .order('snapshot_date', { ascending: true });

  const dates = [...new Set((trend || []).map(r => r.snapshot_date))].sort();
  const series = top5.map((r, i) => ({
    name:   fmt.short(metaOf(r.asin).product_name || r.asin, 28),
    type:   'line', smooth: true, showSymbol: false,
    lineStyle: { width: 2.2 },
    data:   dates.map(d => {
      const row = (trend || []).find(t => t.asin === r.asin && t.snapshot_date === d);
      return row?.bsr ?? null;
    }),
  }));

  const chart = echarts.init(document.getElementById('chart-bsr'), null, { renderer: 'canvas' });
  chart.setOption({
    backgroundColor: 'transparent',
    color: ['#06b6d4', '#a855f7', '#22c55e', '#f59e0b', '#ef4444'],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,23,41,0.95)', borderColor: '#1e293b',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
    },
    legend: {
      bottom: 0, left: 'center', icon: 'circle', itemWidth: 8, itemHeight: 8,
      textStyle: { color: '#94a3b8', fontSize: 10 },
    },
    grid: { left: 40, right: 10, top: 10, bottom: 50 },
    xAxis: {
      type: 'category', data: dates.map(fmt.date),
      axisLine: { lineStyle: { color: '#1e293b' } },
      axisLabel: { color: '#64748b', fontSize: 10 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value', inverse: true,
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 10 },
      name: 'BSR (lower=better)', nameTextStyle: { color: '#64748b', fontSize: 10 },
    },
    series,
  });
  window.addEventListener('resize', () => chart.resize());
}

// ========== Chart 2: Sentiment by Category ==========
function renderSentimentChart() {
  const buckets = {};
  STATE.todaySnap.forEach(r => {
    if (r.sentiment_score == null) return;
    const cat = metaOf(r.asin).category;
    if (!cat) return;
    if (!buckets[cat]) buckets[cat] = [];
    buckets[cat].push(r.sentiment_score);
  });
  const cats = Object.keys(buckets);
  const avgs = cats.map(c => {
    const vals = buckets[c]; return vals.reduce((a, b) => a + b, 0) / vals.length;
  });
  const labels = cats.map(c => CATEGORY_LABELS[c] || c);
  const colors = cats.map(c => CATEGORY_COLORS[c] || '#06b6d4');

  if (!cats.length) {
    document.getElementById('chart-sentiment').innerHTML = '<div class="text-xs text-muted py-12 text-center">No sentiment data.</div>';
    return;
  }

  const chart = echarts.init(document.getElementById('chart-sentiment'), null, { renderer: 'canvas' });
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: 'rgba(15,23,41,0.95)', borderColor: '#1e293b',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: p => `${p[0].name}<br/><b>${p[0].value.toFixed(3)}</b>`,
    },
    grid: { left: 150, right: 50, top: 20, bottom: 30 },
    xAxis: {
      type: 'value', min: -1, max: 1,
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 10 },
    },
    yAxis: {
      type: 'category', data: labels,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: '#cbd5e1', fontSize: 11 },
    },
    series: [{
      type: 'bar',
      data: avgs.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: 4 } })),
      label: { show: true, position: 'right', color: '#e2e8f0', fontSize: 11, formatter: p => p.value.toFixed(2) },
      barWidth: 22,
    }],
  });
  window.addEventListener('resize', () => chart.resize());
}

// ========== Opportunities (top BMS + good sentiment) ==========
function renderOpportunities() {
  const items = [...STATE.todaySnap]
    .filter(r => r.bms_score != null && r.sentiment_score != null)
    .sort((a, b) => {
      // weighted: BMS 0.6 + sentiment 0.4
      const sa = (a.bms_score ?? 0) * 0.6 + (a.sentiment_score ?? 0) * 0.4;
      const sb = (b.bms_score ?? 0) * 0.6 + (b.sentiment_score ?? 0) * 0.4;
      return sb - sa;
    })
    .slice(0, 3);

  const html = items.length ? items.map((r, i) => `
    <div class="event-row">
      <span class="rank-badge">${String(i + 1).padStart(2, '0')}</span>
      <div class="flex-1 min-w-0">
        <div class="text-sm text-fg truncate">${nameOf(r.asin)}</div>
        <div class="text-xs text-muted">${brandOf(r.asin) || '—'} · ${r.asin}</div>
      </div>
      <div class="text-right">
        <div class="text-sm font-mono text-accent">BMS ${r.bms_score.toFixed(2)}</div>
        <div class="text-xs ${r.sentiment_score > 0 ? 'delta-pos' : 'delta-neg'}">sent ${fmt.signed(r.sentiment_score)}</div>
      </div>
    </div>
  `).join('') : `<div class="text-xs text-muted py-4 text-center">No opportunity candidates.</div>`;

  document.getElementById('opps-list').innerHTML = html;
}

// ========== Risks (high-severity alerts) ==========
function renderRisks() {
  const items = STATE.alertsToday
    .filter(a => a.severity === 'high')
    .slice(0, 3);

  const html = items.length ? items.map((a, i) => `
    <div class="event-row">
      <span class="rank-badge rank-bad">${String(i + 1).padStart(2, '0')}</span>
      <div class="flex-1 min-w-0">
        <div class="text-sm text-fg truncate">${nameOf(a.asin)}</div>
        <div class="text-xs text-muted">${brandOf(a.asin) || '—'} · ${a.asin}</div>
      </div>
      <div class="text-right">
        <div class="text-xs font-medium text-bad uppercase tracking-wider">${ALERT_TYPE_LABEL[a.alert_type] || a.alert_type}</div>
        <div class="text-xs text-muted truncate max-w-[180px]">${fmt.short(a.message, 30)}</div>
      </div>
    </div>
  `).join('') : `<div class="text-xs text-muted py-4 text-center">No high-severity alerts. ✓</div>`;

  document.getElementById('risks-list').innerHTML = html;
}

// ========== Recent events feed ==========
function renderEventsFeed() {
  const items = STATE.alertsWeek.slice(0, 10);
  const html = items.length ? items.map(a => {
    const sev = SEVERITY_COLOR[a.severity] || 'muted';
    return `
      <div class="flex items-start gap-3 py-2 border-b border-border/40">
        <span class="dot dot-${sev}"></span>
        <div class="text-xs text-muted whitespace-nowrap">${fmt.date(a.snapshot_date)}</div>
        <div class="text-xs px-2 py-0.5 rounded bg-card border border-border text-${sev} font-medium uppercase tracking-wider">${ALERT_TYPE_LABEL[a.alert_type] || a.alert_type}</div>
        <div class="flex-1 text-sm text-fg">${fmt.short(nameOf(a.asin), 30)} <span class="text-muted">— ${fmt.short(a.message, 80)}</span></div>
      </div>
    `;
  }).join('') : `<div class="text-xs text-muted py-4 text-center">No events in window.</div>`;

  document.getElementById('events-feed').innerHTML = html;
}

// ========== Misc ==========
function showConfigError() {
  document.body.innerHTML = `
    <div class="max-w-2xl mx-auto p-10 text-center">
      <h1 class="text-2xl font-bold text-bad mb-4">⚠️ Supabase config missing</h1>
      <p class="text-muted">Set <code class="bg-card px-2 py-1 rounded text-fg">SUPABASE_URL</code> +
        <code class="bg-card px-2 py-1 rounded text-fg">SUPABASE_ANON_KEY</code> in <code>index.html</code>.</p>
    </div>`;
}

document.addEventListener('DOMContentLoaded', main);
