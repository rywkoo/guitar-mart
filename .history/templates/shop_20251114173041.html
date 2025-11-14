{% extends "base.html" %}
{% block title %}Shop{% endblock %}

{% block content %}
<div style="display:flex; gap:1rem; padding:2rem;">

  <!-- Sidebar -->
  <aside id="sidebar" style="width:250px; position:sticky; top:2rem; border:1px solid #e9ecef; padding:1rem; border-radius:12px; background:#fff; height:max-content;">
    <h2 style="font-size:1.25rem; margin-bottom:1rem;">Filter Products</h2>
    
    <!-- Search -->
    <input type="text" id="searchInput" placeholder="Search name or category..." 
           style="width:100%; padding:.5rem; margin-bottom:1rem; border:1px solid #ced4da; border-radius:6px;">
    
    <!-- Price -->
    <label>Max Price: <span id="priceValue"></span></label>
    <input type="range" id="priceSlider" min="0" max="1000" step="1" value="1000" style="width:100%; margin-bottom:1rem;">
    
    <!-- Categories -->
    <div id="categoryFilters" style="margin-bottom:1rem;">
      <strong>Categories:</strong><br>
      <!-- dynamically filled -->
    </div>
  </aside>

  <!-- Product Grid -->
  <div id="productGrid" style="flex:1; display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:1rem;">
    <!-- Product cards inserted here by JS -->
  </div>

</div>

{% endblock %}

{% block scripts %}
<script>
// ---------- GLOBALS ----------
let allProducts = [];
let allCategories = [];

// ---------- FETCH PRODUCTS ----------
async function fetchProducts() {
  const res = await fetch('/api/products');
  allProducts = await res.json();
  renderCategories();
  renderProducts();
}

// ---------- RENDER CATEGORY CHECKBOXES ----------
function renderCategories() {
  const container = document.getElementById('categoryFilters');
  const categoryMap = {};
  allProducts.forEach(p => {
    if (p.category_id && !categoryMap[p.category_id]) {
      categoryMap[p.category_id] = p.category_name;
    }
  });
  allCategories = Object.entries(categoryMap); // [[id, name], ...]

  container.innerHTML = '<strong>Categories:</strong><br>';
  allCategories.forEach(([id,name]) => {
    const idSafe = `cat-${id}`;
    container.innerHTML += `
      <label style="display:block; margin-bottom:.25rem;">
        <input type="checkbox" value="${id}" class="categoryCheckbox" checked> ${name}
      </label>
    `;
  });
}

// ---------- RENDER PRODUCTS ----------
function renderProducts() {
  const grid = document.getElementById('productGrid');
  const searchQuery = document.getElementById('searchInput').value.toLowerCase();
  const maxPrice = parseFloat(document.getElementById('priceSlider').value);
  const checkedCategories = Array.from(document.querySelectorAll('.categoryCheckbox:checked'))
                                 .map(c => parseInt(c.value));

  grid.innerHTML = '';

  allProducts.forEach(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery) || 
                          (p.category_name && p.category_name.toLowerCase().includes(searchQuery));
    const matchesPrice = p.price <= maxPrice;
    const matchesCategory = checkedCategories.length === 0 || checkedCategories.includes(p.category_id);

    if (matchesSearch && matchesPrice && matchesCategory) {
      const img = p.image ? `<img src="/static/images/${p.image}" style="width:100%;height:180px;object-fit:cover;border-radius:8px;margin-bottom:.5rem;">` : '';
      grid.innerHTML += `
        <div style="border:1px solid #e9ecef; border-radius:12px; padding:1rem; background:#fff;">
          ${img}
          <h3 style="font-size:1rem; margin:0 0 .5rem;">${p.name}</h3>
          <p style="margin:0 0 .25rem; color:#555;">$${p.price.toFixed(2)}</p>
          <p style="margin:0 0 .25rem; font-size:0.85rem; color:#888;">${p.category_name || 'No category'}</p>
          <p style="margin:0; font-size:0.85rem;">Stock: ${p.stock}</p>
        </div>
      `;
    }
  });
}

// ---------- EVENT LISTENERS ----------
document.getElementById('searchInput').addEventListener('input', renderProducts);
document.getElementById('priceSlider').addEventListener('input', () => {
  document.getElementById('priceValue').textContent = '$' + document.getElementById('priceSlider').value;
  renderProducts();
});
document.addEventListener('change', e => {
  if (e.target.classList.contains('categoryCheckbox')) renderProducts();
});

// ---------- INIT ----------
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('priceValue').textContent = '$' + document.getElementById('priceSlider').value;
  fetchProducts();
});
</script>
{% endblock %}
