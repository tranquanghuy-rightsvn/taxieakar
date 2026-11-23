// Header scroll behavior
const header = document.querySelector('.site-header');
if (header) {
  window.addEventListener('scroll', () => {
    header.classList.toggle('scrolled', window.scrollY > 50);
  }, { passive: true });
}

// Mobile menu toggle
const navToggle = document.querySelector('.nav-toggle');
const navClose = document.querySelector('.nav-close');
const mainNav = document.querySelector('.main-nav');
const navOverlay = document.getElementById('navOverlay');

function openNav() {
  mainNav?.classList.add('is-open');
  navOverlay?.classList.add('is-open');
  document.body.classList.add('nav-open');
  navToggle?.setAttribute('aria-expanded', 'true');
}

function closeNav() {
  mainNav?.classList.remove('is-open');
  navOverlay?.classList.remove('is-open');
  document.body.classList.remove('nav-open');
  navToggle?.setAttribute('aria-expanded', 'false');
}

if (navToggle && mainNav) {
  navToggle.addEventListener('click', openNav);
}
if (navClose && mainNav) {
  navClose.addEventListener('click', closeNav);
}
if (navOverlay) {
  navOverlay.addEventListener('click', closeNav);
}
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeNav();
});

// Dropdown toggle (tap on mobile/tablet, click toggle on desktop in addition to hover)
const dropdownToggle = document.querySelector('.nav-dropdown-toggle');
if (dropdownToggle) {
  const dropdownItem = dropdownToggle.closest('.has-dropdown');
  dropdownToggle.addEventListener('click', (e) => {
    e.preventDefault();
    const isOpen = dropdownItem?.classList.toggle('is-open');
    dropdownToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });
  document.addEventListener('click', (e) => {
    if (dropdownItem && !dropdownItem.contains(e.target)) {
      dropdownItem.classList.remove('is-open');
      dropdownToggle.setAttribute('aria-expanded', 'false');
    }
  });
}

// Registration form: no backend on this static page, just confirm to the user
const dangkyForm = document.getElementById('dangkyForm');
if (dangkyForm) {
  dangkyForm.addEventListener('submit', (e) => {
    e.preventDefault();
    alert('Cảm ơn bạn đã để lại thông tin. Vui lòng gọi hotline 0368.395.396 để được hỗ trợ đặt xe nhanh nhất.');
    dangkyForm.reset();
  });
}

// Quick booking bar: no backend on this static page, just confirm to the user
const quickBookingForm = document.getElementById('quickBookingForm');
if (quickBookingForm) {
  quickBookingForm.addEventListener('submit', (e) => {
    e.preventDefault();
    alert('Cảm ơn bạn đã đặt xe. Vui lòng gọi hotline 0368.395.396 để được hỗ trợ đặt xe nhanh nhất.');
    quickBookingForm.reset();
  });
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const href = a.getAttribute('href');
    if (href.length > 1) {
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    }
  });
});
