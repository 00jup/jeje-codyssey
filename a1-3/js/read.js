/*
 * 거부불가 — read.html(받는 사람 화면) 프론트엔드
 *
 * 편지를 불러와서(GET /api/letter) 보여주고, "거부" 버튼이 마우스/손가락이
 * 다가오면 도망가게 만든다. "수락"만 누를 수 있고, 그러면 편지가 공개된다.
 *
 * AI는 여기서 부르지 않는다 — 재치 대사는 편지를 지을 때 이미 같이 저장돼
 * 있어서, 도망갈 때마다 즉시(네트워크 없이) 하나씩 꺼내 쓴다.
 */
(function () {
  'use strict';

  var $ = function (s) { return document.querySelector(s); };
  function show(el) { el.hidden = false; }
  function hide(el) { el.hidden = true; }

  var stateLoading = $('#stateLoading');
  var stateMissing = $('#stateMissing');
  var stateArena = $('#stateArena');
  var stateReveal = $('#stateReveal');

  /* ── 마우스 반짝이 트레일 ─────────────────────────────────────────────
     페이지 전체에서 커서를 따라 반짝이가 튄다. 매 pointermove 마다 만들면
     너무 많아지므로 최소 간격을 둔다. */
  var SPARKLES = ['✨', '💫', '⭐', '🌟'];
  var lastSparkle = 0;
  function spawnSparkle(x, y) {
    var s = document.createElement('span');
    s.className = 'sparkle';
    s.textContent = SPARKLES[Math.floor(Math.random() * SPARKLES.length)];
    s.style.left = x + 'px';
    s.style.top = y + 'px';
    document.body.appendChild(s);
    s.addEventListener('animationend', function () { s.remove(); });
  }
  window.addEventListener('pointermove', function (e) {
    var now = Date.now();
    if (now - lastSparkle < 150) return; // 너무 자주 튀면 클릭하려는 자리를 가려 깜빡여 보인다
    lastSparkle = now;
    spawnSparkle(e.clientX, e.clientY);
  });
  function sparkleBurst(cx, cy, count) {
    for (var i = 0; i < count; i++) {
      (function (i) {
        setTimeout(function () {
          var angle = (Math.PI * 2 * i) / count;
          spawnSparkle(cx + Math.cos(angle) * 40, cy + Math.sin(angle) * 40);
        }, i * 30);
      })(i);
    }
  }

  function letterId() {
    return location.pathname.replace(/^\/+/, '').replace(/\/+$/, '');
  }

  function fetchLetter(id) {
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, 15000);
    return fetch('/api/letter?id=' + encodeURIComponent(id), { signal: ctrl.signal })
      .then(function (res) {
        return res.json().catch(function () { return {}; }).then(function (data) {
          if (res.ok && data.ok) return data.letter;
          throw new Error(data.message || '편지를 불러오지 못했습니다.');
        });
      })
      .finally(function () { clearTimeout(timer); });
  }

  /* ── 아레나: 거부 버튼 도망 게임 ──────────────────────────────────── */
  function setupArena(letter) {
    var arena = $('#arena');
    var acceptBtn = $('#acceptBtn');
    var declineBtn = $('#declineBtn');
    var tauntEl = $('#taunt');

    var taunts = (letter.taunts && letter.taunts.length) ? letter.taunts : ['그건 좀 곤란한데'];
    var attempt = 0;
    var lastMove = 0;
    var cooling = false;

    function nextTaunt() {
      var base = taunts[attempt % taunts.length];
      var prefix = attempt >= taunts.length ? '진짜 마지막이야: ' : '';
      tauntEl.textContent = prefix + base;
      show(tauntEl);
      // 같은 텍스트라도 다시 팝 애니메이션이 보이도록 리플레이한다.
      tauntEl.style.animation = 'none';
      void tauntEl.offsetWidth;
      tauntEl.style.animation = '';
      attempt++;
    }

    function place(x, y) {
      var rect = arena.getBoundingClientRect();
      // 버튼은 이 점을 중심으로 그려진다(translate(-50%,-50%)). 아레나가
      // overflow:hidden 이라, 절반 너비만큼 여유를 안 주면 가장자리에서 잘려 보인다.
      var padX = declineBtn.offsetWidth / 2 + 10;
      var padY = declineBtn.offsetHeight / 2 + 10;
      declineBtn.style.left = Math.max(padX, Math.min(rect.width - padX, x)) + 'px';
      declineBtn.style.top = Math.max(padY, Math.min(rect.height - padY, y)) + 'px';
    }

    function dodge(fromX, fromY) {
      var rect = arena.getBoundingClientRect();
      var acceptRect = acceptBtn.getBoundingClientRect();
      var centerX = acceptRect.left - rect.left + acceptRect.width / 2;
      var centerY = acceptRect.top - rect.top + acceptRect.height / 2;

      var best = null;
      for (var i = 0; i < 8; i++) {
        var x = 50 + Math.random() * Math.max(1, rect.width - 100);
        var y = 40 + Math.random() * Math.max(1, rect.height - 80);
        var dCenter = Math.hypot(x - centerX, y - centerY);
        var dCursor = fromX == null ? Infinity : Math.hypot(x - fromX, y - fromY);
        if (dCenter < 130) continue; // 수락 버튼 근처에 자꾸 붙으면, 다가갈 때마다 재도망가며 깜빡여 보인다
        if (!best || dCursor > best.dCursor) best = { x: x, y: y, dCursor: dCursor };
      }
      if (!best) best = { x: rect.width * 0.7, y: rect.height * 0.75 };
      place(best.x, best.y);
      nextTaunt();
    }

    function tryDodge(clientX, clientY) {
      var now = Date.now();
      if (cooling && now - lastMove < 260) return;
      var rect = declineBtn.getBoundingClientRect();
      var cx = rect.left + rect.width / 2;
      var cy = rect.top + rect.height / 2;
      var dist = Math.hypot(clientX - cx, clientY - cy);
      var threshold = Math.max(rect.width, rect.height) * 0.9 + 40;
      if (dist < threshold) {
        var arenaRect = arena.getBoundingClientRect();
        dodge(clientX - arenaRect.left, clientY - arenaRect.top);
        lastMove = now;
        cooling = true;
      }
    }

    arena.addEventListener('pointermove', function (e) { tryDodge(e.clientX, e.clientY); });
    declineBtn.addEventListener('pointerdown', function (e) {
      e.preventDefault();
      dodge(null, null); // 어쩌다 손이 닿아도 즉시 다시 도망간다
    });
    declineBtn.addEventListener('click', function (e) { e.preventDefault(); });

    acceptBtn.addEventListener('click', function (e) {
      sparkleBurst(e.clientX, e.clientY, 10);
      setTimeout(function () { reveal(letter); }, 180);
    });

    // 처음부터 정중앙 겹침을 피해 살짝 아래쪽에 자리 잡는다.
    requestAnimationFrame(function () { dodge(null, null); tauntEl.hidden = true; attempt = 0; });
  }

  /* ── 공개 ─────────────────────────────────────────────────────────── */
  function reveal(letter) {
    hide(stateArena);
    $('#revealTitle').textContent = letter.title;
    $('#revealTo').textContent = '💌 To. ' + letter.receiverName;
    $('#revealFrom').textContent = '✍️ From. ' + letter.senderName;
    if (letter.location) {
      var where = $('#revealWhere');
      where.textContent = letter.location;
      show(where);
    }
    $('#revealBody').textContent = letter.body;
    if (window.Geobulga && letter.decorations && letter.decorations.length) {
      window.Geobulga.renderDecoLayer($('.letter-card'), letter.decorations, false);
    }
    show(stateReveal);
  }

  /* ── 시작 ─────────────────────────────────────────────────────────── */
  var id = letterId();
  if (!/^[a-z0-9][a-z0-9-]{1,18}[a-z0-9]$/.test(id)) {
    hide(stateLoading);
    show(stateMissing);
    return;
  }

  fetchLetter(id)
    .then(function (letter) {
      hide(stateLoading);
      $('#arenaFrom').textContent =
        '✨ ' + letter.senderName + ' ✨ 님이 ✨ ' + letter.receiverName + ' ✨ 님에게 보냈습니다.';
      $('#arenaTitle').textContent = letter.title;
      show(stateArena);
      setupArena(letter);
    })
    .catch(function () {
      hide(stateLoading);
      show(stateMissing);
    });
})();
