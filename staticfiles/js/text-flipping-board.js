(function () {
  'use strict';

  var FLAP_CHARS = ' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$()-+&=;:\'\"%,./?°';
  var BOARD_ROWS = 6;
  var BOARD_COLS = 22;

  var ACCENTS = [
    { top: '#D32F2F', bottom: '#C62828' },
    { top: '#F57C00', bottom: '#E65100' },
    { top: '#FBC02D', bottom: '#F9A825' },
    { top: '#43A047', bottom: '#2E7D32' },
    { top: '#1E88E5', bottom: '#1565C0' },
    { top: '#8E24AA', bottom: '#6A1B9A' },
    { top: '#FAFAFA', bottom: '#F5F5F5' },
  ];

  var COLOR_MAP = {
    '{R}': '#D32F2F', '{O}': '#F57C00', '{Y}': '#FBC02D',
    '{G}': '#43A047', '{B}': '#1E88E5', '{V}': '#8E24AA', '{W}': '#FAFAFA',
  };

  function parseRow(row) {
    var cells = [];
    var i = 0;
    while (i < row.length) {
      if (row[i] === '{' && i + 2 < row.length && row[i + 2] === '}') {
        var code = row.substring(i, i + 3);
        if (COLOR_MAP[code]) {
          cells.push({ type: 'color', hex: COLOR_MAP[code] });
          i += 3; continue;
        }
      }
      cells.push({ type: 'char', value: row[i] });
      i++;
    }
    return cells;
  }

  function wrapText(text, maxCols) {
    var lines = [];
    var paragraphs = text.split('\n');
    for (var p = 0; p < paragraphs.length; p++) {
      var para = paragraphs[p].trim();
      if (!para) { lines.push(''); continue; }
      var words = para.split(/[ \t]+/).filter(Boolean);
      var current = '';
      for (var w = 0; w < words.length; w++) {
        var word = words[w];
        if (word.length > maxCols) {
          if (current) { lines.push(current); current = ''; }
          lines.push(word.slice(0, maxCols));
          continue;
        }
        if (!current) { current = word; }
        else if (current.length + 1 + word.length <= maxCols) { current += ' ' + word; }
        else { lines.push(current); current = word; }
      }
      if (current) lines.push(current);
    }
    return lines;
  }

  /* ── Cell ── */
  function FlapCell(container) {
    this.el = document.createElement('div');
    this.el.className = 'fb-cell';
    this.el.innerHTML =
      '<div class="fb-static-top"><span class="fb-flap-char"></span></div>' +
      '<div class="fb-static-bottom"><span class="fb-flap-char"></span></div>' +
      '<div class="fb-flap-top"><span class="fb-flap-char"></span><div class="fb-shine"></div></div>' +
      '<div class="fb-flap-bottom"><span class="fb-flap-char"></span><div class="fb-shine"></div></div>' +
      '<div class="fb-divider"></div>';

    this._staticTop = this.el.children[0].querySelector('.fb-flap-char');
    this._staticBottom = this.el.children[1].querySelector('.fb-flap-char');
    this._flapTop = this.el.children[2];
    this._flapBottom = this.el.children[3];
    this._flapTopChar = this._flapTop.querySelector('.fb-flap-char');
    this._flapBottomChar = this._flapBottom.querySelector('.fb-flap-char');
    this._flapTopShine = this._flapTop.querySelector('.fb-shine');
    this._flapBottomShine = this._flapBottom.querySelector('.fb-shine');
    this._timers = [];
    this._anims = [];
    this._busy = false;
    this._value = ' ';
    container.appendChild(this.el);
  }

  FlapCell.prototype.setValue = function (ch) {
    var d = ch === ' ' ? '\u00A0' : ch;
    this._staticTop.textContent = d;
    this._staticBottom.textContent = d;
    this._value = ch;
  };

  FlapCell.prototype.animateTo = function (target, delay, stepMs, flipDur) {
    if (this._busy) return;
    this._busy = true;

    var normalized = FLAP_CHARS.indexOf(target.toUpperCase()) >= 0
      ? target.toUpperCase() : ' ';

    var scrambleCount = normalized === ' '
      ? 8 + Math.floor(Math.random() * 8)
      : 25 + Math.floor(Math.random() * 15);

    var self = this;
    var stepIndex = 1;

    function runStep(i) {
      if (!self._busy) return;
      var isLast = i >= scrambleCount;
      var randChar = isLast
        ? normalized
        : FLAP_CHARS[1 + Math.floor(Math.random() * (FLAP_CHARS.length - 1))];
      self._doFlip(self._value, randChar, flipDur);
      self.setValue(randChar);
      if (!isLast) {
        self._timers.push(setTimeout(function () { runStep(i + 1); }, stepMs));
      } else {
        self._busy = false;
      }
    }

    this._timers.push(setTimeout(function () { runStep(1); }, delay));
  };

  FlapCell.prototype._doFlip = function (oldChar, newChar, flipDur) {
    var oldD = oldChar === ' ' ? '\u00A0' : oldChar;
    var newD = newChar === ' ' ? '\u00A0' : newChar;
    this._flapTopChar.textContent = oldD;
    this._flapBottomChar.textContent = newD;

    var accent = Math.random() < 0.2
      ? ACCENTS[Math.floor(Math.random() * ACCENTS.length)]
      : null;

    this._flapTop.style.display = '';
    this._flapBottom.style.display = '';
    if (accent) {
      this._flapTop.style.backgroundColor = accent.top;
      this._flapBottom.style.backgroundColor = accent.bottom;
    } else {
      this._flapTop.style.backgroundColor = '';
      this._flapBottom.style.backgroundColor = '';
    }

    this._cancelAnims();
    var bottomDelay = flipDur * 0.5;

    this._anims.push(this._flapTop.animate([
      { transform: 'rotateX(0deg)', offset: 0 },
      { transform: 'rotateX(-100deg)', offset: 1 }
    ], {
      duration: flipDur * 1000,
      easing: 'cubic-bezier(0.55, 0.055, 0.675, 0.19)',
      fill: 'forwards'
    }));

    this._anims.push(this._flapBottom.animate([
      { transform: 'rotateX(90deg)', offset: 0 },
      { transform: 'rotateX(0deg)', offset: 1 }
    ], {
      duration: flipDur * 0.85 * 1000,
      delay: bottomDelay * 1000,
      easing: 'cubic-bezier(0.33, 1.55, 0.64, 1)',
      fill: 'forwards'
    }));

    this._anims.push(this._flapTopShine.animate([
      { opacity: 0.5, offset: 0 },
      { opacity: 0, offset: 1 }
    ], {
      duration: flipDur * 1.3 * 1000,
      easing: 'ease-out',
      fill: 'forwards'
    }));

    this._anims.push(this._flapBottomShine.animate([
      { opacity: 0.4, offset: 0 },
      { opacity: 0, offset: 1 }
    ], {
      duration: flipDur * 0.85 * 1000,
      delay: bottomDelay * 1000,
      easing: 'ease-out',
      fill: 'forwards'
    }));

    var total = Math.max(flipDur * 1300, (flipDur * 0.85 + bottomDelay) * 1000);
    setTimeout(function () {
      self._flapTop.style.display = 'none';
      self._flapBottom.style.display = 'none';
    }, total);
  };

  var self;
  FlapCell.prototype._cancelAnims = function () {
    for (var i = 0; i < this._anims.length; i++) {
      if (this._anims[i]) this._anims[i].cancel();
    }
    this._anims = [];
  };

  FlapCell.prototype.destroy = function () {
    this._busy = false;
    for (var i = 0; i < this._timers.length; i++) clearTimeout(this._timers[i]);
    this._timers = [];
    this._cancelAnims();
    if (this.el.parentNode) this.el.parentNode.removeChild(this.el);
  };

  /* ── Color Cell ── */
  function ColorCell(container, hex) {
    this.el = document.createElement('div');
    this.el.className = 'fb-cell fb-color-cell';
    this.el.style.backgroundColor = hex;
    container.appendChild(this.el);
  }
  ColorCell.prototype.destroy = function () {
    if (this.el.parentNode) this.el.parentNode.removeChild(this.el);
  };

  /* ── Board ── */
  function FlapBoard(container, opts) {
    opts = opts || {};
    this._container = container;
    this._messages = opts.messages || [];
    this._interval = opts.interval || 6000;
    this._duration = opts.duration || 1.2;
    this._msgIdx = 0;
    this._timer = null;
    this._cells = [];

    var scale = this._duration / 1.2;
    this._colDelay = 30 * scale;
    this._rowDelay = 20 * scale;
    this._stepMs = Math.round(55 * scale);
    this._flipDur = Math.min(0.6, Math.max(0.15, 0.35 * scale));

    this._build();
  }

  FlapBoard.prototype._build = function () {
    this._boardEl = document.createElement('div');
    this._boardEl.className = 'fb-board';

    var grid = document.createElement('div');
    grid.className = 'fb-grid';
    grid.style.gridTemplateColumns = 'repeat(' + BOARD_COLS + ', 1fr)';
    this._boardEl.appendChild(grid);
    this._grid = grid;

    for (var r = 0; r < BOARD_ROWS; r++) {
      for (var c = 0; c < BOARD_COLS; c++) {
        this._cells.push(new FlapCell(grid));
      }
    }

    this._container.innerHTML = '';
    this._container.appendChild(this._boardEl);
  };

  FlapBoard.prototype._cellAt = function (r, c) {
    return this._cells[r * BOARD_COLS + c];
  };

  FlapBoard.prototype.showMessage = function (text) {
    var grid = [];
    for (var r = 0; r < BOARD_ROWS; r++) {
      grid[r] = [];
      for (var c = 0; c < BOARD_COLS; c++) {
        grid[r][c] = { type: 'char', value: ' ' };
      }
    }

    if (text) {
      var lines = wrapText(text, BOARD_COLS).slice(0, BOARD_ROWS);
      var startRow = Math.max(0, Math.floor((BOARD_ROWS - lines.length) / 2));
      for (var i = 0; i < lines.length; i++) {
        var row = startRow + i;
        if (row >= BOARD_ROWS) break;
        var parsed = parseRow(lines[i]);
        var startCol = Math.max(0, Math.floor((BOARD_COLS - parsed.length) / 2));
        for (var j = 0; j < parsed.length; j++) {
          if (startCol + j < BOARD_COLS) {
            grid[row][startCol + j] = parsed[j];
          }
        }
      }
    }

    for (var ri = 0; ri < BOARD_ROWS; ri++) {
      for (var ci = 0; ci < BOARD_COLS; ci++) {
        var cellDef = grid[ri][ci];
        var idx = ri * BOARD_COLS + ci;
        var existing = this._cells[idx];
        if (cellDef.type === 'color') {
          if (existing instanceof FlapCell) {
            existing.destroy();
            this._cells[idx] = new ColorCell(this._grid, cellDef.hex);
          }
        } else {
          if (existing instanceof ColorCell) {
            existing.destroy();
            var fc = new FlapCell(this._grid);
            fc.setValue(cellDef.value);
            this._cells[idx] = fc;
          } else if (existing instanceof FlapCell) {
            var delay = ci * this._colDelay + ri * this._rowDelay;
            existing.animateTo(cellDef.value, delay, this._stepMs, this._flipDur);
          }
        }
      }
    }
  };

  FlapBoard.prototype.start = function () {
    if (!this._messages.length) return;
    this._msgIdx = 0;
    this.showMessage(this._messages[0]);
    var self = this;
    this._timer = setInterval(function () {
      self._msgIdx = (self._msgIdx + 1) % self._messages.length;
      self.showMessage(self._messages[self._msgIdx]);
    }, this._interval);
  };

  FlapBoard.prototype.stop = function () {
    if (this._timer) { clearInterval(this._timer); this._timer = null; }
  };

  FlapBoard.prototype.destroy = function () {
    this.stop();
    for (var i = 0; i < this._cells.length; i++) this._cells[i].destroy();
    this._cells = [];
    if (this._boardEl && this._boardEl.parentNode) this._boardEl.parentNode.removeChild(this._boardEl);
  };

  /* ── Expose ── */
  window.FlapBoard = FlapBoard;
})();
