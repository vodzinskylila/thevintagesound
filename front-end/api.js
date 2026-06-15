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
function isAdmin() { const u = getUser(); return u && u.role === 'admin'; }

// ── Fetch autenticado ─────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API + path, { ...options, headers });
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

// ── API: Auth ────────────────────────────────────────────────────────────────
const Auth = {
  async login(email, password) {
    const { ok, data } = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    if (ok) {
      setSession(data.token, data.user);
    }
    return { ok, data };
  },
  async register(firstName, lastName, email, password, newsletter = false) {
    const { ok, data } = await apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ firstName, lastName, email, password, newsletter })
    });
    if (ok) {
      setSession(data.token, data.user);
    }
    return { ok, data };
  },
  async me() {
    return apiFetch('/auth/me');
  },
  async updateProfile(data) {
    return apiFetch('/auth/me', { method: 'PATCH', body: JSON.stringify(data) });
  },
  logout() {
    clearSession();
    window.location.href = 'index.html';
  }
};

// ── API: Products ─────────────────────────────────────────────────────────────
const Products = {
  async list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiFetch('/products' + (query ? '?' + query : ''));
  },
  async get(slugOrId) {
    return apiFetch('/products/' + slugOrId);
  },
  async genres() {
    return apiFetch('/products/genres');
  },
  async create(data) {
    return apiFetch('/products', { method: 'POST', body: JSON.stringify(data) });
  },
  async delete(id) {
    return apiFetch('/products/' + id, { method: 'DELETE' });
  }
};

// ── API: Cart ────────────────────────────────────────────────────────────────
const Cart = {
  async get() {
    return apiFetch('/cart');
  },
  async addItem(productId, quantity = 1) {
    return apiFetch('/cart/items', {
      method: 'POST',
      body: JSON.stringify({ productId, quantity })
    });
  },
  async updateItem(itemId, quantity) {
    return apiFetch('/cart/items/' + itemId, {
      method: 'PATCH',
      body: JSON.stringify({ quantity })
    });
  },
  async removeItem(itemId) {
    return apiFetch('/cart/items/' + itemId, { method: 'DELETE' });
  },
  async clear() {
    return apiFetch('/cart', { method: 'DELETE' });
  }
};

// ── API: Orders ──────────────────────────────────────────────────────────────
const Orders = {
  async create(shippingAddress, paymentMethod) {
    return apiFetch('/orders', {
      method: 'POST',
      body: JSON.stringify({ shippingAddress, paymentMethod })
    });
  },
  async myOrders() {
    return apiFetch('/orders/my');
  },
  async getOrder(orderId) {
    return apiFetch('/orders/my/' + orderId);
  },
  async all(status = '') {
    const query = status ? '?status=' + status : '';
    return apiFetch('/orders' + query);
  },
  async updateStatus(orderId, status, note = '') {
    return apiFetch('/orders/' + orderId + '/status', {
      method: 'PATCH',
      body: JSON.stringify({ status, note })
    });
  }
};

// ── API: Subscriptions ─────────────────────────────────────────────────────────
const Subscriptions = {
  async plans() {
    return apiFetch('/subscriptions/plans');
  },
  async subscribe(planId, paymentMethod) {
    return apiFetch('/subscriptions', {
      method: 'POST',
      body: JSON.stringify({ planId, paymentMethod })
    });
  },
  async mySubscription() {
    return apiFetch('/subscriptions/my');
  },
  async cancel(subId) {
    return apiFetch('/subscriptions/' + subId, { method: 'DELETE' });
  },
  async all(status = '') {
    const query = status ? '?status=' + status : '';
    return apiFetch('/subscriptions' + query);
  }
};

// ── Carrinho (contagem no ícone) ──────────────────────────────────────────────
async function updateCartBadge() {
  const badge = document.getElementById('cart-badge');
  if (!badge) return;
  if (!isLoggedIn()) { badge.textContent = '0'; return; }
  const { ok, data } = await Cart.get();
  if (ok) badge.textContent = data.data.itemCount || 0;
}

// ── Navbar: usuário logado vs. anônimo ────────────────────────────────────────
function updateNavUser() {
  const loginLink = document.getElementById('nav-login');
  const logoutBtn = document.getElementById('nav-logout');
  const userGreet = document.getElementById('nav-user-name');
  const user = getUser();
  if (user) {
    if (loginLink) loginLink.classList.add('hidden');
    if (logoutBtn) logoutBtn.classList.remove('hidden');
    if (userGreet) userGreet.textContent = user.firstName;
  } else {
    if (loginLink) loginLink.classList.remove('hidden');
    if (logoutBtn) logoutBtn.classList.add('hidden');
  }
}

function setupLogout() {
  const btn = document.getElementById('nav-logout');
  if (!btn) return;
  btn.addEventListener('click', () => Auth.logout());
}

// ── Toast de notificação ──────────────────────────────────────────────────────
function toast(msg, type = 'success') {
  const el = document.createElement('div');
  el.className = `fixed bottom-6 right-6 z-[9999] px-6 py-4 rounded-xl shadow-2xl text-white font-bold text-sm transition-all ${
    type === 'success' ? 'bg-green-600' : type === 'error' ? 'bg-red-600' : 'bg-blue-600'
  }`;
  el.style.cssText = 'animation: fadeInUp 0.3s ease-out; font-family: Plus Jakarta Sans, sans-serif;';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transition = 'opacity 0.3s';
    setTimeout(() => el.remove(), 300);
  }, 3500);
}

// Adicionar keyframes de animação
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }`;
  document.head.appendChild(style);
}

// ── Formatar preço ─────────────────────────────────────────────────────────────
function formatPrice(value) {
  return 'R$ ' + value.toFixed(2).replace('.', ',');
}

// ── Formatar data ─────────────────────────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ── Verificar auth (redirect) ────────────────────────────────────────────────
function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = 'login.html?redirect=' + encodeURIComponent(window.location.href);
    return false;
  }
  return true;
}

function requireAdmin() {
  if (!isAdmin()) {
    toast('Acesso restrito.', 'error');
    window.location.href = 'index.html';
    return false;
  }
  return true;
}

// ── Loading spinner ────────────────────────────────────────────────────────────
function showLoading(el) {
  el.innerHTML = '<div class="flex justify-center py-12"><div class="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div></div>';
}

function hideLoading(el) {
  el.innerHTML = '';
}