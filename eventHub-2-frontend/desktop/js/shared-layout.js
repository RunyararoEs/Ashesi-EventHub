// shared-layout.js — call buildLayout(pageId) at the top of every protected page

async function buildLayout(pageId) {
  requireAuth();

  const titles = {
    'nav-home':          { title: 'Home',             subtitle: 'Welcome back' },
    'nav-events':        { title: 'Events',           subtitle: 'Browse all events' },
    'nav-clubs':         { title: 'Clubs',            subtitle: 'Explore clubs on campus' },
    'nav-registrations': { title: 'My Registrations', subtitle: 'Events you have signed up for' },
    'nav-notifications': { title: 'Notifications',    subtitle: 'Stay up to date' },
    'nav-profile':       { title: 'My Profile',       subtitle: 'Your account details' },
    'nav-myclub':        { title: 'My Club',          subtitle: 'Manage your club' },
    'nav-sysadmin':      { title: 'System Admin',     subtitle: 'Manage the platform' },
  };

  const page = titles[pageId] || { title: 'EventHub', subtitle: '' };

  document.body.innerHTML = `
    <div id="toast"></div>
    <div class="app-shell">
      <aside class="sidebar">
        <a href="home.html" class="sidebar-logo">
          <div class="logo-icon">e</div>
          <span class="logo-text">EventHub</span>
        </a>

        <nav class="sidebar-nav">
          <a href="home.html" class="nav-item ${pageId === 'nav-home' ? 'active' : ''}">
            ${iconHome()} Home
          </a>
          <a href="events.html" class="nav-item ${pageId === 'nav-events' ? 'active' : ''}">
            ${iconCalendar()} Events
          </a>
          <a href="clubs.html" class="nav-item ${pageId === 'nav-clubs' ? 'active' : ''}">
            ${iconUsers()} Clubs
          </a>
          <a href="my-registrations.html" class="nav-item ${pageId === 'nav-registrations' ? 'active' : ''}">
            ${iconTicket()} My Registrations
          </a>

          <div class="nav-divider"></div>

          <a href="notifications.html" class="nav-item ${pageId === 'nav-notifications' ? 'active' : ''}">
            ${iconBell()}
            Notifications
            <span class="nav-badge hidden" id="notif-badge">0</span>
          </a>

          <div id="club-admin-nav" class="hidden">
            <div class="nav-divider"></div>
            <a href="my-club.html" class="nav-item ${pageId === 'nav-myclub' ? 'active' : ''}" style="color:var(--red);">
              ${iconClub()}
              My Club Dashboard
            </a>
          </div>

          <div id="sys-admin-nav" class="hidden">
            <div class="nav-divider"></div>
            <a href="system-admin.html" class="nav-item ${pageId === 'nav-sysadmin' ? 'active' : ''}" style="color:var(--red);">
              ${iconShield()}
              System Admin
            </a>
          </div>
        </nav>

        <div class="sidebar-bottom">
          <a href="profile.html" class="sidebar-user">
            <div class="sidebar-avatar" id="sidebar-avatar">?</div>
            <div class="sidebar-user-info">
              <div class="sidebar-username" id="sidebar-username">Loading...</div>
              <div class="sidebar-role" id="sidebar-role"></div>
            </div>
          </a>
          <div class="nav-divider"></div>
          <button class="nav-item" onclick="logout()" style="color:#dc2626;">
            ${iconLogout()} Sign Out
          </button>
        </div>
      </aside>

      <main class="main">
        <header class="topbar">
          <div class="topbar-left">
            <div class="topbar-title">${page.title}</div>
            <div class="topbar-subtitle" id="topbar-subtitle">${page.subtitle}</div>
          </div>
          <div class="topbar-right">
            <button class="icon-btn" onclick="window.location.href='notifications.html'" title="Notifications">
              ${iconBell()}
              <span class="notif-dot hidden" id="topbar-notif-dot"></span>
            </button>
          </div>
        </header>

        <div class="page-content" id="page-content">
          <div class="loading-center"><div class="spinner"></div></div>
        </div>
      </main>
    </div>
  ` + document.body.innerHTML;

  try {
    const me = await getMe();
    document.getElementById('sidebar-username').textContent = me.username;
    document.getElementById('sidebar-role').textContent     = me.role.replace('_', ' ');
    document.getElementById('sidebar-avatar').textContent   = me.username[0].toUpperCase();
    document.getElementById('topbar-subtitle').textContent  =
      pageId === 'nav-home' ? `Welcome back, ${me.username} 👋` : page.subtitle;
    window.__me = me;

    if (me.role === 'club_admin') {
      document.getElementById('club-admin-nav').classList.remove('hidden');
    }

    if (me.role === 'system_admin') {
      document.getElementById('sys-admin-nav').classList.remove('hidden');
    }
  } catch(_) {}

  try {
    const notifs = await getNotifications(true);
    const count  = notifs.results?.length ?? notifs.length ?? 0;
    if (count > 0) {
      const badge = document.getElementById('notif-badge');
      const dot   = document.getElementById('topbar-notif-dot');
      badge.textContent = count > 9 ? '9+' : count;
      badge.classList.remove('hidden');
      dot.classList.remove('hidden');
    }
  } catch(_) {}
}

