// ---------- Element refs ----------
const searchInput = document.getElementById('search-input');
const genreSelect = document.getElementById('genre-select');
const storeSelect = document.getElementById('store-select');
const sortSelect = document.getElementById('sort-select');
const priceRange = document.getElementById('price-range');
const priceValue = document.getElementById('price-value');
const bestOnly = document.getElementById('best-only');
const grid = document.getElementById('deal-grid');
const resultCount = document.getElementById('result-count');
const emptyState = document.getElementById('empty-state');
const pagination = document.getElementById('pagination');
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');
const toast = document.getElementById('toast');

const tabButtons = document.querySelectorAll('.tab-btn');
const viewDeals = document.getElementById('view-deals');
const viewWatchlist = document.getElementById('view-watchlist');
const watchlistGrid = document.getElementById('watchlist-grid');
const watchlistEmpty = document.getElementById('watchlist-empty');
const watchCount = document.getElementById('watch-count');

const watchDialog = document.getElementById('watch-dialog');
const watchForm = document.getElementById('watch-form');
const watchDialogTitle = document.getElementById('watch-dialog-title');
const targetPriceInput = document.getElementById('target-price-input');
const watchCancel = document.getElementById('watch-cancel');

let currentPage = 1;
let pendingWatchDeal = null;
const historyCache = {};

// ---------- Helpers ----------
function money(n) {
  return n === 0 ? 'Free' : `$${n.toFixed(2)}`;
}

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  toast.classList.add('is-visible');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => {
    toast.classList.remove('is-visible');
    setTimeout(() => { toast.hidden = true; }, 200);
  }, 2200);
}

function skeletonHTML(count) {
  return Array.from({ length: count }, () => `
    <div class="tag-card skeleton-card">
      <div class="skel skel-line skel-w60"></div>
      <div class="skel skel-line skel-w90"></div>
      <div class="skel skel-line skel-w40"></div>
    </div>
  `).join('');
}

