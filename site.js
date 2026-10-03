(function () {
  'use strict';

  /* ---- Thème clair / sombre : bootstrap avant tout rendu ---- */
  var THEME_KEY = 'asvel-theme';

  function readStorage(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }
  function writeStorage(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* stockage indisponible */ }
  }
  function applyTheme(theme, persist) {
    document.documentElement.setAttribute('data-theme', theme);
    if (persist) writeStorage(THEME_KEY, theme);
    var btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = theme === 'light' ? '☀' : '☾';
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', theme === 'light' ? '#ffffff' : '#000000');
  }
  function toggleTheme() {
    var next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    applyTheme(next, true);
  }
  var savedTheme = readStorage(THEME_KEY);
  if (savedTheme === 'light' || savedTheme === 'dark') {
    applyTheme(savedTheme, false);
  } else if (window.matchMedia) {
    var mq = window.matchMedia('(prefers-color-scheme: light)');
    var followSystem = function () {
      if (!readStorage(THEME_KEY)) applyTheme(mq.matches ? 'light' : 'dark', false);
    };
    followSystem();
    if (mq.addEventListener) mq.addEventListener('change', followSystem);
    else if (mq.addListener) mq.addListener(followSystem);
  }

  var header = document.querySelector('body > header, .site-header');
  if (header) {
    var inArticle = location.pathname.indexOf('/articles/') !== -1;
    var root = inArticle ? '../' : '';
    /* Fonctionnalités préparées mais désactivées. Passer bourse à true quand le service de
       Bourse aux places existe (page bourse-aux-places.html) : l'entrée « Plus » et le bloc
       d'accueil (#bourse-block) apparaissent alors sans autre modification. */
    var FEATURES = window.ASVEL_FEATURES || { bourse: false };

    var primary = [
      ['Accueil', root + 'index.html', 'home'],
      ['Actualités', root + 'actualites.html', 'news'],
      ['Matchs', root + 'matchs.html#calendrier', 'matches'],
      ['Équipe', root + 'effectif.html', 'roster']
    ];
    var more = [
      ['Statistiques', root + 'statistiques.html', 'stats', 'Chiffres par compétition'],
      ['Classements', root + 'matchs.html#classement', 'standings', 'EuroLeague · Betclic ÉLITE'],
      ['Mercato', root + 'mercato.html', 'mercato', 'Arrivées, départs, prêts'],
      ['Palmarès', root + 'palmares.html', 'honours', 'Titres et finales'],
      ['Supporters', root + 'interactif.html', 'interactive', 'Pronos & Cinq, tribune'],
      ['Accès', root + 'acces.html', 'access', 'Venir à la salle'],
      ['Mon compte', root + 'compte.html', 'account', 'Espace supporter'],
      ['À propos', root + 'a-propos.html', 'about', 'Le site et les mentions'],
      ['Contact', root + 'a-propos.html#contact', 'contact', 'Nous écrire']
    ];
    if (FEATURES.bourse) more.splice(5, 0, ['Bourse aux places', root + 'bourse-aux-places.html', 'tickets', 'Échanger des places']);
    var moreKeys = more.map(function (m) { return m[2]; });

    function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
    function linkHtml(item, withHint) {
      return '<a href="' + item[1] + '" data-menu-page="' + item[2] + '">' + esc(item[0]) +
        (withHint && item[3] ? '<small>' + esc(item[3]) + '</small>' : '') + '</a>';
    }

    header.classList.add('global-site-header');

    var logo = header.querySelector('.logo');
    if (!logo) {
      logo = document.createElement('a');
      logo.className = 'logo';
      header.insertBefore(logo, header.firstChild);
    }
    logo.href = root + 'index.html';
    logo.textContent = 'ACTU ASVEL';

    var oldFanBadge = header.querySelector('.fan-badge');
    if (oldFanBadge) oldFanBadge.remove();
    var fanBadge = document.createElement('span');
    fanBadge.className = 'fan-badge';
    fanBadge.textContent = 'SITE FAN';
    fanBadge.title = 'Média indépendant créé par des fans, non affilié au club ASVEL';
    fanBadge.style.cssText = 'display:inline-flex;align-items:center;margin-left:.55rem;padding:.2rem .5rem;background:#ff3b30;color:#fff;border-radius:3px;font-family:Oswald,Arial,sans-serif;font-size:.55rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;line-height:1;white-space:nowrap;vertical-align:middle;';
    logo.insertAdjacentElement('afterend', fanBadge);

    var oldNav = header.querySelector('nav, .site-nav, .nav');
    var desktopNav = document.createElement('nav');
    desktopNav.id = 'site-navigation';
    desktopNav.className = 'global-site-nav';
    desktopNav.setAttribute('aria-label', 'Navigation principale');
    desktopNav.innerHTML = primary.map(function (item) { return linkHtml(item, false); }).join('') +
      '<button type="button" class="plus-toggle" id="plusToggle" aria-haspopup="true" aria-expanded="false" aria-controls="plus-panel">Plus <i aria-hidden="true">▾</i></button>';
    if (oldNav) oldNav.replaceWith(desktopNav);
    else header.appendChild(desktopNav);

    /* Panneau « Plus » (bureau) : hors du <nav> pour ne pas hériter de ses styles de liens */
    var plusPanel = document.createElement('div');
    plusPanel.id = 'plus-panel';
    plusPanel.className = 'plus-panel';
    plusPanel.setAttribute('aria-label', 'Plus de pages');
    plusPanel.hidden = true;
    plusPanel.innerHTML = more.map(function (item) { return linkHtml(item, true); }).join('');
    header.appendChild(plusPanel);
    var plusToggle = desktopNav.querySelector('#plusToggle');
    function setPlus(open, restoreFocus) {
      plusPanel.hidden = !open;
      plusToggle.setAttribute('aria-expanded', String(open));
      plusToggle.classList.toggle('open', open);
      if (!open && restoreFocus) plusToggle.focus();
    }
    plusToggle.addEventListener('click', function (event) {
      event.stopPropagation();
      setPlus(plusPanel.hidden, false);
    });
    plusPanel.addEventListener('click', function (event) {
      if (event.target.closest('a')) setPlus(false, false);
    });
    document.addEventListener('click', function (event) {
      if (!plusPanel.hidden && !plusPanel.contains(event.target)) setPlus(false, false);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && !plusPanel.hidden) setPlus(false, true);
    });

    var oldToggle = header.querySelector('.menu-toggle, .global-menu-toggle');
    if (oldToggle) oldToggle.remove();

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.id = 'globalMenuToggle';
    toggle.className = 'menu-toggle global-menu-toggle';
    toggle.setAttribute('aria-controls', 'mobile-site-navigation');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Ouvrir le menu');
    toggle.innerHTML = '<span></span><span></span><span></span>';
    header.appendChild(toggle);

    var themeBtn = document.createElement('button');
    themeBtn.type = 'button';
    themeBtn.className = 'theme-toggle';
    themeBtn.id = 'themeToggle';
    themeBtn.setAttribute('aria-label', 'Basculer entre le thème clair et sombre');
    themeBtn.textContent = document.documentElement.getAttribute('data-theme') === 'light' ? '☀' : '☾';
    header.insertBefore(themeBtn, toggle);
    themeBtn.addEventListener('click', toggleTheme);

    document.querySelectorAll('.mobile-nav-drawer,.mobile-nav-backdrop').forEach(function (el) { el.remove(); });

    var drawer = document.createElement('nav');
    drawer.id = 'mobile-site-navigation';
    drawer.className = 'mobile-nav-drawer';
    drawer.setAttribute('aria-label', 'Navigation mobile');
    drawer.setAttribute('aria-hidden', 'true');
    drawer.innerHTML = primary.map(function (item) { return linkHtml(item, false); }).join('') +
      '<div class="drawer-label">Plus</div>' +
      more.map(function (item) { return linkHtml(item, false); }).join('');
    document.body.appendChild(drawer);

    var backdrop = document.createElement('button');
    backdrop.type = 'button';
    backdrop.className = 'mobile-nav-backdrop';
    backdrop.setAttribute('aria-label', 'Fermer le menu');
    backdrop.setAttribute('tabindex', '-1');
    document.body.appendChild(backdrop);

    function currentSection() {
      var page = location.pathname.split('/').pop() || 'index.html';
      if (inArticle || page === 'actualites.html') return 'news';
      if (page === 'mercato.html') return 'mercato';
      if (page === 'effectif.html') return 'roster';
      if (page === 'interactif.html' || page === 'espace-membre.html') return 'interactive';
      if (page === 'statistiques.html') return 'stats';
      if (page === 'palmares.html') return 'honours';
      if (page === 'acces.html') return 'access';
      if (page === 'compte.html') return 'account';
      if (page === 'bourse-aux-places.html') return 'tickets';
      if (page === 'a-propos.html') return location.hash === '#contact' ? 'contact' : 'about';
      if (page === 'matchs.html') return location.hash === '#classement' ? 'standings' : 'matches';
      return 'home';
    }

    function markCurrentSection() {
      var section = currentSection();
      [desktopNav, plusPanel, drawer].forEach(function (nav) {
        nav.querySelectorAll('a').forEach(function (link) {
          var active = link.dataset.menuPage === section;
          link.classList.toggle('active', active);
          if (active) link.setAttribute('aria-current', 'page');
          else link.removeAttribute('aria-current');
        });
      });
      plusToggle.classList.toggle('active', moreKeys.indexOf(section) !== -1);
    }

    function syncMenuPosition() {
      var rect = header.getBoundingClientRect();
      document.documentElement.style.setProperty('--mobile-nav-top', Math.max(0, Math.round(rect.bottom)) + 'px');
    }

    function setMenu(open, restoreFocus) {
      syncMenuPosition();
      drawer.classList.toggle('open', open);
      toggle.classList.toggle('open', open);
      backdrop.classList.toggle('visible', open);
      document.body.classList.toggle('menu-open', open);
      drawer.setAttribute('aria-hidden', String(!open));
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
      if (!open && restoreFocus) toggle.focus();
    }

    toggle.addEventListener('click', function () {
      setMenu(!drawer.classList.contains('open'), false);
    });
    backdrop.addEventListener('click', function () { setMenu(false, true); });
    drawer.addEventListener('click', function (event) {
      if (event.target.closest('a')) setMenu(false, false);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && drawer.classList.contains('open')) setMenu(false, true);
    });
    window.addEventListener('resize', function () {
      syncMenuPosition();
      if (window.innerWidth > 980 && drawer.classList.contains('open')) setMenu(false, false);
      if (window.innerWidth <= 980 && !plusPanel.hidden) setPlus(false, false);
    });
    window.addEventListener('scroll', function () {
      if (drawer.classList.contains('open')) syncMenuPosition();
    }, { passive: true });
    window.addEventListener('hashchange', function () {
      markCurrentSection();
      if (window.innerWidth <= 980) setMenu(false, false);
    });

    syncMenuPosition();
    markCurrentSection();

    /* Blocs « préparés » : visibles uniquement quand la fonctionnalité est activée */
    document.querySelectorAll('[data-feature]').forEach(function (block) {
      block.hidden = !FEATURES[block.getAttribute('data-feature')];
    });
  }

  /* ---- Lien "Mentions légales" dans le pied de page, sur toutes les pages ---- */
  var footer = document.querySelector('footer');
  if (footer && !footer.querySelector('.legal-link')) {
    var legalRoot = location.pathname.indexOf('/articles/') !== -1 ? '../' : '';
    var legalLink = document.createElement('a');
    legalLink.className = 'legal-link';
    legalLink.href = legalRoot + 'a-propos.html';
    legalLink.textContent = 'Mentions légales';
    legalLink.style.cssText = 'margin-left:.9rem;';
    var igLink = footer.querySelector('a[href*="instagram.com"]');
    if (igLink) igLink.insertAdjacentElement('afterend', legalLink);
    else footer.appendChild(legalLink);
  }

  document.querySelectorAll('img').forEach(function (image, index) {
    image.decoding = 'async';
    if (index > 0 && !image.classList.contains('hero-image')) image.loading = 'lazy';
  });

  var progress = document.querySelector('.article-content') ? document.createElement('div') : null;
  if (progress) {
    progress.className = 'reading-progress';
    progress.setAttribute('aria-hidden', 'true');
    document.body.appendChild(progress);
  }

  var topButton = document.createElement('button');
  topButton.className = 'back-to-top';
  topButton.type = 'button';
  topButton.setAttribute('aria-label', 'Revenir en haut de la page');
  topButton.textContent = '↑';
  document.body.appendChild(topButton);
  topButton.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  function onScroll() {
    var y = window.scrollY || document.documentElement.scrollTop;
    document.body.classList.toggle('has-scrolled', y > 12);
    topButton.classList.toggle('visible', y > 650);
    if (progress) {
      var height = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.transform = 'scaleX(' + (height > 0 ? Math.min(1, y / height) : 0) + ')';
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- Monogrammes : images manquantes → placeholder noir/or ---- */
  function initials(text, fallback) {
    var words = String(text || '').trim().split(/\s+/).filter(Boolean);
    if (!words.length) return fallback || 'ASVEL';
    var out = words.map(function (w) { return w.charAt(0); }).slice(0, 2).join('').toUpperCase();
    return out || fallback || 'ASVEL';
  }
  document.addEventListener('error', function (event) {
    var target = event.target;
    if (!target || target.tagName !== 'IMG') return;
    if (target.matches('.hero-image')) { target.style.display = 'none'; return; }
    if (target.closest('.initials')) {
      var box = target.closest('.initials');
      if (!box.textContent.trim()) {
        var monogram = document.createElement('span');
        monogram.className = 'media-fallback';
        monogram.setAttribute('aria-hidden', 'true');
        monogram.textContent = initials(target.getAttribute('alt') || '', 'ASVEL');
        box.appendChild(monogram);
      }
      target.style.display = 'none';
      return;
    }
    if (target.closest('.club-mark')) { target.style.display = 'none'; return; }
    if (target.closest('.movement-photo')) {
      var div = document.createElement('div');
      div.className = 'movement-photo media-fallback';
      div.textContent = initials(target.getAttribute('alt') || '', 'ASVEL');
      if (target.parentNode) target.parentNode.replaceChild(div, target);
      return;
    }
    target.style.display = 'none';
  }, true);

  /* ---- Reveal au défilement (désactivé si réduction de mouvement) ---- */
  var revealTargets = document.querySelectorAll('.reveal-on-scroll');
  if (revealTargets.length) {
    var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if ('IntersectionObserver' in window && !reduced) {
      var revealObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            revealObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12 });
      revealTargets.forEach(function (el) { revealObserver.observe(el); });
    } else {
      revealTargets.forEach(function (el) { el.classList.add('revealed'); });
    }
  }
})();
