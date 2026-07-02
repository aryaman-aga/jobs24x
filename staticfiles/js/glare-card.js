(function () {
  'use strict';

  function initGlareCards(container) {
    var cards = (container || document).querySelectorAll('.glare-card');
    cards.forEach(function (card) {
      var state = {
        glare: { x: 50, y: 50 },
        background: { x: 50, y: 50 },
        rotate: { x: 0, y: 0 },
      };
      var isInside = false;
      var resetTimer = null;

      function updateStyles() {
        card.style.setProperty('--m-x', state.glare.x + '%');
        card.style.setProperty('--m-y', state.glare.y + '%');
        card.style.setProperty('--r-x', state.rotate.x + 'deg');
        card.style.setProperty('--r-y', state.rotate.y + 'deg');
        card.style.setProperty('--bg-x', state.background.x + '%');
        card.style.setProperty('--bg-y', state.background.y + '%');
      }

      card.addEventListener('pointermove', function (e) {
        var rect = card.getBoundingClientRect();
        var pos = { x: e.clientX - rect.left, y: e.clientY - rect.top };
        var pct = { x: (100 / rect.width) * pos.x, y: (100 / rect.height) * pos.y };
        var delta = { x: pct.x - 50, y: pct.y - 50 };
        var rf = 0.4;

        state.background.x = 50 + pct.x / 4 - 12.5;
        state.background.y = 50 + pct.y / 3 - 16.67;
        state.rotate.x = -(delta.x / 3.5) * rf;
        state.rotate.y = (delta.y / 2) * rf;
        state.glare.x = pct.x;
        state.glare.y = pct.y;
        updateStyles();
      });

      card.addEventListener('pointerenter', function () {
        isInside = true;
        clearTimeout(resetTimer);
        setTimeout(function () {
          if (isInside) card.style.setProperty('--duration', '0s');
        }, 300);
      });

      card.addEventListener('pointerleave', function () {
        isInside = false;
        card.style.removeProperty('--duration');
        state.rotate.x = 0;
        state.rotate.y = 0;
        updateStyles();
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { initGlareCards(); });
  } else {
    initGlareCards();
  }

  window.initGlareCards = initGlareCards;
})();
