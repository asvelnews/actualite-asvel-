/* notifs.js — Cloche de notifications Actu ASVEL
   Panneau in-site (matchs à venir + dernières actus) et alertes du navigateur
   à l'heure du match via le service worker sw.js (même domaine).
   Rien d'externe : data.js, rss.xml et sw.js sont servis par le même site.
   Calqué sur site.js : IIFE stricte, helpers de stockage en try/catch.
   Chargé en defer APRÈS site.js (le header y est déjà construit). */
(function () {
  'use strict';

  function readStorage(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }
  function writeStorage(key, value) { try { localStorage.setItem(key, value); } catch (e) { /* stockage indisponible */ } }

  var inArticle = location.pathname.indexOf('/articles/') !== -1;
  var root = inArticle ? '../' : '';

  /* Membre connecté ? (même résolution que les pages interactives) */
  var currentUser = null;
  (function () {
    try {
      var norm = localStorage.getItem('asvel-session');
      if (!norm) return;
      var raw = localStorage.getItem('asvel-accounts');
      if (!raw) return;
      var arr = JSON.parse(raw);
      if (!Array.isArray(arr)) return;
      for (var i = 0; i < arr.length; i++) { if (arr[i].norm === norm) { currentUser = arr[i]; return; } }
    } catch (e) {}
  })();

  /* ---- Helpers matchs (mêmes règles de calcul qu'interactif.html) ---- */
  var months = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
  var days = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  function dateOfGame(g) { if (!g || !g[0]) return null; var d = new Date(g[0] + 'T12:00:00'); if (isNaN(d.getTime())) return null; return d; }
  function kickOfGame(g) {
    var base = dateOfGame(g); if (!base) return null;
    var hh = 0, mm = 0, t = /^(\d{1,2})h(\d{2})$/.exec(String(g[1]));
    if (t) { hh = +t[1]; mm = +t[2]; }
    var k = new Date(base); k.setHours(hh, mm, 0, 0); return k;
  }
  function compLabel(c) { if (c === 'euroleague') return 'EuroLeague'; if (c === 'belite') return 'Betclic ÉLITE'; if (c === 'derby') return 'Derby · Betclic ÉLITE'; return ''; }
  function gameTitle(g) { return g[3] === 'home' ? ('ASVEL – ' + g[2]) : (g[2] + ' – ASVEL'); }
  function kickTimeLabel(g) {
    var k = kickOfGame(g);
    if (k && /h\d{2}$/.test(String(g[1]))) return pad2(k.getHours()) + 'h' + pad2(k.getMinutes());
    return 'À venir';
  }
  function gameMeta(g, k) {
    var parts = [days[k.getDay()] + ' ' + k.getDate() + ' ' + months[k.getMonth()]];
    var t = kickTimeLabel(g);
    if (t !== 'À venir') parts.push(t);
    var c = compLabel(g[4]);
    if (c) parts.push(c);
    return parts.join(' · ');
  }
  function relDay(ms) {
    var d = Math.ceil(ms / 86400000);
    if (d <= 0) return 'Aujourd‘hui';
    if (d === 1) return 'Demain';
    return 'Dans ' + d + ' j';
  }
  function fmtDateFR(d) { return d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear(); }

  /* ---- Données matchs (source unique : data.js) ---- */
  var games = (typeof self.ASVEL_GAMES !== 'undefined' && Array.isArray(self.ASVEL_GAMES)) ? self.ASVEL_GAMES : [];
  function upcomingGames(limit) {
    var now = Date.now(), out = [];
    for (var i = 0; i < games.length; i++) {
      var k = kickOfGame(games[i]);
      if (k && k.getTime() > now) out.push({ g: games[i], kick: k.getTime() });
    }
    out.sort(function (a, b) { return a.kick - b.kick; });
    return out.slice(0, limit);
  }

  /* ---- État lu / non-lu (par entrée, localStorage) ---- */
  var READ_KEY = 'asvel-notifs-read';
  function readRead() { try { var r = JSON.parse(readStorage(READ_KEY) || '{}'); return (r && typeof r === 'object') ? r : {}; } catch (e) { return {}; } }
  function writeRead(o) { writeStorage(READ_KEY, JSON.stringify(o)); }

  var displayedIds = []; /* ids affichés dans le panneau → base du badge */

  function renderMatches(listEl) {
    var list = upcomingGames(3);
    if (!list.length) return;
    var read = readRead();
    var group = document.createElement('div');
    group.className = 'notifs-group';
    var h = document.createElement('h3');
    h.textContent = list.length === 1 ? 'Match à venir' : 'Matchs à venir';
    group.appendChild(h);
    list.forEach(function (item) {
      var id = 'm|' + item.g[0] + '|' + item.g[2];
      displayedIds.push(id);
      var k = new Date(item.kick);
      var a = document.createElement('a');
      a.className = 'notifs-item' + (read[id] ? '' : ' unread');
      a.href = root + 'matchs.html#calendrier';
      a.innerHTML = '<span class="notifs-dot" aria-hidden="true"></span>' +
        '<span class="notifs-text"><b>' + gameTitle(item.g) + '</b>' +
        '<span class="notifs-meta">' + gameMeta(item.g, k) + ' <em>' + relDay(item.kick - Date.now()) + '</em></span></span>';
      group.appendChild(a);
    });
    listEl.appendChild(group);
  }

  /* ---- Actus / mercato depuis rss.xml (date réelle, rien d'inventé) ---- */
  function parseRSS(txt) {
    var items = [];
    try {
      var doc = new DOMParser().parseFromString(txt, 'text/xml');
      var nodes = doc.querySelectorAll('item');
      for (var i = 0; i < nodes.length; i++) {
        var t = nodes[i].querySelector('title'), l = nodes[i].querySelector('link');
        var d = nodes[i].querySelector('pubDate'), c = nodes[i].querySelector('category');
        var title = t ? t.textContent.replace(/\s+/g, ' ').trim() : '';
        var link = l ? l.textContent.trim() : '';
        var dateV = d ? new Date(d.textContent.trim()) : null;
        if (!title || !link) continue;
        items.push({ title: title, link: link, date: dateV, category: c ? c.textContent.trim() : '', id: 'n|' + link });
      }
      items.sort(function (a, b) {
        var at = a.date ? a.date.getTime() : 0, bt = b.date ? b.date.getTime() : 0;
        return bt - at;
      });
      items = items.slice(0, 5);
    } catch (e) { items = []; }
    return items;
  }
  function renderNews(listEl, items) {
    if (!items.length) return;
    var read = readRead();
    var group = document.createElement('div');
    group.className = 'notifs-group';
    var h = document.createElement('h3');
    h.textContent = 'Actus & mercato';
    group.appendChild(h);
    items.forEach(function (item) {
      displayedIds.push(item.id);
      var a = document.createElement('a');
      a.className = 'notifs-item' + (read[item.id] ? '' : ' unread');
      a.href = item.link;
      a.innerHTML = '<span class="notifs-dot" aria-hidden="true"></span>' +
        '<span class="notifs-text"><b>' + item.title + '</b>' +
        '<span class="notifs-meta">' + (item.category ? item.category + ' · ' : '') + (item.date ? fmtDateFR(item.date) : '') + '</span></span>';
      group.appendChild(a);
    });
    listEl.appendChild(group);
  }
  function fetchRSS(cb) {
    var done = false, finish = function (items) { if (done) return; done = true; cb(items); };
    if (window.fetch) {
      fetch(root + 'rss.xml', { cache: 'no-store' })
        .then(function (r) { return r.text(); })
        .then(function (txt) { finish(parseRSS(txt)); })
        .catch(function () { finish([]); });
      return;
    }
    try {
      var xhr = new XMLHttpRequest();
      xhr.open('GET', root + 'rss.xml', true);
      xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
          if (xhr.status === 200 || xhr.status === 0) finish(parseRSS(xhr.responseText));
          else finish([]);
        }
      };
      xhr.onerror = function () { finish([]); };
      xhr.send();
    } catch (e) { finish([]); }
  }

  /* ---- Badge ---- */
  function updateBadge() {
    var read = readRead(), count = 0;
    for (var i = 0; i < displayedIds.length; i++) if (!read[displayedIds[i]]) count++;
    var badge = document.getElementById('notifsBadge');
    if (!badge) return;
    badge.textContent = count < 100 ? String(count) : '99+';
    badge.hidden = count === 0;
  }
  function markAllRead() {
    var read = readRead();
    for (var i = 0; i < displayedIds.length; i++) read[displayedIds[i]] = 1;
    writeRead(read);
    var panel = document.getElementById('notifsPanel');
    if (panel) {
      var items = panel.querySelectorAll('.notifs-item');
      for (var j = 0; j < items.length; j++) items[j].classList.remove('unread');
    }
    updateBadge();
  }

  /* ---- Alertes du navigateur : opt-in au clic, enregistrement SW silencieux ---- */
  function registerSW() {
    if (!currentUser) return; /* popups réservés aux membres */
    if (!('serviceWorker' in navigator)) return;
    try {
      navigator.serviceWorker.register(root + 'sw.js', { scope: root }).then(function (reg) {
        if (reg.active) reg.active.postMessage({ type: 'reschedule' });
        else reg.addEventListener('updatefound', function () {
          var w = reg.installing;
          if (!w) return;
          w.addEventListener('statechange', function () {
            if (w.state === 'activated') w.postMessage({ type: 'reschedule' });
          });
        });
      }).catch(function () { /* SW indisponible : la cloche reste fonctionnelle */ });
    } catch (e) {}
  }
  function optinStatus() {
    var st = document.getElementById('notifsStatus'), note = document.getElementById('notifsNote');
    var en = document.getElementById('notifsEnable');
    var show = function (msg, hideNote, hideBtn) {
      if (st) st.textContent = msg;
      if (note) note.hidden = !!hideNote;
      if (en) en.hidden = !!hideBtn;
    };
    if (!currentUser) { show('', false, false); return; } /* visiteur : le CTA vers compte.html reste visible */
    if (!('Notification' in window)) { show('Non pris en charge par ce navigateur.', true, true); return; }
    var p = Notification.permission;
    if (p === 'granted') { show('Alertes activées ✓ — popup à l‘heure du match.', true, true); }
    else if (p === 'denied') { show('Alertes bloquées — autorisez-les dans les réglages du navigateur.', true, true); }
    else { show('', false, false); }
  }
  function requestOptin() {
    if (!currentUser) return;
    if (!('Notification' in window)) return;
    var done = function () { optinStatus(); registerSW(); };
    try {
      var p = Notification.requestPermission(function () { done(); });
      if (p && p.then) p.then(function () { done(); });
    } catch (e) {}
  }

  /* ---- Panneau ---- */
  function buildPanel() {
    var panel = document.createElement('section');
    panel.id = 'notifsPanel';
    panel.className = 'notifs-panel';
    panel.setAttribute('aria-label', 'Notifications');
    panel.setAttribute('aria-hidden', 'true');
    panel.hidden = true;
    panel.innerHTML =
      '<div class="notifs-head"><h2>Notifications</h2>' +
      '<button type="button" id="notifsMarkAll" class="notifs-mark">Tout marquer comme lu</button></div>' +
      '<div class="notifs-list" id="notifsList"></div>' +
      '<div class="notifs-optin">' +
      '<p class="notifs-optin-title">⚡ Alertes du navigateur</p>' +
      '<p class="notifs-optin-note" id="notifsNote">' + (currentUser
        ? 'Recevez un popup à l‘heure du match. Sans serveur externe, la notification ne s‘affiche que tant qu‘une page du site est ouverte.'
        : 'Les popups à l‘heure du match sont réservés aux membres. Le panneau ci-dessus reste ouvert à tous.') + '</p>' +
      (currentUser
        ? '<button type="button" id="notifsEnable" class="notifs-enable">Activer les alertes</button>'
        : '<a class="notifs-enable" href="' + root + 'compte.html">Créer un compte / Me connecter</a>') +
      '<p class="notifs-optin-status" id="notifsStatus"></p></div>';
    document.body.appendChild(panel);
    var mark = document.getElementById('notifsMarkAll');
    if (mark) mark.addEventListener('click', markAllRead);
    var en = document.getElementById('notifsEnable');
    if (en) en.addEventListener('click', requestOptin);
    var list = document.getElementById('notifsList');
    renderMatches(list);
    fetchRSS(function (items) { renderNews(list, items); updateBadge(); });
  }

  /* ---- Cloche + ouverture/fermeture ---- */
  var bell = null, panel = null, open = false;
  function setPanel(openState) {
    open = openState;
    if (panel) { panel.hidden = !open; panel.setAttribute('aria-hidden', String(!open)); }
    if (bell) bell.setAttribute('aria-expanded', String(open));
  }
  function toggle() {
    pick();
    setPanel(!open);
  }
  function init() {
    var header = document.querySelector('body > header, .site-header');
    if (!header) return; /* pas de header : la cloche n'a pas de place */
    var themeBtn = document.getElementById('themeToggle');
    bell = document.createElement('button');
    bell.type = 'button';
    bell.id = 'notifsBell';
    bell.className = 'notifs-bell';
    bell.setAttribute('aria-label', 'Notifications');
    bell.setAttribute('aria-haspopup', 'true');
    bell.setAttribute('aria-expanded', 'false');
    bell.innerHTML = '<span class="notifs-ico" aria-hidden="true">🔔</span><span class="notifs-badge" id="notifsBadge" hidden></span>';
    header.insertBefore(bell, themeBtn || header.lastChild);
    bell.addEventListener('click', function (e) { e.stopPropagation(); toggle(); });
    panel = buildPanel();
    panel.addEventListener('click', function (e) { e.stopPropagation(); });
    document.addEventListener('click', function (e) {
      if (open && !panel.contains(e.target) && bell.contains(e.target) === false) setPanel(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && open) setPanel(false);
    });
    optinStatus();
    registerSW();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();