function iconHome() {
  return `<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"/></svg>`;
}

function iconCalendar() {
  return `<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5"/></svg>`;
}

function iconUsers() {
  return `<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z"/></svg>`;
}

function iconTicket() {
  return `<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 6v.75m0 3v.75m0 3v.75m0 3V18m-9-5.25h5.25M7.5 15h3M3.375 5.25c-.621 0-1.125.504-1.125 1.125v3.026a2.999 2.999 0 0 1 0 5.198v3.026c0 .621.504 1.125 1.125 1.125h17.25c.621 0 1.125-.504 1.125-1.125v-3.026a2.999 2.999 0 0 1 0-5.198V6.375c0-.621-.504-1.125-1.125-1.125H3.375Z"/></svg>`;
}

function iconBell() {
  return `<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0"/></svg>`;
}

function iconClub() {
  return `<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M11.42 15.17 17.25 21A2.652 2.652 0 0 0 21 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 1 1-3.586-3.586l5.653-4.655m5.833-4.329c1.012-.833 2.5-1.302 4.062-.876a4.086 4.086 0 0 1 2.85 2.849c.425 1.562-.043 3.05-.876 4.063m-5.036-4.036-.177-.184c-.332-.329-.85-.427-1.285-.235L9.75 8.25"/></svg>`;
}

function iconShield() {
  return `<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"/></svg>`;
}

function iconLogout() {
  return `<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9"/></svg>`;
}

function showToast(msg, type = '') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className = 'show ' + type;
  setTimeout(() => { t.className = ''; }, 3200);
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)  return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const PALETTES = [
  ['#ffecd2','#fcb69f'],['#a1c4fd','#c2e9fb'],
  ['#d4fc79','#96e6a1'],['#fbc2eb','#a6c1ee'],
  ['#ffeaa7','#dfe6e9'],['#fd79a8','#e17055'],
];

function eventGradient(index) {
  const [a, b] = PALETTES[index % PALETTES.length];
  return `linear-gradient(135deg, ${a}, ${b})`;
}

function eventEmoji(title = '') {
  const t = title.toLowerCase();
  if (t.includes('music') || t.includes('concert') || t.includes('band')) return '🎵';
  if (t.includes('hack') || t.includes('tech') || t.includes('code'))     return '💻';
  if (t.includes('sport') || t.includes('run') || t.includes('game'))     return '⚽';
  if (t.includes('art') || t.includes('design') || t.includes('photo'))   return '🎨';
  if (t.includes('food') || t.includes('cook') || t.includes('dining'))   return '🍕';
  if (t.includes('talk') || t.includes('lecture') || t.includes('seminar')) return '🎤';
  return '📅';
}
