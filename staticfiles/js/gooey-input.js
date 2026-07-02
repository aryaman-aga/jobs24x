(function () {
  'use strict';

  function generateId() {
    return 'gooey-' + Math.random().toString(36).slice(2, 9);
  }

  function createFilter(id, blur) {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'gooey-svg');
    svg.setAttribute('aria-hidden', 'true');
    var defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    var filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
    filter.setAttribute('id', id);
    filter.setAttribute('x', '-50%');
    filter.setAttribute('y', '-50%');
    filter.setAttribute('width', '200%');
    filter.setAttribute('height', '200%');

    var blurEl = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
    blurEl.setAttribute('in', 'SourceGraphic');
    blurEl.setAttribute('stdDeviation', String(blur));
    blurEl.setAttribute('result', 'blur');

    var colorMatrix = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
    colorMatrix.setAttribute('in', 'blur');
    colorMatrix.setAttribute('type', 'matrix');
    colorMatrix.setAttribute('values', '1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 -10');
    colorMatrix.setAttribute('result', 'goo');

    var composite = document.createElementNS('http://www.w3.org/2000/svg', 'feComposite');
    composite.setAttribute('in', 'SourceGraphic');
    composite.setAttribute('in2', 'goo');
    composite.setAttribute('operator', 'atop');

    filter.appendChild(blurEl);
    filter.appendChild(colorMatrix);
    filter.appendChild(composite);
    defs.appendChild(filter);
    svg.appendChild(defs);
    return svg;
  }

  function SearchIcon() {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('class', 'gooey-icon');
    var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '11');
    circle.setAttribute('cy', '11');
    circle.setAttribute('r', '8');
    svg.appendChild(circle);
    var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'm21 21-4.3-4.3');
    svg.appendChild(path);
    return svg;
  }

  function GooeySearch(container, opts) {
    opts = opts || {};
    var id = generateId();
    var filterId = 'gooey-filter-' + id;
    var collapsedWidth = opts.collapsedWidth || 52;
    var expandedWidth = opts.expandedWidth || 260;
    var gooeyBlur = opts.gooeyBlur || 5;
    var placeholder = opts.placeholder || 'Search jobs, companies, keywords...';
    var actionUrl = opts.actionUrl || '/jobs/search/?q=';
    var self = this;
    var expanded = false;

    container.style.position = 'relative';

    var svgFilter = createFilter(filterId, gooeyBlur);
    container.appendChild(svgFilter);

    var wrap = document.createElement('div');
    wrap.className = 'gooey-wrap';

    var inner = document.createElement('div');
    inner.className = 'gooey-inner';
    inner.style.filter = 'url(#' + filterId + ')';

    var track = document.createElement('div');
    track.className = 'gooey-track';
    track.style.width = collapsedWidth + 'px';
    track.style.marginLeft = '0px';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'gooey-btn';
    if (opts.disabled) btn.disabled = true;

    var iconInBtn = SearchIcon();
    btn.appendChild(iconInBtn);

    var inputEl = document.createElement('input');
    inputEl.type = 'search';
    inputEl.className = 'gooey-input-el';
    inputEl.placeholder = placeholder;
    inputEl.autocomplete = 'off';
    inputEl.disabled = true;
    inputEl.style.display = 'none';
    btn.appendChild(inputEl);

    track.appendChild(btn);
    inner.appendChild(track);

    var bubble = document.createElement('div');
    bubble.className = 'gooey-bubble collapsed';
    var bubbleInner = document.createElement('div');
    bubbleInner.className = 'gooey-bubble-inner';
    var iconInBubble = SearchIcon();
    bubbleInner.appendChild(iconInBubble);
    bubble.appendChild(bubbleInner);
    inner.appendChild(bubble);

    wrap.appendChild(inner);
    container.appendChild(wrap);

    function expand() {
      if (opts.disabled) return;
      expanded = true;
      track.style.width = expandedWidth + 'px';
      track.style.marginLeft = '52px';
      inputEl.style.display = '';
      inputEl.disabled = false;
      setTimeout(function () { inputEl.focus(); }, 350);
      bubble.className = 'gooey-bubble expanded';
      if (opts.onOpen) opts.onOpen(true);
    }

    function collapse() {
      if (!inputEl.value && expanded) {
        expanded = false;
        track.style.width = collapsedWidth + 'px';
        track.style.marginLeft = '0px';
        inputEl.style.display = 'none';
        inputEl.disabled = true;
        bubble.className = 'gooey-bubble collapsed';
        if (opts.onOpen) opts.onOpen(false);
      }
    }

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (!expanded) expand();
    });

    inputEl.addEventListener('blur', function () {
      collapse();
    });

    inputEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && inputEl.value.trim()) {
        window.location.href = actionUrl + encodeURIComponent(inputEl.value.trim());
      }
      if (e.key === 'Escape') {
        inputEl.value = '';
        inputEl.blur();
        collapse();
      }
    });

    this.expand = expand;
    this.collapse = collapse;
    this.getValue = function () { return inputEl.value; };
    this.setValue = function (v) { inputEl.value = v; };
    this.destroy = function () {
      container.innerHTML = '';
    };
  }

  window.GooeySearch = GooeySearch;
})();
