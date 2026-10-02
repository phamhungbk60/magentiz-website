/* =============================================
   MAGENTIZ - Main JavaScript
   ============================================= */

document.addEventListener('DOMContentLoaded', () => {

  /* --- Theme toggle (initial theme is applied inline in <head>) --- */
  const themeToggle = document.querySelector('.theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const isLight = document.documentElement.classList.toggle('light');
      try { localStorage.setItem('theme', isLight ? 'light' : 'dark'); } catch (e) {}
    });
  }

  /* --- Navbar scroll effect --- */
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    const onScroll = () => navbar.classList.toggle('scrolled', window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* --- Mobile nav toggle --- */
  const navToggle = document.querySelector('.nav-toggle');
  const navMenu = document.querySelector('.nav-menu');

  if (navToggle && navMenu) {
    const closeMenu = () => {
      navMenu.classList.remove('open');
      navToggle.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    };

    navToggle.addEventListener('click', () => {
      const isOpen = navMenu.classList.toggle('open');
      navToggle.classList.toggle('open', isOpen);
      navToggle.setAttribute('aria-expanded', isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });

    navMenu.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));

    document.addEventListener('click', (e) => {
      if (!navbar.contains(e.target) && navMenu.classList.contains('open')) closeMenu();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && navMenu.classList.contains('open')) closeMenu();
    });
  }

  /* --- Active nav link (clean URLs: /services, /services.html, /services/) --- */
  const normalize = (p) => p.replace(/\.html$/, '').replace(/\/index$/, '/').replace(/(.)\/$/, '$1') || '/';
  const currentPath = normalize(window.location.pathname);
  document.querySelectorAll('.nav-link').forEach(link => {
    if (normalize(link.getAttribute('href')) === currentPath) {
      link.classList.add('active');
      link.setAttribute('aria-current', 'page');
    }
  });

  /* --- Scroll reveal animation --- */
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.querySelectorAll('.stagger-children').forEach(parent => {
    parent.querySelectorAll(':scope > *').forEach((child, i) => {
      child.classList.add('reveal', `reveal-delay-${Math.min(i + 1, 5)}`);
    });
  });

  if (reduceMotion || !('IntersectionObserver' in window)) {
    document.querySelectorAll('.reveal').forEach(el => el.classList.add('visible'));
  } else {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));
  }

  /* --- Animated counter (numbers formatted for the page language, e.g. 99.9 / 99,9) --- */
  const pageLang = document.documentElement.lang || 'en';
  const formatNumber = (value, decimals) => new Intl.NumberFormat(pageLang, {
    minimumFractionDigits: decimals, maximumFractionDigits: decimals,
  }).format(value);

  function animateCounter(el, target, duration = 1800) {
    const start = performance.now();
    const decimals = target % 1 !== 0 ? 1 : 0;

    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const value = (1 - Math.pow(1 - progress, 3)) * target; // ease-out cubic
      el.textContent = formatNumber(decimals ? value : Math.floor(value), decimals);
      if (progress < 1) requestAnimationFrame(tick);
      else el.textContent = formatNumber(target, decimals);
    };

    requestAnimationFrame(tick);
  }

  const counters = document.querySelectorAll('[data-target]');
  if (reduceMotion || !('IntersectionObserver' in window)) {
    // Keep the server-rendered text, which is already formatted for the page language
  } else {
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target, parseFloat(entry.target.dataset.target));
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(el => counterObserver.observe(el));
  }

  /* --- Smooth scroll for in-page anchor links --- */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const id = anchor.getAttribute('href');
      if (id.length < 2) return;
      const target = document.querySelector(id);
      if (target) {
        e.preventDefault();
        const offset = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-height')) || 72;
        const top = target.getBoundingClientRect().top + window.scrollY - offset - 16;
        window.scrollTo({ top, behavior: reduceMotion ? 'auto' : 'smooth' });
        history.replaceState(null, '', id);
      }
    });
  });

});
