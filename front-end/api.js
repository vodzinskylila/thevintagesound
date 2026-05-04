// api.js — módulo compartilhado entre todas as páginas
const API = 'http://localhost:3000/api';

// ── Helpers de token ──────────────────────────────────────────────────────────
function getToken() { return localStorage.getItem('tvs_token'); }
function getUser()  { const u = localStorage.getItem('tvs_user'); return u ? JSON.parse(u) : null; }
function setSession(token, user) {
  localStorage.setItem('tvs_token', token);
  localStorage.setItem('tvs_user', JSON.stringify(user));
}
function clearSession() {
  localStorage.removeItem('tvs_token');
  localStorage.removeItem('tvs_user');
}
function isLoggedIn() { return !!getToken(); }

// ── Fetch autenticado ─────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API + path, { ...options, headers });
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

// ── Carrinho (contagem no ícone) ──────────────────────────────────────────────
async function updateCartBadge() {
  const badge = document.getElementById('cart-badge');
  if (!badge) return;
  if (!isLoggedIn()) { badge.textContent = '0'; return; }
  const { ok, data } = await apiFetch('/cart');
  if (ok) badge.textContent = data.data.itemCount || 0;
}

// ── Navbar: usuário logado vs. anônimo ────────────────────────────────────────
function updateNavUser() {
  const loginLink  = document.getElementById('nav-login');
  const logoutBtn  = document.getElementById('nav-logout');
  const userGreet  = document.getElementById('nav-user-name');
  const user = getUser();
  if (user) {
    if (loginLink)  loginLink.classList.add('hidden');
    if (logoutBtn)  logoutBtn.classList.remove('hidden');
    if (userGreet)  userGreet.textContent = user.firstName;
  } else {
    if (loginLink)  loginLink.classList.remove('hidden');
    if (logoutBtn)  logoutBtn.classList.add('hidden');
  }
}

function setupLogout() {
  const btn = document.getElementById('nav-logout');
  if (!btn) return;
  btn.addEventListener('click', () => {
    clearSession();
    window.location.href = 'index.html';
  });
}

// Toast de notificação
function toast(msg, type = 'success') {
  const el = document.createElement('div');
  el.className = `fixed bottom-6 right-6 z-[9999] px-6 py-4 rounded-xl shadow-2xl text-white font-bold text-sm transition-all
    ${type === 'success' ? 'bg-green-600' : 'bg-red-600'}`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}
