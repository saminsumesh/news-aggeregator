/* PulseNews — main.js */

// ── Mobile Nav Toggle ─────────────────────────────
const menuToggle = document.getElementById('menuToggle');
const mainNav = document.getElementById('mainNav');
if (menuToggle && mainNav) {
  menuToggle.addEventListener('click', () => {
    mainNav.classList.toggle('open');
  });
  document.addEventListener('click', (e) => {
    if (!menuToggle.contains(e.target) && !mainNav.contains(e.target)) {
      mainNav.classList.remove('open');
    }
  });
}

// ── User Dropdown ──────────────────────────────────
const userBtn = document.getElementById('userBtn');
const userDropdown = document.getElementById('userDropdown');
if (userBtn && userDropdown) {
  userBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = userDropdown.style.display === 'block';
    userDropdown.style.display = isOpen ? 'none' : 'block';
  });
  document.addEventListener('click', () => {
    if (userDropdown) userDropdown.style.display = 'none';
  });
}

// ── Auto-dismiss messages ──────────────────────────
document.querySelectorAll('.message').forEach(msg => {
  setTimeout(() => {
    msg.style.opacity = '0';
    msg.style.transition = 'opacity 0.4s ease';
    setTimeout(() => msg.remove(), 400);
  }, 4000);
});

// ── CSRF helper ────────────────────────────────────
function getCsrfToken() {
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1].trim() : '';
}

// ── Smooth scroll for anchor links ────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// ── Lazy load images polyfill ─────────────────────
if ('loading' in HTMLImageElement.prototype) {
  // Native support
} else {
  const images = document.querySelectorAll('img[loading="lazy"]');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.src = entry.target.dataset.src;
        observer.unobserve(entry.target);
      }
    });
  });
  images.forEach(img => observer.observe(img));
}

// ── Fade-in cards on scroll ───────────────────────
const cards = document.querySelectorAll('.article-card');
if (cards.length && 'IntersectionObserver' in window) {
  const cardObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        cardObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach((card, i) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(16px)';
    card.style.transition = `opacity 0.4s ease ${i * 0.05}s, transform 0.4s ease ${i * 0.05}s`;
    cardObserver.observe(card);
  });
}

// ── Search expand ─────────────────────────────────
const searchInput = document.querySelector('.search-input');
if (searchInput) {
  searchInput.addEventListener('focus', () => searchInput.classList.add('expanded'));
  searchInput.addEventListener('blur', () => {
    if (!searchInput.value) searchInput.classList.remove('expanded');
  });
}

// ── Confirm before destructive actions ────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});

console.log('%cPulseNews', 'font-family:serif;font-size:24px;font-weight:900;color:#c0392b;');
console.log('%cPowered by Django + NewsAPI + Groq AI', 'font-size:12px;color:#888;');
