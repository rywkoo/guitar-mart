{% extends "admin/base.html" %}

{% block title %}Admin Dashboard{% endblock %}

{% block content %}
<h1 style="font-size:2rem;font-weight:700;color:#1d1d1f;margin-bottom:1rem;">Dashboard</h1>
<p class="text-muted">Welcome, <span id="adminUsername">Admin</span>. Manage your store and view analytics here.</p>

<div id="dashboardGrid" style="
    display:grid;
    grid-template-columns:repeat(auto-fill,minmax(250px,1fr));
    gap:1.5rem;
    margin-top:1rem;
">
  <!-- Stats Cards Loaded via JS -->
</div>

<!-- ---------- INVOICE LIST + CHART (side-by-side) ---------- -->
<div style="display:flex; gap:2rem; margin-top:2rem; flex-wrap:wrap;">

  <!-- LEFT: Last 10 invoices -->
  <div style="flex:1; min-width:300px; background:#fff; padding:1.5rem; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,.05); max-height:500px; overflow-y:auto;">
    <h3 style="font-weight:700;color:#1d1d1f;margin-bottom:1rem;">Last 10 Invoices</h3>
    <table style="width:100%; border-collapse:collapse;">
      <thead>
        <tr>
          <th style="border-bottom:1px solid #ddd;padding:.5rem;text-align:left;">#</th>
          <th style="border-bottom:1px solid #ddd;padding:.5rem;text-align:left;">Invoice</th>
          <th style="border-bottom:1px solid #ddd;padding:.5rem;text-align:left;">User</th>
          <th style="border-bottom:1px solid #ddd;padding:.5rem;text-align:right;">Amount</th>
          <th style="border-bottom:1px solid #ddd;padding:.5rem;text-align:left;">Date</th>
        </tr>
      </thead>
      <tbody id="invoiceListBody"></tbody>
    </table>
  </div>

  <!-- RIGHT: Purchase chart (filtered by selected invoice's user) -->
  <div style="flex:2; min-width:350px; background:#fff; padding:2rem; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,.05);">
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.5rem; align-items:center;">
      <h3 id="chartTitle" style="font-weight:700;color:#1d1d1f;margin:0;">Select an invoice to view user purchases</h3>

      <div style="margin-left:auto; display:flex; gap:.5rem;">
        <select id="reportType" style="padding:.4rem .8rem;border:1px solid #ced4da;border-radius:6px;">
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
          <option value="custom">Custom</option>
        </select>

        <input type="date" id="startDate" style="padding:.4rem .8rem;border:1px solid #ced4da;border-radius:6px;display:none;">
        <input type="date" id="endDate"   style="padding:.4rem .8rem;border:1px solid #ced4da;border-radius:6px;display:none;">
      </div>
    </div>

    <canvas id="purchaseChart" style="width:100%;max-height:400px;"></canvas>
  </div>
</div>
{% endblock %}


{% block scripts %}
<!-- Chart.js + time adapter -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3"></script>

<script>
/* ------------------------------------------------------------------ */
/*  Global variables                                                  */
/* ------------------------------------------------------------------ */
let purchaseChart = null;
let selectedUsername = null;   // user from clicked invoice

/* ------------------------------------------------------------------ */
/*  Load product / category stats                                     */
/* ------------------------------------------------------------------ */
async function loadCounts() {
  try {
    const opts = { credentials: 'include', headers: { Accept: 'application/json' } };
    const [prodRes, catRes] = await Promise.all([
      fetch('/admin/api/products', opts),
      fetch('/admin/api/categories', opts)
    ]);

    if (!prodRes.ok || !catRes.ok) throw new Error('API error');

    const products   = await prodRes.json();
    const categories = await catRes.json();

    const grid = document.getElementById('dashboardGrid');
    grid.innerHTML = `
      <div class="stat-card">
        <div class="stat-title">Total Products</div>
        <h2 class="stat-value" style="color:#4f46e5;">${products.length}</h2>
        <small class="text-muted">Active items</small>
      </div>
      <div class="stat-card">
        <div class="stat-title">Total Categories</div>
        <h2 class="stat-value" style="color:#16a34a;">${categories.length}</h2>
        <small class="text-muted">Product groupings</small>
      </div>
    `;

    grid.querySelectorAll('.stat-card').forEach(c => {
      c.addEventListener('mouseenter', () => c.style.transform = 'translateY(-4px)');
      c.addEventListener('mouseleave', () => c.style.transform = '');
    });

  } catch (e) {
    console.error('loadCounts →', e);
  }
}

/* ------------------------------------------------------------------ */
/*  Load last 10 invoices (for the list)                              */
/* ------------------------------------------------------------------ */
async function loadInvoiceList() {
  try {
    const res = await fetch('/admin/api/invoices', { credentials: 'include' });
    if (!res.ok) throw new Error('Failed to load invoices');
    const allInvoices = await res.json();

    // newest first, take 10
    const latest = allInvoices
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 10);

    const tbody = document.getElementById('invoiceListBody');
    tbody.innerHTML = '';

    latest.forEach((inv, idx) => {
      const tr = document.createElement('tr');
      tr.style.cursor = 'pointer';
      tr.dataset.username = inv.username;
      tr.innerHTML = `
        <td style="padding:.5rem;">${idx + 1}</td>
        <td style="padding:.5rem;">${inv.invoice_number}</td>
        <td style="padding:.5rem;">${inv.username}</td>
        <td style="padding:.5rem;text-align:right;">$${Number(inv.total_amount).toFixed(2)}</td>
        <td style="padding:.5rem;">${inv.created_at.split('T')[0]}</td>
      `;
      tr.addEventListener('click', () => selectInvoice(inv.username));
      tbody.appendChild(tr);
    });

  } catch (e) {
    console.error('loadInvoiceList →', e);
  }
}

