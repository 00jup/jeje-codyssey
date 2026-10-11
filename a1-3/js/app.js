/*
 * 거부불가 — index.html(홈/편지 만들기/사용법/소개) 프론트엔드
 *
 * 하는 일: 해시 라우팅, 테마 기억, 글자 수, 편지 짓기 폼 → fetch → 결과 렌더, 복사.
 * 하지 않는 일: AI 키를 아는 것. 키는 서버리스 함수만 안다.
 */
(function () {
  'use strict';

  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  var toastEl = $('#toast');
  var toastTimer;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.hidden = false;
    requestAnimationFrame(function () { toastEl.classList.add('show'); });
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toastEl.classList.remove('show');
      setTimeout(function () { toastEl.hidden = true; }, 250);
    }, 1800);
  }

  /* ── 라우팅 ───────────────────────────────────────────────────────────
     한 번에 한 섹션만 보인다. 주소 그대로 공유하면 같은 화면이 열린다. */
  var PAGES = ['home', 'compose', 'guide', 'about'];

  function show(name, push) {
    if (PAGES.indexOf(name) < 0) name = 'home';

    $$('.page').forEach(function (p) { p.hidden = p.dataset.page !== name; });
    $$('[data-nav]').forEach(function (a) {
      if (a.dataset.nav === name) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });

    var title = { home: '', compose: '편지 만들기', guide: '사용법', about: '소개' }[name];
    document.title = (title ? title + ' · ' : '') + '거부불가';

    if (push && location.hash !== '#' + name) history.pushState(null, '', '#' + name);
    closeMenu();
    window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
  }

  function currentHash() { return (location.hash || '#home').slice(1); }

  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[data-nav]');
    if (!a) return;
    e.preventDefault();
    show(a.dataset.nav, true);
  });

  window.addEventListener('popstate', function () { show(currentHash(), false); });

  /* ── 모바일 메뉴 ──────────────────────────────────────────────────── */
  var menuBtn = $('#menuBtn');
  var mobileNav = $('#mobileNav');

  function closeMenu() {
    menuBtn.setAttribute('aria-expanded', 'false');
    mobileNav.hidden = true;
  }
  menuBtn.addEventListener('click', function () {
    var open = menuBtn.getAttribute('aria-expanded') === 'true';
    menuBtn.setAttribute('aria-expanded', String(!open));
    mobileNav.hidden = open;
  });
  window.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });

  /* ── 테마 ─────────────────────────────────────────────────────────────
     자동 → 라이트 → 다크 순환. 고른 값만 저장하고, 자동이면 지운다. */
  var THEMES = ['auto', 'light', 'dark'];
  var LABEL = { auto: '자동', light: '라이트', dark: '다크' };
  var themeBtn = $('#themeBtn');
  var themeLabel = $('[data-theme-label]');

  function applyTheme(v) {
    document.documentElement.setAttribute('data-theme', v);
    themeLabel.textContent = LABEL[v];
    try {
      if (v === 'auto') localStorage.removeItem('geobulga-theme');
      else localStorage.setItem('geobulga-theme', v);
    } catch (_) { /* 프라이빗 모드에서 막힐 수 있다. 기능을 죽이진 않는다. */ }
  }

  themeBtn.addEventListener('click', function () {
    var now = document.documentElement.getAttribute('data-theme') || 'auto';
    applyTheme(THEMES[(THEMES.indexOf(now) + 1) % THEMES.length]);
  });

  /* ── 글자 수 ──────────────────────────────────────────────────────── */
  $$('[data-count]').forEach(function (out) {
    var input = document.getElementById(out.dataset.count);
    if (!input) return;
    var max = Number(input.getAttribute('maxlength')) || 0;
    var update = function () {
      out.textContent = String(input.value.length);
      if (max) out.parentNode.classList.toggle('over', input.value.length >= max);
    };
    input.addEventListener('input', update);
    update();
  });

  /* ── 서버 호출 ────────────────────────────────────────────────────────
     실패 세 갈래를 전부 사람 말로 바꾼다:
       1) 빈 입력 — 보내기 전에 막는다
       2) API 오류(4xx/5xx) — 서버가 준 message 를 그대로 쓴다
       3) 지연/타임아웃 — AbortController 로 끊고 안내한다 */
  var TIMEOUT_MS = 30000;

  function postJSON(url, body) {
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, TIMEOUT_MS);

    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: ctrl.signal
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (res.ok && data.ok) return data;
        var e = new Error(data.message ||
          (res.status >= 500
            ? '서버가 응답하지 못했습니다. 잠시 후 다시 시도해 주세요.'
            : '요청을 처리하지 못했습니다. 입력을 확인해 주세요.'));
        e.code = data.code || ('HTTP_' + res.status);
        throw e;
      });
    }).catch(function (err) {
      if (err.name === 'AbortError') {
        var t = new Error('응답이 30초를 넘겼습니다. 잠시 후 다시 시도해 주세요.');
        t.code = 'TIMEOUT';
        throw t;
      }
      if (err.code) throw err;
      var n = new Error('네트워크에 연결하지 못했습니다. 연결 상태를 확인해 주세요.');
      n.code = 'NETWORK';
      throw n;
    }).finally(function () { clearTimeout(timer); });
  }

  /* ── 결과 그리기 ──────────────────────────────────────────────────── */
  function skeleton(box, lines) {
    box.textContent = '';
    var sk = el('div', 'skeleton');
    for (var i = 0; i < lines; i++) {
      sk.appendChild(el('div', 'sk-line' + (i % 3 === 2 ? ' short' : '')));
    }
    box.appendChild(sk);
  }

  function fail(box, err) {
    box.textContent = '';
    var a = el('div', 'alert');
    a.appendChild(el('strong', null, '만들지 못했습니다'));
    a.appendChild(el('span', null, err.message));
    box.appendChild(a);
  }

  function copyBtn(getText, label) {
    var b = el('button', 'copy', label || '복사');
    b.type = 'button';
    b.addEventListener('click', function () {
      var text = getText();
      var done = function () {
        toast('복사했습니다');
        var prev = b.textContent;
        b.textContent = '복사됨';
        setTimeout(function () { b.textContent = prev; }, 1500);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, function () { legacy(text, done); });
      } else { legacy(text, done); }
    });
    return b;
  }

  // http 로 열었거나 권한이 없으면 Clipboard API 가 없다. 그때도 복사는 되게 한다.
  function legacy(text, done) {
    var ta = el('textarea');
    ta.value = text;
    ta.style.cssText = 'position:fixed;opacity:0;pointer-events:none';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); done(); }
    catch (_) { toast('복사에 실패했습니다'); }
    document.body.removeChild(ta);
  }

  /* ── 편지지 꾸미기: 스티커 · 사진 ─────────────────────────────────────
     스티커는 이름(id)만 서버로 보낸다 — 그림은 read.html 도 같은
     js/stickers.js 를 갖고 있어서 그때 그려진다. 사진만 base64 로 실제
     담아 보낸다. 업로드 즉시 캔버스로 줄여서(가로 640px, JPEG) 편지가
     너무 무거워지지 않게 한다. */
  var decorations = [];
  var MAX_DECOS = 6;
  var MAX_PHOTOS = 2;
  var PHOTO_MAX_EDGE = 640;

  var decoCanvas = $('#decoCanvas');
  var decoPalette = $('#decoPalette');
  var photoInput = $('#photoInput');

  function redrawDeco() {
    if (window.Geobulga) window.Geobulga.renderDecoLayer(decoCanvas, decorations, true, redrawDeco);
  }

  if (window.Geobulga && decoPalette) {
    window.Geobulga.STICKER_ORDER.forEach(function (id) {
      var b = el('button', 'deco-sticker-btn');
      b.type = 'button';
      b.innerHTML = window.Geobulga.STICKERS[id];
      b.setAttribute('aria-label', id + ' 스티커 추가');
      b.addEventListener('click', function () {
        if (decorations.length >= MAX_DECOS) { toast('스티커·사진은 최대 ' + MAX_DECOS + '개까지'); return; }
        decorations.push({
          kind: 'sticker', src: id,
          x: 30 + Math.random() * 40, y: 30 + Math.random() * 40,
          scale: 1, rotation: Math.round(Math.random() * 20 - 10)
        });
        redrawDeco();
      });
      decoPalette.appendChild(b);
    });

    var photoBtn = el('button', 'deco-photo-btn', '📷');
    photoBtn.type = 'button';
    photoBtn.setAttribute('aria-label', '사진 추가');
    photoBtn.addEventListener('click', function () { photoInput.click(); });
    decoPalette.appendChild(photoBtn);
  }

  photoInput.addEventListener('change', function () {
    var file = photoInput.files[0];
    photoInput.value = '';
    if (!file) return;
    var photoCount = decorations.filter(function (d) { return d.kind === 'photo'; }).length;
    if (photoCount >= MAX_PHOTOS) { toast('사진은 최대 ' + MAX_PHOTOS + '장까지'); return; }
    if (decorations.length >= MAX_DECOS) { toast('스티커·사진은 최대 ' + MAX_DECOS + '개까지'); return; }

    var img = new Image();
    var reader = new FileReader();
    reader.onload = function () { img.src = reader.result; };
    img.onload = function () {
      var scale = Math.min(1, PHOTO_MAX_EDGE / Math.max(img.width, img.height));
      var w = Math.round(img.width * scale), h = Math.round(img.height * scale);
      var cv = document.createElement('canvas');
      cv.width = w; cv.height = h;
      cv.getContext('2d').drawImage(img, 0, 0, w, h);
      decorations.push({
        kind: 'photo', src: cv.toDataURL('image/jpeg', .82),
        x: 50, y: 50, scale: 1.6, rotation: Math.round(Math.random() * 10 - 5)
      });
      redrawDeco();
    };
    reader.readAsDataURL(file);
  });

  /* ── 편지 만들기 ──────────────────────────────────────────────────── */
  var form = $('#composeForm');
  var box = $('#composeResult');
  var btn = $('[data-submit]', form);
  var busy = false;

  form.addEventListener('input', function (e) { e.target.removeAttribute('aria-invalid'); });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (busy) return;

    var required = [
      ['#receiverName', '받는 사람 이름을 입력해 주세요.'],
      ['#senderName', '보내는 사람 이름을 입력해 주세요.'],
      ['#note', '무슨 얘기인지 적어 주세요.']
    ];
    for (var i = 0; i < required.length; i++) {
      var input = $(required[i][0]);
      if (!input.value.trim()) {
        input.setAttribute('aria-invalid', 'true');
        input.focus();
        box.textContent = '';
        var a = el('div', 'alert');
        a.appendChild(el('strong', null, '입력이 필요합니다'));
        a.appendChild(el('span', null, required[i][1]));
        box.appendChild(a);
        return;
      }
      input.removeAttribute('aria-invalid');
    }

    busy = true;
    var label = btn.textContent;
    btn.disabled = true;
    btn.textContent = '';
    btn.appendChild(el('span', 'spin'));
    btn.appendChild(el('span', null, '짓는 중…'));
    skeleton(box, 5);

    var payload = {
      situation: $('#situation').value,
      receiverName: $('#receiverName').value,
      senderName: $('#senderName').value,
      location: $('#location').value,
      note: $('#note').value,
      tone: $('#tone').value,
      provider: $('#provider').value,
      customId: $('#customId').value,
      decorations: decorations
    };

    postJSON('/api/compose', payload)
      .then(function (data) { renderResult(box, data); })
      .catch(function (err) {
        fail(box, err);
        if (err.code === 'ID_TAKEN' || err.code === 'RESERVED_ID' || err.code === 'BAD_CUSTOM_ID') {
          $('#customId').setAttribute('aria-invalid', 'true');
          $('#customId').focus();
        }
      })
      .finally(function () {
        busy = false;
        btn.disabled = false;
        btn.textContent = label;
      });
  });

  var linkPrefix = $('#linkPrefix');
  if (linkPrefix) linkPrefix.textContent = location.host + '/';

  function renderResult(box, data) {
    box.textContent = '';
    var letter = data.letter;
    var url = location.origin + '/' + data.id;

    var preview = el('div', 'letter-preview');
    preview.appendChild(el('h3', null, letter.title));
    var meta = 'To. ' + letter.receiverName + '  ·  From. ' + letter.senderName +
      (letter.location ? '  ·  ' + letter.location : '');
    preview.appendChild(el('p', 'meta', meta));
    preview.appendChild(el('div', 'body', letter.body));
    box.appendChild(preview);

    var linkBox = el('div', 'link-box');
    linkBox.appendChild(el('code', null, url));
    linkBox.appendChild(copyBtn(function () { return url; }, '링크 복사'));
    box.appendChild(linkBox);

    var links = el('div', 'result-links');
    var preview2 = el('a', 'btn btn-ghost');
    preview2.href = '/' + data.id;
    preview2.target = '_blank';
    preview2.rel = 'noopener';
    preview2.textContent = '받는 사람 화면 미리보기';
    links.appendChild(preview2);
    box.appendChild(links);

    var note = el('div', 'note');
    note.appendChild(el('strong', null, '마음에 안 든다면 · '));
    var noteMsg = '위 "편지 만들기"를 다시 누르면 새로 짓는다.';
    if (letter.decorations && letter.decorations.length) {
      noteMsg += ' 꾸민 스티커/사진 ' + letter.decorations.length + '개는 그대로 유지된다.';
    }
    note.appendChild(el('span', null, noteMsg));
    box.appendChild(note);
  }

  /* ── 시작 ─────────────────────────────────────────────────────────── */
  var saved = null;
  try { saved = localStorage.getItem('geobulga-theme'); } catch (_) {}
  applyTheme(saved === 'light' || saved === 'dark' ? saved : 'auto');
  show(currentHash(), false);
})();
