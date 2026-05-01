const ACCESS_KEY  = 'eh_access';
const REFRESH_KEY = 'eh_refresh';

function saveTokens(access, refresh) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

function getAccessToken()  { return localStorage.getItem(ACCESS_KEY); }
function getRefreshToken() { return localStorage.getItem(REFRESH_KEY); }

function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

function logout() {
  clearTokens();
  window.location.href = '/desktop/index.html';
}

// Call at the top of every protected page
function requireAuth() {
  if (!getAccessToken()) {
    window.location.href = '/desktop/index.html';
  }
}

// Redirect away from login/signup if already logged in
function redirectIfAuthed() {
  if (getAccessToken()) {
    window.location.href = '/desktop/home.html';
  }
}
