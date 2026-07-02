(function () {
  'use strict';

  var LOCATIONS_DATA = [];
  var LOCATION_ICONS = {
    'remote': '🌍',
    'bangalore': '📍',
    'bengaluru': '📍',
    'mumbai': '📍',
    'delhi': '📍',
    'pune': '📍',
    'hyderabad': '📍',
    'chennai': '📍',
    'kolkata': '📍',
    'gurgaon': '📍',
    'noida': '📍',
    'ahmedabad': '📍',
    'jaipur': '📍',
    'san francisco': '🌉',
    'new york': '🗽',
    'london': '🇬🇧',
    'berlin': '🇩🇪',
    'singapore': '🇸🇬',
    'sydney': '🇦🇺',
    'toronto': '🇨🇦',
    'dubai': '🇦🇪',
    'amsterdam': '🇳🇱',
    'paris': '🇫🇷',
    'india': '🇮🇳',
  };

  var DEFAULTS = [
    'Remote', 'Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad',
    'Chennai', 'Kolkata', 'Gurgaon', 'Noida', 'Ahmedabad', 'Jaipur',
    'San Francisco', 'New York', 'London', 'Berlin', 'Singapore',
    'Sydney', 'Toronto', 'Dubai', 'Amsterdam', 'Paris',
  ];

  function getIcon(loc) {
    var key = loc.toLowerCase().trim();
    for (var k in LOCATION_ICONS) {
      if (key.indexOf(k) !== -1 || k.indexOf(key) !== -1) return LOCATION_ICONS[k];
    }
    return '📍';
  }

  function initLocationDropdown(container) {
    var input = container.querySelector('.location-input');
    var dropdown = container.querySelector('.location-dropdown');
    var list = dropdown.querySelector('.location-dropdown-inner');

    if (!input || !dropdown || !list) return;

    var selectedValue = input.value;
    var currentHighlight = -1;

    function buildOptions(filter) {
      list.innerHTML = '';
      var filterLower = (filter || '').toLowerCase().trim();
      var matched = [];

      LOCATIONS_DATA.forEach(function (loc) {
        if (!filterLower || loc.toLowerCase().indexOf(filterLower) !== -1) {
          matched.push(loc);
        }
      });

      if (matched.length === 0 && filterLower) {
        var custom = filterLower.charAt(0).toUpperCase() + filterLower.slice(1);
        matched = [custom];
      }

      if (matched.length === 0) {
        list.innerHTML = '<div class="location-empty">No locations found</div>';
        return;
      }

      matched.forEach(function (loc, idx) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'location-option';
        if (loc === selectedValue) btn.classList.add('selected');
        btn.setAttribute('data-value', loc);
        btn.setAttribute('data-index', idx);

        var icon = document.createElement('span');
        icon.className = 'loc-icon';
        icon.textContent = getIcon(loc);

        var label = document.createElement('span');
        label.className = 'loc-label';
        if (filterLower) {
          var re = new RegExp('(' + filterLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
          label.innerHTML = loc.replace(re, '<em>$1</em>');
        } else {
          label.textContent = loc;
        }

        btn.appendChild(icon);
        btn.appendChild(label);
        list.appendChild(btn);

        btn.addEventListener('click', function () {
          selectLocation(this.getAttribute('data-value'));
        });
      });

      currentHighlight = -1;
    }

    function selectLocation(value) {
      selectedValue = value;
      input.value = value;
      closeDropdown();
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function openDropdown() {
      dropdown.classList.add('open');
    }

    function closeDropdown() {
      dropdown.classList.remove('open');
      currentHighlight = -1;
    }

    function highlightNext() {
      var opts = list.querySelectorAll('.location-option');
      if (opts.length === 0) return;
      currentHighlight = Math.min(currentHighlight + 1, opts.length - 1);
      highlightCurrent(opts);
    }

    function highlightPrev() {
      var opts = list.querySelectorAll('.location-option');
      if (opts.length === 0) return;
      currentHighlight = Math.max(currentHighlight - 1, 0);
      highlightCurrent(opts);
    }

    function highlightCurrent(opts) {
      opts.forEach(function (o) { o.classList.remove('highlighted'); });
      if (currentHighlight >= 0 && currentHighlight < opts.length) {
        opts[currentHighlight].classList.add('highlighted');
        opts[currentHighlight].scrollIntoView({ block: 'nearest' });
      }
    }

    input.addEventListener('focus', function () {
      buildOptions(input.value);
      openDropdown();
    });

    input.addEventListener('input', function () {
      buildOptions(input.value);
      if (!dropdown.classList.contains('open')) openDropdown();
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (!dropdown.classList.contains('open')) {
          buildOptions(input.value);
          openDropdown();
        } else {
          highlightNext();
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (dropdown.classList.contains('open')) highlightPrev();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        var opts = list.querySelectorAll('.location-option');
        if (currentHighlight >= 0 && currentHighlight < opts.length) {
          selectLocation(opts[currentHighlight].getAttribute('data-value'));
        } else if (input.value.trim()) {
          selectLocation(input.value.trim());
        }
      } else if (e.key === 'Escape') {
        closeDropdown();
      }
    });

    input.addEventListener('blur', function () {
      setTimeout(closeDropdown, 180);
    });

    document.addEventListener('click', function (e) {
      if (!container.contains(e.target)) closeDropdown();
    });

    buildOptions('');
  }

  function loadLocations(callback) {
    if (LOCATIONS_DATA.length > 0) {
      if (callback) callback(LOCATIONS_DATA);
      return;
    }
    var req = new XMLHttpRequest();
    req.open('GET', '/api/locations/', true);
    req.onload = function () {
      if (req.status === 200) {
        try {
          var data = JSON.parse(req.responseText);
          LOCATIONS_DATA = data.locations || [];
        } catch (e) {
          LOCATIONS_DATA = DEFAULTS.slice();
        }
      } else {
        LOCATIONS_DATA = DEFAULTS.slice();
      }
      if (callback) callback(LOCATIONS_DATA);
      initAllDropdowns();
    };
    req.onerror = function () {
      LOCATIONS_DATA = DEFAULTS.slice();
      if (callback) callback(LOCATIONS_DATA);
      initAllDropdowns();
    };
    req.send();
  }

  function initAllDropdowns() {
    document.querySelectorAll('.location-wrap').forEach(function (wrap) {
      if (wrap.dataset.dropdownInited) return;
      wrap.dataset.dropdownInited = '1';
      initLocationDropdown(wrap);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { loadLocations(); });
  } else {
    loadLocations();
  }

  window.initLocationDropdown = initLocationDropdown;
  window.loadLocationData = loadLocations;
})();
