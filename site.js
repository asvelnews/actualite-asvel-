(function () {
  'use strict';

  var header = document.querySelector('body > header, .site-header');
  var nav = header && header.querySelector('nav, .site-nav, .nav');
  var toggle = header && header.querySelector('.menu-toggle');
  var injectedToggle = false;

  if (header && nav && !toggle) {
    injectedToggle = true;
    toggle = document.createElement('button');
    toggle.className = 'menu-toggle';
    toggle.type = 'button';
    toggle.setAttribute('aria-label', 'Ouvrir le menu');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.innerHTML = '<span></span><span></span><span></span>';
    header.appendChild(toggle);
  }

  function closeMenu() {
    if (!nav || !toggle) return;
    nav.classList.remove('open');
    toggle.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('menu-open');
  }

  if (nav && toggle && injectedToggle) {
    toggle.dataset.enhanced = 'true';
    toggle.addEventListener('click', function () {
      var open = !nav.classList.contains('open');
      nav.classList.toggle('open', open);
      toggle.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
      document.body.classList.toggle('menu-open', open);
    });
    nav.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', closeMenu);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closeMenu();
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 820) closeMenu();
    });
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
})();
