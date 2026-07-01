// Static, backend-free demo for the GitHub Pages landing page.
// Loads the same sample data the Flask app falls back on, and reimplements
// search/genre/sort/best-only filtering entirely client-side.

const searchInput = document.getElementById('search-input');
const genreSelect = document.getElementById('genre-select');
const sortSelect = document.getElementById('sort-select');
const bestOnly = document.getElementById('best-only');
const grid = document.getElementById('deal-grid');
const resultCount = document.getElementById('result-count');
const emptyState = document.getElementById('empty-state');
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');

const BEST_DEAL_THRESHOLD = 60;
let allDeals = [];

function money(n) {
  return n === 0 ? 'Free' : `$${n.toFixed(2)}`;
}

function cardHTML(deal) {
  const isBest = deal.discount_pct >= BEST_DEAL_THRESHOLD;
  const freeClass = deal.price === 0 ? ' price-free' : '';
  return `
    <article class="tag-card ${isBest ? 'is-best' : ''}">
      ${isBest ? '<span class="best-sticker">BEST DEAL</span>' : ''}
      <p class="tag-genre">${deal.genre} &middot; ${deal.store || 'Steam'}</p>
      <h2 class="tag-title">${deal.title}</h2>
      <div class="price-row${freeClass}">
        <span class="price-final">${money(deal.price)}</span>
        ${deal.original_price > deal.price ? `<span class="price-original">${money(deal.original_price)}</span>` : ''}
      </div>
      <div class="discount-row">
        ${deal.discount_pct > 0 ? `<span class="discount-pill">-${deal.discount_pct}%</span>` : ''}
      </div>
      <a class="tag-link" href="${deal.url}" target="_blank" rel="noopener">View &rarr;</a>
    </article>
  `;
}

function populateGenres(deals) {
  const genres = [...new Set(deals.map(d => d.genre))].sort();
  genres.forEach(g => {
    const opt = document.createElement('option');
    opt.value = g;
    opt.textContent = g;
    genreSelect.appendChild(opt);
  });
}

function render() {
  const search = searchInput.value.trim().toLowerCase();
  const genre = genreSelect.value;
  const sortBy = sortSelect.value;

  let filtered = allDeals.filter(d => {
    if (genre !== 'all' && d.genre !== genre) return false;
    if (bestOnly.checked && d.discount_pct < BEST_DEAL_THRESHOLD) return false;
    if (search && !d.title.toLowerCase().includes(search)) return false;
    return true;
  });

  const sorters = {
    discount_desc: (a, b) => b.discount_pct - a.discount_pct,
    price_asc: (a, b) => a.price - b.price,
    price_desc: (a, b) => b.price - a.price,
    alpha: (a, b) => a.title.localeCompare(b.title),
  };
  filtered.sort(sorters[sortBy] || sorters.discount_desc);

  // Cap the demo grid so the landing page doesn't turn into an infinite scroll
  const shown = filtered.slice(0, 24);

  grid.innerHTML = shown.map(cardHTML).join('');
  resultCount.textContent = `${filtered.length} deal${filtered.length === 1 ? '' : 's'} matched` +
    (filtered.length > shown.length ? ` — showing first ${shown.length}` : '');
  emptyState.hidden = filtered.length !== 0;
}

async function init() {
  try {
    const [steamRes, csRes] = await Promise.all([
      fetch('data/sample_deals.json'),
      fetch('data/sample_cheapshark_deals.json'),
    ]);
    const steam = await steamRes.json();
    const cs = await csRes.json();
    allDeals = [...steam, ...cs];
  } catch (err) {
    resultCount.textContent = 'Could not load sample data.';
    return;
  }

  populateGenres(allDeals);
  render();
}

searchInput.addEventListener('input', render);
genreSelect.addEventListener('change', render);
sortSelect.addEventListener('change', render);
bestOnly.addEventListener('change', render);

// ---------- Dark mode (mirrors static/script.js so both pages match) ----------
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

init();
