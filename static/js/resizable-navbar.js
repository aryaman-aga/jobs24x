(function () {
  'use strict';

  function initResizableNavbar(navEl) {
    if (!navEl) return;
    var scrollThreshold = 100;
    var ticking = false;
    var mobileToggle = navEl.querySelector('.rn-mobile-toggle');
    var mobileMenu = navEl.querySelector('.rn-mobile-menu');
    var items = navEl.querySelectorAll('.rn-item');

    /* ── Scroll shrink ── */
    function onScroll() {
      if (!ticking) {
        requestAnimationFrame(function () {
          var shouldShrink = window.scrollY > scrollThreshold;
          navEl.classList.toggle('desktop-shrunk', shouldShrink);
          ticking = false;
        });
        ticking = true;
      }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    /* ── Mobile menu toggle ── */
    if (mobileToggle && mobileMenu) {
      mobileToggle.addEventListener('click', function () {
        var isOpen = mobileMenu.classList.contains('open');
        mobileMenu.classList.toggle('open');
        mobileToggle.setAttribute('aria-expanded', !isOpen);
      });
    }

    /* ── Close mobile menu on link click ── */
    if (mobileMenu) {
      mobileMenu.querySelectorAll('a, .rn-btn').forEach(function (el) {
        el.addEventListener('click', function () {
          mobileMenu.classList.remove('open');
          if (mobileToggle) mobileToggle.setAttribute('aria-expanded', 'false');
        });
      });
    }

    /* ── Nav item hover pill ── */
    items.forEach(function (item) {
      item.addEventListener('mouseenter', function () {
        items.forEach(function (other) {
          var bg = other.querySelector('.rn-item-bg');
          if (bg) bg.style.display = other === item ? '' : 'none';
        });
      });
      item.addEventListener('mouseleave', function () {
        items.forEach(function (other) {
          var bg = other.querySelector('.rn-item-bg');
          if (bg) bg.style.display = 'none';
        });
      });
    });

    /* ── Close on Escape ── */
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mobileMenu && mobileMenu.classList.contains('open')) {
        mobileMenu.classList.remove('open');
        if (mobileToggle) mobileToggle.setAttribute('aria-expanded', 'false');
      }
    });

    /* ── Close on outside click ── */
    document.addEventListener('click', function (e) {
      if (mobileMenu && mobileMenu.classList.contains('open') && !navEl.contains(e.target)) {
        mobileMenu.classList.remove('open');
        if (mobileToggle) mobileToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      var nav = document.querySelector('.rn-nav');
      if (nav) initResizableNavbar(nav);
    });
  } else {
    var nav = document.querySelector('.rn-nav');
    if (nav) initResizableNavbar(nav);
  }

  window.initResizableNavbar = initResizableNavbar;
})();
