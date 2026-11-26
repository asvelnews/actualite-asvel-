/* ========== ASVEL 2026-2027 — APP LOGIC ========== */

(function() {
  'use strict';

  // ========== CAROUSEL ==========
  const carousel = document.querySelector('.carousel-track');
  if (carousel) {
    const slides = document.querySelectorAll('.carousel-slide');
    const dots = document.querySelectorAll('.carousel-dot');
    let currentSlide = 0;

    function showSlide(n) {
      slides.forEach(s => s.classList.remove('active'));
      dots.forEach(d => d.classList.remove('active'));
      slides[n].classList.add('active');
      dots[n].classList.add('active');
      currentSlide = n;
    }

    // Auto-advance carousel every 5 seconds
    setInterval(() => {
      showSlide((currentSlide + 1) % slides.length);
    }, 5000);

    // Dots click handlers
    dots.forEach((dot, idx) => {
      dot.addEventListener('click', () => showSlide(idx));
    });
  }

  // ========== MOBILE MENU ==========
  const menuBtn = document.querySelector('.menu-btn');
  const nav = document.querySelector('.nav');

  if (menuBtn && nav) {
    menuBtn.addEventListener('click', () => {
      nav.classList.toggle('open');
    });

    nav.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        nav.classList.remove('open');
      });
    });

    // Close on ESC
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        nav.classList.remove('open');
      }
    });
  }

  // ========== ACTIVE NAV LINK ==========
  function updateActiveLink() {
    const currentPath = window.location.pathname;
    const fileName = currentPath.split('/').pop() || 'index.html';

    document.querySelectorAll('.nav-link').forEach(link => {
      const href = link.getAttribute('href');
      const isActive = href === fileName ||
                      (fileName === '' && href === 'index.html') ||
                      (currentPath.endsWith(href));
      link.classList.toggle('active', isActive);
    });
  }

  updateActiveLink();
  window.addEventListener('hashchange', updateActiveLink);

  // ========== SCROLL REVEAL ==========
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

  // ========== SHARE FUNCTIONALITY ==========
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
      background: var(--primary);
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

})();
