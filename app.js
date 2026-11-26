/* ======= ACTU ASVEL — Navigation & Utilitaires ======= */

(function() {
  'use strict';

  // ======= MENU MOBILE =======
  const menuToggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('nav');

  if (menuToggle && nav) {
    menuToggle.addEventListener('click', function() {
      const isOpen = nav.classList.toggle('open');
      menuToggle.classList.toggle('open', isOpen);
      menuToggle.setAttribute('aria-expanded', String(isOpen));
    });

    nav.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', function() {
        nav.classList.remove('open');
        menuToggle.classList.remove('open');
        menuToggle.setAttribute('aria-expanded', 'false');
      });
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) {
        nav.classList.remove('open');
        menuToggle.classList.remove('open');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ======= ACTIVE NAV LINK =======
  function updateActiveLink() {
    const currentPath = window.location.pathname;
    const fileName = currentPath.split('/').pop() || 'index.html';

    nav?.querySelectorAll('a').forEach(link => {
      const href = link.getAttribute('href');
      const isActive = href === fileName ||
                      (fileName === '' && href === 'index.html') ||
                      (currentPath.endsWith(href));

      link.classList.toggle('active', isActive);
      link.setAttribute('aria-current', isActive ? 'page' : 'false');
    });
  }

  updateActiveLink();
  window.addEventListener('hashchange', updateActiveLink);

  // ======= SCROLL REVEAL =======
  const revealElements = document.querySelectorAll('.reveal');
  if (revealElements.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    revealElements.forEach(el => observer.observe(el));
  }

  // ======= SHARE BUTTON =======
  window.shareArticle = async function(title, text, url) {
    const data = { title, text, url: url || window.location.href };

    if (navigator.share) {
      try {
        await navigator.share(data);
      } catch (err) {
        if (err.name !== 'AbortError') fallbackCopy(data.url);
      }
    } else {
      fallbackCopy(data.url);
    }
  };

  function fallbackCopy(url) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(url).then(() => {
        showNotification('Lien copié !');
      });
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = url;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      textarea.remove();
      showNotification('Lien copié !');
    }
  }

  function showNotification(msg) {
    const notif = document.createElement('div');
    notif.style.cssText = `
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: var(--primary-dark);
      color: white;
      padding: 1rem 1.5rem;
      border-radius: 8px;
      font-size: 0.9rem;
      z-index: 1000;
      animation: slideIn 0.3s ease;
    `;
    notif.textContent = msg;
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 2000);
  }

  // ======= LAZY LOAD IMAGES =======
  document.querySelectorAll('img[data-src]').forEach(img => {
    img.src = img.dataset.src;
    img.removeAttribute('data-src');
  });

})();
