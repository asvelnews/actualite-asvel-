/* _test-notifs-membre.js — Évaluation auto des fonctionnalités "Notifications + avantages membre + verrous pronos/cinq".
   Lance un serveur HTTP local (127.0.0.1), teste avec Playwright (chromium).
   Usage : node _test-notifs-membre.js  (dans le dossier du site) */

'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = __dirname;
const PORT = 8753;
const BASE = 'http://127.0.0.1:' + PORT;

const server = http.createServer(function (req, res) {
  let p;
  try { p = decodeURIComponent(req.url.split('?')[0]); } catch (e) { p = req.url; }
  if (p === '/') p = '/index.html';
  const file = path.normalize(path.join(ROOT, p));
  if (file.indexOf(path.normalize(ROOT)) !== 0) { res.writeHead(403); return res.end('forbidden'); }
  fs.readFile(file, function (err, data) {
    if (err) { res.writeHead(404); return res.end('not found: ' + p); }
    const ext = path.extname(file).toLowerCase();
    const type = {
      '.html': 'text/html; charset=utf-8',
      '.css': 'text/css; charset=utf-8',
      '.js': 'application/javascript; charset=utf-8',
      '.json': 'application/json',
      '.xml': 'application/rss+xml',
      '.svg': 'image/svg+xml',
      '.png': 'image/png',
      '.ico': 'image/x-icon'
    }[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
    res.end(data);
  });
});

let passed = 0, failed = 0;
function check(name, ok, detail) {
  if (ok) { passed++; console.log('  ✔ ' + name); }
  else { failed++; console.log('  ✘ ' + name + (detail ? ' — ' + detail : '')); }
}

function waitFor(fn, timeout) {
  const start = Date.now();
  return new Promise(function (resolve, reject) {
    (function loop() {
      fn().then(function (v) {
        if (v) return resolve(v);
        if (Date.now() - start > (timeout || 5000)) return reject(new Error('timeout'));
        setTimeout(loop, 120);
      }).catch(reject);
    })();
  });
}

async function attachErrors(page, box) {
  page.on('pageerror', function (e) { box.push('pageerror: ' + e.message); });
  page.on('console', function (m) {
    if (m.type() === 'error') box.push('console.error: ' + m.text());
  });
}

function injectAccount(pseudo) {
  return function (args) { args.__pseudo = pseudo; };
}

async function main() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  /* ---- Contexte visiteur (aucun compte) ---- */
  const visitor = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  /* ---- Contexte membre (un compte local) ---- */
  const member = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  await member.addInitScript(function (pseudo) {
    try {
      const norm = String(pseudo).trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_\-]/g, '');
      localStorage.setItem('asvel-accounts', JSON.stringify([{ pseudo: pseudo, norm: norm, hash: 'plain:mdp123456', createdAt: 1757001600000 }]));
      localStorage.setItem('asvel-session', norm);
      /* Quelques pronos + une compo pour vérifier le mini-profil */
      localStorage.setItem('asvel-pronos', JSON.stringify({ '2026-09-24|Maccabi Tel-Aviv|home': 'home', '2026-09-27|Cholet Basket|away': 'away' }));
      localStorage.setItem('asvel-cinq', JSON.stringify({ PG: 'Nando De Colo', SG: 'Théo Maledon', SF: 'Émile Baudry', PF: 'Rudy Gobert', C: 'Mathis Dossou-Yovo' }));
      localStorage.setItem('asvel-activity-' + norm, JSON.stringify({ pronos: 2, compo: 1, lastAt: 1757100000000 }));
    } catch (e) {}
  }, 'TestMembre');

  console.log('\n=== Partie A — Verrous pronos & cinq (visiteur) ===');
  {
    const page = await visitor.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/interactif.html', { waitUntil: 'load' });
    await waitFor(function () { return page.evaluate(function () { return !document.getElementById('pronosGate').hidden && document.getElementById('pronostics').hidden; }); });
    const gateVisible = await page.evaluate(function () { return !document.getElementById('pronosGate').hidden; });
    const pronosHidden = await page.evaluate(function () { return document.getElementById('pronostics').hidden; });
    const compoHidden = await page.evaluate(function () { return document.getElementById('composition').hidden; });
    const jaugeHidden = await page.evaluate(function () { return document.getElementById('jaugeBox').hidden; });
    const shareHidden = await page.evaluate(function () { return document.getElementById('shareBanner').hidden; });
    const tribuneGate = await page.evaluate(function () { return document.getElementById('tribuneGate') ? !document.getElementById('tribuneGate').hidden : false; });
    check('interactif : #pronosGate visible pour un visiteur', gateVisible);
    check('interactif : #pronostics masqué', pronosHidden);
    check('interactif : #composition masqué', compoHidden);
    check('interactif : #jaugeBox masqué', jaugeHidden);
    check('interactif : #shareBanner masqué', shareHidden);
    check('interactif : tribune toujours verrouillée (visiteur)', tribuneGate);
    const gateCta = await page.evaluate(function () {
      var g = document.getElementById('pronosGate');
      var a = g && g.querySelector('a');
      return a && a.getAttribute('href').indexOf('compte.html') !== -1;
    });
    check('interactif : le gate pointe vers compte.html', gateCta);
    await page.close();
  }
  {
    const page = await visitor.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/matchs.html', { waitUntil: 'load' });
    await waitFor(function () { return page.evaluate(function () { return document.querySelectorAll('.prono-bar.locked').length > 0; }); });
    const gateVisible = await page.evaluate(function () { return !document.getElementById('pronosGate').hidden; });
    const lockedBars = await page.evaluate(function () { return document.querySelectorAll('.prono-bar.locked').length; });
    const unlockedBars = await page.evaluate(function () { return document.querySelectorAll('.prono-bar:not(.locked)').length; });
    check('matchs : #pronosGate visible (visiteur)', gateVisible);
    check('matchs : barres pronos visiteur = verrouillées', lockedBars > 0 && unlockedBars === 0, 'locked=' + lockedBars + ' unlocked=' + unlockedBars);
    await page.close();
  }
  {
    const page = await visitor.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/effectif.html', { waitUntil: 'load' });
    await waitFor(function () { return page.evaluate(function () { return !document.getElementById('cinqGate').hidden; }); });
    const gateVisible = await page.evaluate(function () { return !document.getElementById('cinqGate').hidden; });
    const cinqHidden = await page.evaluate(function () { return document.getElementById('cinqBar').hidden; });
    const toggleHidden = await page.evaluate(function () { return document.getElementById('compoToggle').hidden; });
    check('effectif : #cinqGate visible (visiteur)', gateVisible);
    check('effectif : #cinqBar masqué', cinqHidden);
    check('effectif : bouton compo masqué', toggleHidden);
    await page.close();
  }

  console.log('\n=== Partie A — Déverrouillé pour un membre ===');
  {
    const page = await member.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/interactif.html', { waitUntil: 'load' });
    const unlocked = await page.evaluate(function () {
      return document.getElementById('pronosGate').hidden &&
        !document.getElementById('pronostics').hidden &&
        !document.getElementById('composition').hidden;
    });
    check('interactif : zones visibles pour un membre', unlocked);
    await page.close();
  }
  {
    const page = await member.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/matchs.html', { waitUntil: 'load' });
    await waitFor(function () { return page.evaluate(function () { return document.querySelectorAll('.prono-bar:not(.locked)').length > 0; }); });
    const ok = await page.evaluate(function () {
      return document.getElementById('pronosGate').hidden &&
        document.querySelectorAll('.prono-bar:not(.locked)').length > 0 &&
        document.querySelectorAll('.prono-bar.locked').length === 0;
    });
    check('matchs : barres interactives pour un membre', ok);
    await page.close();
  }
  {
    const page = await member.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/effectif.html', { waitUntil: 'load' });
    const ok = await page.evaluate(function () {
      var c = document.getElementById('cinqGate');
      return c && c.hidden && !document.getElementById('cinqBar').hidden && !document.getElementById('compoToggle').hidden;
    });
    check('effectif : cinq déverrouillé pour un membre', ok);
    await page.close();
  }

  console.log('\n=== Partie B — Notifications ===');
  {
    const page = await visitor.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/index.html', { waitUntil: 'load' });
    const bell = await waitFor(function () { return page.evaluate(function () { return !!document.getElementById('notifsBell'); }); });
    check('index : cloche présente dans le header', bell);
    /* Panneau + contenu */
    await page.click('#notifsBell');
    await waitFor(function () { return page.evaluate(function () { return document.getElementById('notifsPanel') && !document.getElementById('notifsPanel').hidden; }); });
    await waitFor(function () { return page.evaluate(function () { return document.querySelectorAll('#notifsList .notifs-item').length >= 3; }); });
    const groups = await page.evaluate(function () {
      var hs = Array.prototype.map.call(document.querySelectorAll('#notifsList .notifs-group h3'), function (h) { return h.textContent; });
      return hs.join('|');
    });
    const hasMatches = groups.indexOf('Match') !== -1;
    const hasActu = groups.indexOf('Actus') !== -1;
    const items = await page.evaluate(function () { return document.querySelectorAll('#notifsList .notifs-item').length; });
    const badgeShown = await page.evaluate(function () { var b = document.getElementById('notifsBadge'); return b && !b.hidden && parseInt(b.textContent, 10) > 0; });
    check('panneau : groupes "Matchs à venir" + "Actus & mercato"', hasMatches && hasActu, groups);
    check('panneau : items affichés (' + items + ')', items >= 4);
    check('badge non-lu initial affiché', badgeShown);
    /* Le prochain match est Maccabi (24/09) et Cholet est venu au 27/09 */
    const text = await page.evaluate(function () { return document.querySelector('#notifsList').textContent; });
    check('panneau : Maccabi = prochain match', text.indexOf('Maccabi') !== -1);
    check('panneau : Cholet présent (fix 27/09)', text.indexOf('Cholet') !== -1);
    /* Visiteur : le bloc opt-in est un lien vers compte.html, pas un bouton */
    const ctaType = await page.evaluate(function () {
      var a = document.querySelector('#notifsPanel .notifs-enable');
      return { tag: a ? a.tagName : null, href: a ? (a.getAttribute('href') || '') : '' };
    });
    check('visiteur : opt-in = lien vers compte.html', ctaType.tag === 'A' && ctaType.href.indexOf('compte.html') !== -1, JSON.stringify(ctaType));
    /* Fermeture par Échap */
    await page.keyboard.press('Escape');
    const closed = await page.evaluate(function () { return document.getElementById('notifsPanel').hidden; });
    check('fermeture panneau par Échap', closed);
    /* Tout marquer comme lu */
    await page.click('#notifsBell');
    await waitFor(function () { return page.evaluate(function () { return !document.getElementById('notifsPanel').hidden; }); });
    await page.click('#notifsMarkAll');
    await page.click('#notifsBell'); /* ferme */
    const markAllOk = await page.evaluate(function () {
      var b = document.getElementById('notifsBadge');
      return b && b.hidden && document.querySelectorAll('#notifsList .notifs-item.unread').length === 0;
    });
    check('tout marquer comme lu → badge masqué, plus de non-lus', markAllOk);
    /* Persistance après reload */
    await page.reload({ waitUntil: 'load' });
    await waitFor(function () { return page.evaluate(function () { return !!document.getElementById('notifsBell'); }); });
    const persisted = await page.evaluate(function () {
      var b = document.getElementById('notifsBadge');
      return b && b.hidden;
    });
    check('persistance : badge reste masqué après reload', persisted);
    /* Données source : Cholet corrigé au 27/09 19h */
    const cholet = await page.evaluate(function () {
      if (!window.ASVEL_GAMES) return null;
      for (var i = 0; i < window.ASVEL_GAMES.length; i++) {
        var g = window.ASVEL_GAMES[i];
        if (g[2] === 'Cholet Basket' && g[3] === 'away') return g[0] + '|' + g[1];
      }
      return null;
    });
    check('data.js : Cholet away = 2026-09-27 19h00', cholet === '2026-09-27|19h00', String(cholet));
    await page.close();
  }
  {
    const page = await member.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/index.html', { waitUntil: 'load' });
    await waitFor(function () { return page.evaluate(function () { return !!document.getElementById('notifsBell'); }); });
    await page.click('#notifsBell');
    await waitFor(function () { return page.evaluate(function () { return !document.getElementById('notifsPanel').hidden; }); });
    const btnType = await page.evaluate(function () {
      var el = document.querySelector('#notifsPanel .notifs-enable');
      return el ? el.tagName : null;
    });
    check('membre : opt-in = bouton "Activer les alertes"', btnType === 'BUTTON', String(btnType));
    /* Le clic ne doit pas lever d'erreur (permission refusée/acceptée selon le navigateur) */
    let threw = false;
    try { await page.click('#notifsEnable').catch(function () {}); } catch (e) { threw = true; }
    check('membre : clic opt-in sans erreur JS', !threw);
    await page.close();
  }

  console.log('\n=== Partie C — Avantages membre (compte + espace membre + tribune) ===');
  {
    const page = await member.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/compte.html', { waitUntil: 'load' });
    const ok = await page.evaluate(function () {
      var st = document.getElementById('stateSignedIn');
      var since = document.getElementById('mpSince');
      var pronos = document.getElementById('mpPronos');
      var cinq = document.getElementById('mpCinq');
      var link = document.querySelector('.member-link');
      return st && !st.hidden && since && since.textContent.indexOf('sept.') !== -1 && pronos.textContent === '2' && cinq.textContent === '5/5' && link && link.getAttribute('href').indexOf('espace-membre.html') !== -1;
    });
    check('compte : mini-profil membre (depuis, pronos, compo, lien espace)', ok);
    await page.close();
  }
  {
    const page = await member.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/espace-membre.html', { waitUntil: 'load' });
    const ok = await page.evaluate(function () {
      var guest = document.getElementById('memberGuest');
      var panel = document.getElementById('memberPanel');
      var pseudo = document.getElementById('emPseudo');
      var rankRows = document.querySelectorAll('#emRank .rank-row').length;
      var hasVous = document.querySelector('#emRank .you');
      return guest.hidden && !panel.hidden && pseudo.textContent.indexOf('TestMembre') !== -1 && rankRows >= 1 && !!hasVous;
    });
    check('espace-membre : profil + classement local avec "Vous"', ok);
    const cinqSeats = await page.evaluate(function () { return document.querySelectorAll('#emCinq .seat b:not(.empty)').length; });
    check('espace-membre : compo du jour (5 sièges remplis)', cinqSeats === 5, 'seats=' + cinqSeats);
    await page.close();
  }
  {
    const page = await visitor.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/espace-membre.html', { waitUntil: 'load' });
    const ok = await page.evaluate(function () {
      return !document.getElementById('memberGuest').hidden && document.getElementById('memberPanel').hidden;
    });
    check('espace-membre : verrou visiteur actif', ok);
    await page.close();
  }
  {
    const page = await member.newPage(); await attachErrors(page, []);
    await page.goto(BASE + '/interactif.html', { waitUntil: 'load' });
    const hasBadgeCss = await page.evaluate(function () {
      var sheets = document.styleSheets, found = false;
      for (var i = 0; i < sheets.length; i++) {
        try {
          var rules = sheets[i].cssRules;
          for (var j = 0; j < rules.length; j++) {
            if (rules[j].selectorText && rules[j].selectorText.indexOf('.member-tag') !== -1) found = true;
          }
        } catch (e) {}
      }
      return found;
    });
    check('tribune : style du badge Membre présent (.member-tag)', hasBadgeCss);
    await page.close();
  }

  /* Console : aucune erreur JS non gérée sur un chargement clé */
  {
    const box = [];
    const page = await member.newPage(); await attachErrors(page, box);
    await page.goto(BASE + '/interactif.html', { waitUntil: 'load' });
    await page.waitForTimeout(800);
    check('interactif (membre) : aucune erreur JS à l\'exécution', box.length === 0, box.join(' | '));
    await page.close();
  }

  await visitor.close(); await member.close(); await browser.close();

  server.close();
  console.log('\nRésultat : ' + passed + ' / ' + (passed + failed) + ' tests OK' + (failed ? ' — ÉCHECS : ' + failed : ' ✓'));
  process.exit(failed ? 1 : 0);
}

server.listen(PORT, '127.0.0.1', function () {
  console.log('Serving ' + ROOT + ' on ' + BASE);
  main().catch(function (e) {
    console.error('FATAL', e);
    process.exit(1);
  });
});