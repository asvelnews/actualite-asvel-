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
    var desktopNav = document.createElement('nav');
    desktopNav.id = 'site-navigation';
    desktopNav.className = 'global-site-nav';
    desktopNav.setAttribute('aria-label', 'Navigation principale');
    desktopNav.innerHTML = items.map(function (item) {
      return '<a href="' + item[1] + '" data-menu-page="' + item[2] + '">' + item[0] + '</a>';
    }).join('');
    if (oldNav) oldNav.replaceWith(desktopNav);
    else header.appendChild(desktopNav);

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

    document.querySelectorAll('.mobile-nav-drawer,.mobile-nav-backdrop').forEach(function (el) { el.remove(); });

    var drawer = document.createElement('nav');
    drawer.id = 'mobile-site-navigation';
    drawer.className = 'mobile-nav-drawer';
    drawer.setAttribute('aria-label', 'Navigation mobile');
    drawer.setAttribute('aria-hidden', 'true');
    drawer.innerHTML = items.map(function (item) {
      return '<a href="' + item[1] + '" data-menu-page="' + item[2] + '">' + item[0] + '</a>';
    }).join('');
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
      if (page === 'statistiques.html') return 'stats';
      if (page === 'palmares.html') return 'honours';
      if (page === 'a-propos.html') return 'about';
      if (page === 'matchs.html') return location.hash === '#classement' ? 'standings' : 'matches';
      return 'home';
    }

    function markCurrentSection() {
      var section = currentSection();
      [desktopNav, drawer].forEach(function (nav) {
        nav.querySelectorAll('a').forEach(function (link) {
          var active = link.dataset.menuPage === section;
          link.classList.toggle('active', active);
          if (active) link.setAttribute('aria-current', 'page');
          else link.removeAttribute('aria-current');
        });
      });
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
})();
