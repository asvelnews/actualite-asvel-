(function () {
  'use strict';

  var header = document.querySelector('body > header, .site-header');
  var nav = header && header.querySelector('nav, .site-nav, .nav');
  var toggle = header && header.querySelector('.menu-toggle');

  if (header && nav) {
    var inArticle = location.pathname.indexOf('/articles/') !== -1;
    var root = inArticle ? '../' : '';
    var items = [
      ['Accueil', root + 'index.html', 'home'],
      ['Actualités', root + 'actualites.html', 'news'],
      ['Mercato', root + 'mercato.html', 'mercato'],
      ['Matchs', root + 'matchs.html#calendrier', 'matches'],
      ['Classements', root + 'matchs.html#classement', 'standings'],
      ['Effectif', root + 'effectif.html', 'roster'],
      ['ASVEL Filles', root + 'filles.html', 'filles'],
      ['Espoirs', root + 'espoirs.html', 'espoirs'],
      ['Palmarès', root + 'palmares.html', 'honours']
    ];

    header.classList.add('global-site-header');
    nav.classList.add('global-site-nav');
    nav.id = 'site-navigation';
    nav.setAttribute('aria-label', 'Navigation principale');
    nav.innerHTML = items.map(function (item) {
      return '<a href="' + item[1] + '" data-menu-page="' + item[2] + '">' + item[0] + '</a>';
    }).join('');

    if (!toggle) {
      toggle = document.createElement('button');
      toggle.className = 'menu-toggle';
      toggle.type = 'button';
      toggle.innerHTML = '<span></span><span></span><span></span>';
      header.appendChild(toggle);
    } else {
      var cleanToggle = toggle.cloneNode(true);
      toggle.parentNode.replaceChild(cleanToggle, toggle);
      toggle = cleanToggle;
    }

    toggle.id = 'globalMenuToggle';
    toggle.classList.add('global-menu-toggle');
    toggle.setAttribute('aria-controls', nav.id);
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Ouvrir le menu');

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
      if (page === 'filles.html') return 'filles';
      if (page === 'espoirs.html') return 'espoirs';
      if (page === 'palmares.html') return 'honours';
      if (page === 'matchs.html') return location.hash.indexOf('classement') !== -1 ? 'standings' : 'matches';
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

    function closeMenu(restoreFocus) {
      nav.classList.remove('open');
      toggle.classList.remove('open');
      backdrop.classList.remove('visible');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Ouvrir le menu');
      document.body.classList.remove('menu-open');
      if (restoreFocus) toggle.focus();
    }

    function openMenu() {
      syncMenuPosition();
      nav.classList.add('open');
      toggle.classList.add('open');
      backdrop.classList.add('visible');
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'Fermer le menu');
      document.body.classList.add('menu-open');
      window.setTimeout(function () {
        var firstLink = nav.querySelector('a');
        if (firstLink) firstLink.focus();
      }, 60);
    }

    toggle.addEventListener('click', function () {
      if (nav.classList.contains('open')) closeMenu(false);
      else openMenu();
    });
    backdrop.addEventListener('click', function () { closeMenu(true); });
    nav.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () { closeMenu(false); });
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && nav.classList.contains('open')) closeMenu(true);
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 980) closeMenu(false);
      else if (nav.classList.contains('open')) syncMenuPosition();
    });
    window.addEventListener('scroll', function () {
      if (nav.classList.contains('open')) syncMenuPosition();
    }, { passive: true });
    window.addEventListener('hashchange', markCurrentSection);
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

  /* --- Animations d'apparition au défilement --- */
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
    /* Filet de sécurité : si un élément reste caché trop longtemps (contenu ajouté dynamiquement après coup), on le révèle quand même */
    window.setTimeout(function () {
      document.querySelectorAll('.reveal-on-scroll:not(.revealed)').forEach(function (el) {
        el.classList.add('revealed');
      });
    }, 2500);
  } else {
    revealTargets.forEach(function (el) { el.classList.add('revealed'); });
  }

  /* --- Compteurs animés pour les chiffres clés --- */
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
        var start = 0;
        var duration = 900;
        var startTime = null;
        function tick(ts) {
          if (!startTime) startTime = ts;
          var progress = Math.min(1, (ts - startTime) / duration);
          var eased = 1 - Math.pow(1 - progress, 3);
          el.textContent = Math.round(eased * target) + suffix;
          if (progress < 1) requestAnimationFrame(tick);
          else el.textContent = raw;
        }
        requestAnimationFrame(tick);
      });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { counterIo.observe(el); });
  }
})();
