const API_BASE = 'http://127.0.0.1:8000';

let currentSearch = '';
let currentLimit = 5;
let currentMode = 'all';
let currentFilter = 'all';
let currentSort = 'accuracy';

async function fetchLeaderboard() {
    const res = await fetch(`${API_BASE}/leaderboard`);
    if (!res.ok) throw new Error('API error: ' + res.status);
    return await res.json();
}

function applyFilters(entries) {
    entries = entries.map(e => ({
        player: e.username,
        hits: e.hits,
        accuracy: parseFloat(e.accuracy),
        mode: (e.mode || '').toLowerCase(),
        timestamp: e.played_at,
        misses: e.misses,
    }));

    if (currentMode !== 'all') {
        entries = entries.filter(e => e.mode === currentMode);
    }

    if (currentSearch) {
        const q = currentSearch.toLowerCase();
        entries = entries.filter(e => e.player.toLowerCase().includes(q));
    }

    entries.sort((a, b) => b.accuracy - a.accuracy || b.hits - a.hits);

    return entries;
}

function rankClass(i) {
    if (i === 0) return 'rank-1';
    if (i === 1) return 'rank-2';
    if (i === 2) return 'rank-3';
    return '';
}

function badgeClass(i) {
    if (i === 0) return 'gold';
    if (i === 1) return 'silver';
    if (i === 2) return 'bronze';
    return 'normal';
}

function timeAgo(ts) {
    if (!ts) return '—';
    const date = new Date(ts);
    const diff = (Date.now() - date) / 1000;
    let ago;

    if (diff < 60) ago = 'just now';
    else if (diff < 3600) ago = `${Math.floor(diff / 60)}m ago`;
    else if (diff < 86400) ago = `${Math.floor(diff / 3600)}h ago`;
    else ago = `${Math.floor(diff / 86400)}d ago`;

    const dateStr = date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    return `${ago}<br><span style="font-size:0.65rem;opacity:0.6">${dateStr} ${timeStr}</span>`;
}

function isNew(ts) {
    return ts && (Date.now() - new Date(ts)) < 300000;
}

async function renderLeaderboard() {
    const body = document.getElementById('leaderboard-body');
    body.innerHTML = '<div class="empty-state"><div class="big">⊕</div><p>Loading...</p></div>';

    let entries;
    try {
        entries = await fetchLeaderboard();
    } catch (e) {
        body.innerHTML = `<div class="empty-state"><div class="big">⚠</div><p>Cannot reach API at ${API_BASE} — is the FastAPI server running?</p></div>`;
        return;
    }

    entries = applyFilters(entries);
    entries = entries.slice(0, currentLimit);

    if (entries.length === 0) {
        body.innerHTML = `<div class="empty-state"><div class="big">⊕</div><p>No entries found — play a game to submit a score!</p></div>`;
        return;
    }

    body.innerHTML = entries.map((e, i) => {
        const barWidth = Math.round(e.accuracy);
        const newEntry = isNew(e.timestamp);

        return `<div class="row ${rankClass(i)}" style="animation-delay:${i * 30}ms">
      <div><div class="rank-badge ${badgeClass(i)}">${i + 1}</div></div>
      <div class="player-name">
        ${e.player}
        ${e.mode ? `<span class="player-tag">${e.mode}</span>` : ''}
        ${newEntry ? '<span class="new-badge">NEW</span>' : ''}
      </div>
      <div class="score">${e.hits}</div>
      <div class="score">${e.misses}</div>
      <div class="accuracy-wrap">
        <span class="accuracy-val">${e.accuracy.toFixed(1)}%</span>
        <div class="accuracy-bar-bg"><div class="accuracy-bar-fill" style="width:${barWidth}%"></div></div>
      </div>
      <div class="col-date date-cell">${timeAgo(e.timestamp)}</div>
    </div>`;
    }).join('');
}

async function updateStats() {
    let entries;
    try {
        entries = await fetchLeaderboard();
    } catch {
        return;
    }

    entries = applyFilters(entries);
    document.getElementById('stat-total').textContent = entries.length;

    if (entries.length > 0) {
        const topAcc = Math.max(...entries.map(e => parseFloat(e.accuracy)));
        document.getElementById('stat-top').textContent = topAcc.toFixed(1) + '%';
        const avgAcc = entries.reduce((s, e) => s + parseFloat(e.accuracy), 0) / entries.length;
        document.getElementById('stat-avg').textContent = avgAcc.toFixed(1) + '%';
    } else {
        document.getElementById('stat-top').textContent = '—';
        document.getElementById('stat-avg').textContent = '—';
    }
}

function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3500);
}

document.querySelectorAll('[data-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        renderLeaderboard();
        updateStats();
    });
});

document.querySelectorAll('[data-limit]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('[data-limit]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentLimit = Number(btn.dataset.limit);
        renderLeaderboard();
    });
});

document.querySelectorAll('[data-mode]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('[data-mode]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentMode = btn.dataset.mode;
        renderLeaderboard();
        updateStats();
    });
});

document.querySelectorAll('[data-sort]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('[data-sort]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentSort = btn.dataset.sort;
        renderLeaderboard();
    });
});

let searchTimer;
document.getElementById('search-input').addEventListener('input', e => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        currentSearch = e.target.value.trim();
        renderLeaderboard();
    }, 200);
});

document.getElementById('api-toggle-btn').addEventListener('click', () => {
    const body = document.getElementById('api-body');
    const label = document.getElementById('api-toggle-label');
    body.classList.toggle('open');
    label.textContent = body.classList.contains('open') ? '[ hide ]' : '[ show ]';
});

renderLeaderboard();
updateStats();

setInterval(() => {
    document.getElementById('last-updated').textContent =
        'updated ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    renderLeaderboard();
}, 15000);