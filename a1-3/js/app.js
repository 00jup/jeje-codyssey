/*
 * 타래공방 — 프론트엔드
 *
 * 하는 일: 해시 라우팅, 테마 기억, 글자 수, 폼 → fetch → 화면 반영, 복사.
 * 하지 않는 일: API 키를 아는 것. 키는 서버리스 함수만 안다 — 프론트가 키를 들고
 * 있으면 브라우저 개발자 도구에서 그대로 읽힌다.
 */
(function () {
  'use strict';

  /* ── 작은 도구 ────────────────────────────────────────────────────── */
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
     한 번에 한 섹션만 보인다. 스크롤 앵커가 아니라 진짜 화면 전환이라
     주소를 그대로 공유하면 같은 화면이 열린다. */
  var PAGES = ['home', 'draft', 'reply', 'guide', 'about'];

  function show(name, push) {
    if (PAGES.indexOf(name) < 0) name = 'home';

    $$('.page').forEach(function (p) { p.hidden = p.dataset.page !== name; });
    $$('[data-nav]').forEach(function (a) {
      if (a.dataset.nav === name) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });

    var title = { home: '', draft: '타래 짓기', reply: '답글 짓기',
                  guide: '사용법', about: '소개' }[name];
    document.title = (title ? title + ' · ' : '') + '타래공방';

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
      if (v === 'auto') localStorage.removeItem('tarae-theme');
      else localStorage.setItem('tarae-theme', v);
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
  var TIMEOUT_MS = 25000;

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
        var t = new Error('응답이 25초를 넘겼습니다. 소재를 조금 줄이거나 잠시 후 다시 시도해 주세요.');
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

  function copyBtn(getText) {
    var b = el('button', 'copy', '복사');
    b.type = 'button';
    b.addEventListener('click', function () {
      var text = getText();
      var done = function () { toast('복사했습니다'); b.textContent = '복사됨'; 
        setTimeout(function () { b.textContent = '복사'; }, 1500); };
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

  function pieceCard(no, total, text, limit) {
    var card = el('article', 'piece');
    card.style.animationDelay = (no - 1) * 60 + 'ms';

    var head = el('div', 'piece-head');
    head.appendChild(el('span', 'piece-no', no + ' / ' + total));
    head.appendChild(copyBtn(function () { return text; }));

    var len = el('span', 'piece-len', text.length + ' / ' + limit);
    if (text.length > limit * 0.9) len.classList.add('tight');
    head.appendChild(len);

    card.appendChild(head);
    card.appendChild(el('div', 'piece-body', text));
    return card;
  }

  /* ── 타래 짓기 ────────────────────────────────────────────────────── */
  wireForm({
    form: '#draftForm',
    box: '#draftResult',
    required: [['#topic', '오늘 할 이야기를 한 줄이라도 적어 주세요.']],
    skeletonLines: 5,
    payload: function () {
      return {
        topic: $('#topic').value,
        audience: $('#audience').value,
        tone: $('#tone').value,
        count: $('#count').value,
        hashtags: $('#hashtags').checked
      };
    },
    url: '/api/draft',
    render: function (box, data) {
      box.textContent = '';
      var limit = data.limit || 500;

      data.pieces.forEach(function (t, i) {
        box.appendChild(pieceCard(i + 1, data.pieces.length, t, limit));
      });

      if (data.pieces.length > 1) {
        var all = el('div', 'piece');
        var h = el('div', 'piece-head');
        h.appendChild(el('span', 'piece-no', '전체'));
        h.appendChild(copyBtn(function () { return data.pieces.join('\n\n---\n\n'); }));
        all.appendChild(h);
        all.appendChild(el('div', 'piece-body', '조각 ' + data.pieces.length + '개를 한 번에 복사한다.'));
        box.appendChild(all);
      }

      if (data.hashtags && data.hashtags.length) {
        var tags = el('div', 'tags');
        data.hashtags.forEach(function (t) { tags.appendChild(el('span', null, t)); });
        box.appendChild(tags);
      }

      if (data.hookReason) {
        var note = el('div', 'note');
        note.appendChild(el('strong', null, '첫 문장을 이렇게 연 이유 · '));
        note.appendChild(el('span', null, data.hookReason));
        box.appendChild(note);
      }
    }
  });

  /* ── 답글 짓기 ────────────────────────────────────────────────────── */
  wireForm({
    form: '#replyForm',
    box: '#replyResult',
    required: [['#comment', '답할 댓글을 붙여 넣어 주세요.']],
    skeletonLines: 4,
    payload: function () {
      return {
        post: $('#post').value,
        comment: $('#comment').value,
        intent: $('#intent').value,
        tone: $('#replyTone').value
      };
    },
    url: '/api/reply',
    render: function (box, data) {
      box.textContent = '';

      var meta = el('div', 'tags');
      var kind = el('span', 'badge', data.kind);
      kind.setAttribute('data-kind', data.kind);
      meta.appendChild(kind);
      if (data.language) meta.appendChild(el('span', null, data.language + '로 씀'));
      box.appendChild(meta);

      [['짧은 답', data.short], ['자세한 답', data.long]].forEach(function (pair, i) {
        var card = el('article', 'piece');
        card.style.animationDelay = i * 60 + 'ms';
        var head = el('div', 'piece-head');
        head.appendChild(el('span', 'piece-no', pair[0]));
        head.appendChild(copyBtn(function () { return pair[1]; }));
        head.appendChild(el('span', 'piece-len', pair[1].length + '자'));
        card.appendChild(head);
        card.appendChild(el('div', 'piece-body', pair[1]));
        box.appendChild(card);
      });

      var note = el('div', 'note');
      note.appendChild(el('strong', null, '올리기 전에 · '));
      note.appendChild(el('span', null,
        data.caution || '초안이다. 사실 관계를 직접 확인하고 올린다.'));
      box.appendChild(note);
    }
  });

  /* ── 폼 배선 ───────────────────────────────────────────────────────── */
  function wireForm(cfg) {
    var form = $(cfg.form);
    if (!form) return;
    var box = $(cfg.box);
    var btn = $('[data-submit]', form);
    var busy = false;

    // 사용자가 고치기 시작하면 오류 표시를 지운다.
    form.addEventListener('input', function (e) {
      e.target.removeAttribute('aria-invalid');
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (busy) return;

      // 1) 빈 입력 — 서버까지 가지 않는다
      for (var i = 0; i < cfg.required.length; i++) {
        var input = $(cfg.required[i][0]);
        if (!input.value.trim()) {
          input.setAttribute('aria-invalid', 'true');
          input.focus();
          box.textContent = '';
          var a = el('div', 'alert');
          a.appendChild(el('strong', null, '입력이 필요합니다'));
          a.appendChild(el('span', null, cfg.required[i][1]));
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
      btn.appendChild(el('span', null, '만드는 중…'));
      skeleton(box, cfg.skeletonLines);

      postJSON(cfg.url, cfg.payload())
        .then(function (data) { cfg.render(box, data); })
        .catch(function (err) { fail(box, err); })
        .finally(function () {
          busy = false;
          btn.disabled = false;
          btn.textContent = label;
        });
    });
  }

  /* ── 시작 ─────────────────────────────────────────────────────────── */
  var saved = null;
  try { saved = localStorage.getItem('tarae-theme'); } catch (_) {}
  applyTheme(saved === 'light' || saved === 'dark' ? saved : 'auto');
  show(currentHash(), false);
})();