// ---------- Sparkline (tiny inline SVG, no library) ----------
function sparklineSVG(history) {
  if (!history || history.length < 2) {
    return '<p class="history-empty">Not enough history yet — check back after another scrape.</p>';
  }
  const prices = history.map(h => h.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const w = 220, h = 50, pad = 4;
  const range = (max - min) || 1;

  const points = prices.map((p, i) => {
    const x = pad + (i / (prices.length - 1)) * (w - pad * 2);
    const y = h - pad - ((p - min) / range) * (h - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  return `
    <svg class="sparkline" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
      <polyline points="${points}" fill="none" stroke="currentColor" stroke-width="2" />
    </svg>
    <div class="history-range"><span>${money(min)}</span><span>${money(max)}</span></div>
  `;
}

// ---------- Deal cards ----------
function cardHTML(deal) {
  const bestBadge = deal.is_best_deal ? '<span class="best-sticker">BEST DEAL</span>' : '';
  const freeClass = deal.price === 0 ? ' price-free' : '';
  const key = `${deal.appid}::${deal.store}`;

  return `
    <article class="tag-card ${deal.is_best_deal ? 'is-best' : ''}" data-appid="${deal.appid}" data-store="${deal.store}">
      ${bestBadge}
      <p class="tag-genre">${deal.genre} &middot; ${deal.store}</p>
      <h2 class="tag-title">${deal.title}</h2>
      <div class="price-row${freeClass}">
        <span class="price-final">${money(deal.price)}</span>
        ${deal.original_price > deal.price ? `<span class="price-original">${money(deal.original_price)}</span>` : ''}
      </div>
      <div class="discount-row">
        ${deal.discount_pct > 0 ? `<span class="discount-pill">-${deal.discount_pct}%</span>` : ''}
      </div>

      <div class="card-actions">
        <a class="tag-link" href="${deal.url}" target="_blank" rel="noopener">View &rarr;</a>
        <button class="icon-btn watch-btn" data-appid="${deal.appid}" data-store="${deal.store}" data-title="${deal.title.replace(/"/g, '&quot;')}" title="Watch for price drops">&#9733; Watch</button>
        <button class="icon-btn share-btn" data-url="${deal.url}" title="Copy link">&#128279;</button>
        <button class="icon-btn history-btn" data-key="${key}" title="Price history">&#8593;&#8595;</button>
      </div>

      <div class="history-panel" id="history-${key.replace(/[^a-zA-Z0-9]/g, '_')}" hidden></div>
    </article>
  `;
}

function watchCardHTML(w) {
  const met = w.alert_met;
  return `
    <article class="tag-card ${met ? 'is-best' : ''}">
      ${met ? '<span class="best-sticker">TARGET HIT</span>' : ''}
      <p class="tag-genre">Watching &middot; ${w.store}</p>
      <h2 class="tag-title">${w.title}</h2>
      <div class="price-row">
        <span class="price-final">${w.current_price !== null ? money(w.current_price) : '—'}</span>
        <span class="price-original">target ${money(w.target_price)}</span>
      </div>
      <div class="card-actions">
        <button class="icon-btn remove-watch-btn" data-id="${w.id}">Remove</button>
      </div>
    </article>
  `;
}

// ---------- Fetch + render deals ----------
async function loadDeals(page = 1) {
  currentPage = page;
  grid.innerHTML = skeletonHTML(6);
  emptyState.hidden = true;
  pagination.innerHTML = '';

  const params = new URLSearchParams({
    genre: genreSelect.value,
    store: storeSelect.value,
    max_price: priceRange.value,
    best_only: bestOnly.checked ? '1' : '0',
    q: searchInput.value,
    sort: sortSelect.value,
    page: String(page),
    per_page: '12',
  });

  let data;
  try {
    const res = await fetch(`/api/deals?${params.toString()}`);
    data = await res.json();
  } catch (err) {
    grid.innerHTML = '';
    resultCount.textContent = 'Could not reach the server.';
    return;
  }

  grid.innerHTML = data.results.map(cardHTML).join('');
  resultCount.textContent = `${data.total} deal${data.total === 1 ? '' : 's'} found — page ${data.page} of ${data.total_pages}`;
  emptyState.hidden = data.results.length !== 0;
  renderPagination(data.page, data.total_pages);
}

function renderPagination(page, totalPages) {
  if (totalPages <= 1) { pagination.innerHTML = ''; return; }
  pagination.innerHTML = `
    <button class="page-btn" id="prev-page" ${page <= 1 ? 'disabled' : ''}>&larr; Prev</button>
    <span class="page-status">${page} / ${totalPages}</span>
    <button class="page-btn" id="next-page" ${page >= totalPages ? 'disabled' : ''}>Next &rarr;</button>
  `;
  document.getElementById('prev-page')?.addEventListener('click', () => loadDeals(page - 1));
  document.getElementById('next-page')?.addEventListener('click', () => loadDeals(page + 1));
}

// ---------- Watchlist ----------
async function loadWatchlist() {
  watchlistGrid.innerHTML = skeletonHTML(3);
  let watches;
  try {
    const res = await fetch('/api/watchlist');
    watches = await res.json();
  } catch (err) {
    watchlistGrid.innerHTML = '';
    return;
  }

  watchCount.textContent = watches.length ? `(${watches.length})` : '';
  watchlistGrid.innerHTML = watches.map(watchCardHTML).join('');
  watchlistEmpty.hidden = watches.length !== 0;
}

async function addWatch(appid, store, title, targetPrice) {
  const res = await fetch('/api/watchlist', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ appid, store, title, target_price: targetPrice }),
  });
  if (res.ok) {
    showToast(`Watching ${title} for $${targetPrice.toFixed(2)} or less`);
    loadWatchlist();
  } else {
    showToast('Could not add to watchlist.');
  }
}

async function removeWatch(id) {
  await fetch(`/api/watchlist/${id}`, { method: 'DELETE' });
  loadWatchlist();
}

// ---------- Event delegation for cards (watch / share / history) ----------
document.addEventListener('click', async (e) => {
  const watchBtn = e.target.closest('.watch-btn');
  if (watchBtn) {
    pendingWatchDeal = {
      appid: watchBtn.dataset.appid,
      store: watchBtn.dataset.store,
      title: watchBtn.dataset.title,
    };
    watchDialogTitle.textContent = pendingWatchDeal.title;
    targetPriceInput.value = '';
    watchDialog.showModal();
    return;
  }

  const shareBtn = e.target.closest('.share-btn');
  if (shareBtn) {
    try {
      await navigator.clipboard.writeText(shareBtn.dataset.url);
      showToast('Link copied to clipboard');
    } catch (err) {
      showToast('Could not copy link');
    }
    return;
  }

  const historyBtn = e.target.closest('.history-btn');
  if (historyBtn) {
    const key = historyBtn.dataset.key;
    const panelId = `history-${key.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const panel = document.getElementById(panelId);
    if (!panel) return;

    if (!panel.hidden) { panel.hidden = true; return; }

    panel.hidden = false;
    panel.innerHTML = '<p class="history-empty">Loading...</p>';

    const [appid, store] = key.split('::');
    if (!historyCache[key]) {
      const res = await fetch(`/api/deals/${appid}/history?store=${encodeURIComponent(store)}`);
      historyCache[key] = await res.json();
    }
    panel.innerHTML = sparklineSVG(historyCache[key]);
    return;
  }

  const removeBtn = e.target.closest('.remove-watch-btn');
  if (removeBtn) {
    removeWatch(removeBtn.dataset.id);
    return;
  }
});

watchCancel.addEventListener('click', () => watchDialog.close());

watchForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const target = parseFloat(targetPriceInput.value);
  if (pendingWatchDeal && !Number.isNaN(target)) {
    addWatch(pendingWatchDeal.appid, pendingWatchDeal.store, pendingWatchDeal.title, target);
  }
  watchDialog.close();
});

// ---------- Tabs ----------
tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    tabButtons.forEach(b => b.classList.remove('is-active'));
    btn.classList.add('is-active');
    const view = btn.dataset.view;
    viewDeals.hidden = view !== 'deals';
    viewWatchlist.hidden = view !== 'watchlist';
    if (view === 'watchlist') loadWatchlist();
  });
});

// ---------- Filters ----------
let searchDebounce;
searchInput.addEventListener('input', () => {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => loadDeals(1), 300);
});

[genreSelect, storeSelect, sortSelect].forEach(el => {
  el.addEventListener('change', () => loadDeals(1));
});
bestOnly.addEventListener('change', () => loadDeals(1));

priceValue.textContent = `$${priceRange.value}`;
priceRange.addEventListener('input', () => {
  priceValue.textContent = `$${priceRange.value}`;
});
priceRange.addEventListener('change', () => loadDeals(1));

// ---------- Dark mode ----------
function applyTheme(theme) {
  document.body.classList.toggle('dark', theme === 'dark');
  themeIcon.textContent = theme === 'dark' ? '☀' : '☾';
}

const savedTheme = localStorage.getItem('theme') ||
  (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
applyTheme(savedTheme);

themeToggle.addEventListener('click', () => {
  const next = document.body.classList.contains('dark') ? 'light' : 'dark';
  localStorage.setItem('theme', next);
  applyTheme(next);
});

// ---------- Init ----------
loadDeals(1);