/* ------------------------------------------------------------------ */
/*  When an invoice row is clicked → load user purchases               */
/* ------------------------------------------------------------------ */
function selectInvoice(username) {
  selectedUsername = username;
  document.getElementById('chartTitle').textContent = `Purchases of ${username}`;
  loadPurchaseReport();   // uses selectedUsername
}

/* ------------------------------------------------------------------ */
/*  Build line chart for selected user (or clear if none)              */
/* ------------------------------------------------------------------ */
async function loadPurchaseReport() {
  if (!selectedUsername) {
    if (purchaseChart) purchaseChart.destroy();
    return;
  }

  try {
    const type   = document.getElementById('reportType').value;
    const start  = document.getElementById('startDate').value;
    const end    = document.getElementById('endDate').value;

    const params = new URLSearchParams({ type, username: selectedUsername });
    if (type === 'custom') {
      if (!start || !end) return;
      params.append('start', start);
      params.append('end',   end);
    }

    const url = `/admin/api/reports/purchases?${params.toString()}`;
    const res = await fetch(url, { credentials: 'include' });
    if (!res.ok) throw new Error('Report fetch failed');

    const data = await res.json();

    // If endpoint returns per-invoice list (for user mode)
    let labels = [], totals = [];
    if (data.invoices && Array.isArray(data.invoices)) {
      const sorted = data.invoices
        .filter(i => i.username === selectedUsername)
        .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      labels = sorted.map(i => i.created_at.split('T')[0]);
      totals = sorted.map(i => i.total_amount);
    } else {
      // fallback: aggregated labels/totals
      labels = data.labels || [];
      totals = data.totals || [];
    }

    const ctx = document.getElementById('purchaseChart').getContext('2d');
    if (purchaseChart) purchaseChart.destroy();

    purchaseChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: `Purchases of ${selectedUsername}`,
          data: totals,
          backgroundColor: 'rgba(79,70,229,0.2)',
          borderColor: '#4f46e5',
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          pointRadius: 4,
          pointBackgroundColor: '#4f46e5'
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true, position: 'top' },
          tooltip: { mode: 'index', intersect: false }
        },
        scales: {
          y: { beginAtZero: true },
          x: { ticks: { maxRotation: 0 } }
        }
      }
    });

  } catch (e) {
    console.error('loadPurchaseReport →', e);
  }
}

/* ------------------------------------------------------------------ */
/*  UI: Show/hide custom date inputs                                  */
/* ------------------------------------------------------------------ */
document.getElementById('reportType').addEventListener('change', () => {
  const isCustom = document.getElementById('reportType').value === 'custom';
  document.getElementById('startDate').style.display = isCustom ? 'inline-block' : 'none';
  document.getElementById('endDate').style.display   = isCustom ? 'inline-block' : 'none';
  if (selectedUsername) loadPurchaseReport();
});

document.getElementById('startDate').addEventListener('change', () => { if (selectedUsername) loadPurchaseReport(); });
document.getElementById('endDate').addEventListener('change',   () => { if (selectedUsername) loadPurchaseReport(); });

/* ------------------------------------------------------------------ */
/*  Initial load                                                      */
/* ------------------------------------------------------------------ */
document.getElementById('adminUsername').textContent = 'Admin';
loadCounts();
loadInvoiceList();   // will populate list; chart stays empty until click
</script>

<style>
.stat-card {
  background:#fff;
  padding:1.5rem;
  border-radius:12px;
  border:1px solid #e9ecef;
  cursor:pointer;
  box-shadow:0 4px 10px rgba(0,0,0,.05);
  transition:transform .2s, box-shadow .2s;
}
.stat-card:hover {
  transform:translateY(-4px);
  box-shadow:0 8px 20px rgba(0,0,0,.1);
}
.stat-title { font-weight:700; font-size:1.1rem; color:#1d1d1f; }
.stat-value { margin-top:.5rem; }

#invoiceListBody tr:hover {
  background-color: #f8f9fa;
}
#invoiceListBody tr {
  transition: background-color .15s;
}
</style>
{% endblock %}