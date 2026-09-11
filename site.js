(function () {
  'use strict';

  var header = document.querySelector('body > header, .site-header');
  if (header) {
    var inArticle = location.pathname.indexOf('/articles/') !== -1;
    var root = inArticle ? '../' : '';
    var items = [
      ['Accueil', root + 'index.html', 'home'],
      ['Actualités', root + 'actualites.html', 'news'],
      ['Mercato', root + 'mercato.html', 'mercato'],
      ['Matchs', root + 'matchs.html#calendrier', 'matches'],
      ['Classements', root + 'matchs.html#classement', 'standings'],
      ['Effectif', root + 'effectif.html', 'roster'],
      ['Stats', root + 'statistiques.html', 'stats'],
      ['Palmarès', root + 'palmares.html', 'honours'],
      ['À propos', root + 'a-propos.html', 'about']
    ];

    header.classList.add('global-site-header');

    var logo = header.querySelector('.logo');
    if (!logo) {
      logo = document.createElement('a');
      logo.className = 'logo';
      header.insertBefore(logo, header.firstChild);
    }
    logo.href = root + 'index.html';
    logo.textContent = 'ACTU ASVEL';

    var oldNav = header.querySelector('nav, .site-nav, .nav');
    var nav = document.createElement('nav');
    nav.id = 'site-navigation';
    nav.className = 'global-site-nav';
    nav.setAttribute('aria-label', 'Navigation principale');
    nav.innerHTML = items.map(function (item) {
      return '<a href="' + item[1] + '" data-menu-page="' + item[2] + '">' + item[0] + '</a>';
    }).join('');

    if (oldNav) oldNav.replaceWith(nav);
    else header.appendChild(nav);

    var oldToggle = header.querySelector('.menu-toggle, .global-menu-toggle');
    if (oldToggle) oldToggle.remove();

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.id = 'globalMenuToggle';
    toggle.className = 'menu-toggle global-menu-toggle';
    toggle.setAttribute('aria-controls', nav.id);
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Ouvrir le menu');
    toggle.innerHTML = '<span></span><span></span><span></span>';
    header.appendChild(toggle);

    document.querySelectorAll('.mobile-nav-backdrop').forEach(function (el) { el.remove(); });
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
      if (page === 'statistiques.html') return 'stats';
      if (page === 'palmares.html') return 'honours';
      if (page === 'a-propos.html') return 'about';
      if (page === 'matchs.html') {
        return location.hash === '#classement' ? 'standings' : 'matches';
      }
      return 'home';
    }

    function markCurrentSection() {
      var section = currentSection();
      nav.querySelectorAll('a').forEach(function (link) {
        var active = link.dataset.menuPage === section;
        link.classList.toggle('active', active);
        if (active) link.setAttribute('aria-current', 'page');
        else link.removeAttribute('aria-current');
      });
    }

    function syncMenuPosition() {
      var bottom = Math.max(0, Math.round(header.getBoundingClientRect().bottom));
      document.documentElement.style.setProperty('--mobile-nav-top', bottom + 'px');
    }

    function setMenu(open, restoreFocus) {
      nav.classList.toggle('open', open);
      toggle.classList.toggle('open', open);
      backdrop.classList.toggle('visible', open);
      document.body.classList.toggle('menu-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
      if (open) syncMenuPosition();
      if (!open && restoreFocus) toggle.focus();
    }

    toggle.addEventListener('click', function () {
      setMenu(!nav.classList.contains('open'), false);
    });

    backdrop.addEventListener('click', function () { setMenu(false, true); });

    nav.addEventListener('click', function (event) {
      var link = event.target.closest('a');
      if (!link) return;
      if (window.innerWidth <= 980) setMenu(false, false);
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && nav.classList.contains('open')) setMenu(false, true);
    });

    window.addEventListener('resize', function () {
      syncMenuPosition();
      if (window.innerWidth > 980 && nav.classList.contains('open')) setMenu(false, false);
    });

    window.addEventListener('hashchange', function () {
      markCurrentSection();
      if (window.innerWidth <= 980) setMenu(false, false);
    });

    syncMenuPosition();
    markCurrentSection();
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
  topButton.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

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

  var revealTargets = document.querySelectorAll(
    '.metric, .player, .news-card, .player-card, .staff-card, article.article, .latest-card, ' +
    '.movement, .article-content > h2, .article-content > h3, .article-content > p, .article-content > blockquote, ' +
    '.trophy, .comparison-card'
  );
  if (revealTargets.length && 'IntersectionObserver' in window) {
    revealTargets.forEach(function (el) { el.classList.add('reveal-on-scroll'); });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    revealTargets.forEach(function (el) { io.observe(el); });
    window.setTimeout(function () {
      document.querySelectorAll('.reveal-on-scroll:not(.revealed)').forEach(function (el) {
        el.classList.add('revealed');
      });
    }, 2500);
  } else {
    revealTargets.forEach(function (el) { el.classList.add('revealed'); });
  }

  var counters = document.querySelectorAll('.metric strong, .stat strong');
  if (counters.length && 'IntersectionObserver' in window) {
    var counterIo = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        counterIo.unobserve(el);
        var raw = el.textContent.trim();
        var match = raw.match(/^(\d+)/);
        if (!match) return;
        var target = parseInt(match[1], 10);
        var suffix = raw.slice(match[1].length);
        var duration = 900;
        var startTime = null;
        function tick(ts) {
          if (!startTime) startTime = ts;
          var p = Math.min(1, (ts - startTime) / duration);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(eased * target) + suffix;
          if (p < 1) requestAnimationFrame(tick);
          else el.textContent = raw;
        }
        requestAnimationFrame(tick);
      });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { counterIo.observe(el); });
  }
})();
