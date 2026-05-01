const BASE_URL = 'https://ashesi-eventhub-4604.onrender.com/api';

async function apiFetch(path, options = {}) {
  const token = getAccessToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  // Token expired — try refresh
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (!refreshed) { logout(); return; }

    const retryRes = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: {
        ...headers,
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });
    return handleResponse(retryRes);
  }

  return handleResponse(res);
}

async function handleResponse(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, data };
  return data;
}

async function tryRefresh() {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    saveTokens(data.access, refresh);
    return true;
  } catch {
    return false;
  }
}

// ── Auth ──────────────────────────────────────────
function login(email, password) {
  return apiFetch('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

function register(payload) {
  return apiFetch('/users/register/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── User ──────────────────────────────────────────
function getMe()           { return apiFetch('/users/me/'); }
function updateMe(payload) {
  return apiFetch('/users/me/', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

// ── System Admin: Users ───────────────────────────
function getAllUsers() { return apiFetch('/users/all/'); }

// ── System Admin: Clubs ───────────────────────────
function createClub(payload) {
  return apiFetch('/clubs/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── System Admin: Assign Club Admin ───────────────
function assignClubAdmin(payload) {
  return apiFetch('/users/assign-club-admin/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── System Admin: Transfer Requests ───────────────
function getTransferRequests(status = 'pending') {
  return apiFetch(`/users/transfer-request/list/?status=${status}`);
}

function approveTransferRequest(id) {
  return apiFetch(`/users/transfer-request/${id}/approve/`, { method: 'PATCH' });
}

function rejectTransferRequest(id) {
  return apiFetch(`/users/transfer-request/${id}/reject/`, { method: 'PATCH' });
}

// ── Clubs ─────────────────────────────────────────
function getClubs()    { return apiFetch('/clubs/'); }
function getClub(slug) { return apiFetch(`/clubs/${slug}/`); }

// ── Events ────────────────────────────────────────
function getEvents(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/events/${qs ? '?' + qs : ''}`);
}

function getEvent(id)         { return apiFetch(`/events/${id}/`); }

function registerForEvent(id) {
  return apiFetch(`/events/${id}/register/`, { method: 'POST' });
}

function cancelRegistration(id) {
  return apiFetch(`/events/${id}/register/`, { method: 'DELETE' });
}

function getMyRegistrations() { return apiFetch('/events/my-registrations/'); }

function cloneEvent(id, payload = {}) {
  return apiFetch(`/events/${id}/clone/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── Notifications ─────────────────────────────────
function getNotifications(unreadOnly = false) {
  return apiFetch(`/notifications/${unreadOnly ? '?unread=true' : ''}`);
}

function markNotificationRead(id) {
  return apiFetch(`/notifications/${id}/read/`, { method: 'PATCH' });
}

function markAllNotificationsRead() {
  return apiFetch('/notifications/mark-all-read/', { method: 'POST' });
}
