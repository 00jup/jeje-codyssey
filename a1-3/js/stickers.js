/*
 * 거부불가 — 스티커 정의 + 꾸밈 레이어 렌더러
 *
 * index.html(꾸미기 UI)과 read.html(공개된 편지) 양쪽이 이 파일을 그대로
 * 불러 쓴다. 스티커는 서버로 이름(id)만 보내고 저장한다 — 그림 자체는
 * 두 페이지에 이미 있는 이 목록에서 그때그때 그려서, 편지마다 SVG 를
 * 중복 저장하지 않는다. 사진만 base64 로 실제 저장된다.
 */
(function (global) {
  'use strict';

  var STICKERS = {
    heart:   '<svg viewBox="0 0 24 24"><path fill="#ff5c8a" d="M12 21s-7.5-4.6-10-9.3C.4 8.4 2 5 5.4 5c2 0 3.4 1.1 4.1 2.3C10.2 6.1 11.6 5 13.6 5 17 5 18.6 8.4 17 11.7 14.5 16.4 12 21 12 21z"/></svg>',
    star:    '<svg viewBox="0 0 24 24"><path fill="#ffce3b" d="M12 2l2.9 6.6 7.1.6-5.4 4.7 1.7 7-6.3-3.9L5.7 21l1.7-7-5.4-4.7 7.1-.6z"/></svg>',
    sparkle: '<svg viewBox="0 0 24 24"><path fill="#8ad0ff" d="M12 2c.6 4.4 2.4 6.2 6.8 6.8-4.4.6-6.2 2.4-6.8 6.8-.6-4.4-2.4-6.2-6.8-6.8C9.6 8.2 11.4 6.4 12 2z"/><path fill="#d6b3ff" d="M19 15c.3 1.9 1 2.6 2.9 2.9-1.9.3-2.6 1-2.9 2.9-.3-1.9-1-2.6-2.9-2.9 1.9-.3 2.6-1 2.9-2.9z"/></svg>',
    ribbon:  '<svg viewBox="0 0 24 24"><path fill="#ff5c8a" d="M12 12 3 6v4l6 2-6 2v4l9-6z"/><path fill="#ff8fb3" d="M12 12l9-6v4l-6 2 6 2v4l-9-6z"/><circle cx="12" cy="12" r="2.4" fill="#fff"/></svg>',
    crown:   '<svg viewBox="0 0 24 24"><path fill="#ffce3b" d="M3 8l4 3 5-6 5 6 4-3-2 10H5L3 8z"/></svg>',
    flame:   '<svg viewBox="0 0 24 24"><path fill="#ff8a3d" d="M12 2c1 3-3 4-3 8a3 3 0 0 0 6 0c1.4 1 2 2.6 2 4a5 5 0 0 1-10 0c0-4 3-5 3-8 0-1.4.7-2.8 2-4z"/></svg>',
    cloud:   '<svg viewBox="0 0 24 24"><path fill="#bfe3ff" d="M7 18a4 4 0 0 1-.6-7.95A5 5 0 0 1 16 8a4.5 4.5 0 0 1 1 8.9V18H7z"/></svg>',
    balloon: '<svg viewBox="0 0 24 24"><ellipse cx="12" cy="9" rx="6" ry="7" fill="#ff9ad1"/><path fill="#ff9ad1" d="M12 16l-1.5 3 1.5 1 1.5-1z"/></svg>'
  };
  var STICKER_ORDER = ['heart', 'star', 'sparkle', 'ribbon', 'crown', 'flame', 'cloud', 'balloon'];

  /**
   * 꾸밈 레이어를 그린다. interactive 가 true 면 드래그·삭제가 붙는다
   * (편지 만들기 화면), false 면 정적으로만 배치한다(공개된 편지 화면).
   */
  function renderDecoLayer(container, decorations, interactive, onChange) {
    container.querySelectorAll('.deco-item').forEach(function (n) { n.remove(); });

    decorations.forEach(function (deco) {
      var el = document.createElement('div');
      el.className = 'deco-item';
      el.style.left = deco.x + '%';
      el.style.top = deco.y + '%';
      el.style.setProperty('--deco-scale', deco.scale);
      el.style.setProperty('--deco-rot', deco.rotation + 'deg');
      el.style.setProperty('--deco-x', deco.x); // 둥둥 뜨는 타이밍을 자리마다 어긋나게 하는 데만 쓴다(단위 없음)

      if (deco.kind === 'photo') {
        var img = document.createElement('img');
        img.src = deco.src;
        img.alt = '';
        img.draggable = false;
        el.appendChild(img);
      } else {
        el.innerHTML += STICKERS[deco.src] || '';
      }

      if (interactive) {
        var del = document.createElement('button');
        del.type = 'button';
        del.className = 'deco-del';
        del.textContent = '×';
        del.setAttribute('aria-label', '이 꾸밈 지우기');
        del.addEventListener('pointerdown', function (e) { e.stopPropagation(); });
        del.addEventListener('click', function (e) {
          e.stopPropagation();
          var i = decorations.indexOf(deco);
          if (i >= 0) decorations.splice(i, 1);
          renderDecoLayer(container, decorations, interactive, onChange);
          if (onChange) onChange();
        });
        el.appendChild(del);
        wireDrag(el, container, deco, onChange);
      }

      container.appendChild(el);
    });
  }

  function wireDrag(el, container, deco, onChange) {
    el.addEventListener('pointerdown', function (e) {
      el.setPointerCapture(e.pointerId);
      el.classList.add('dragging');
      var move = function (ev) {
        var rect = container.getBoundingClientRect();
        var x = ((ev.clientX - rect.left) / rect.width) * 100;
        var y = ((ev.clientY - rect.top) / rect.height) * 100;
        deco.x = Math.max(4, Math.min(96, x));
        deco.y = Math.max(4, Math.min(96, y));
        el.style.left = deco.x + '%';
        el.style.top = deco.y + '%';
      };
      var up = function () {
        el.classList.remove('dragging');
        el.removeEventListener('pointermove', move);
        el.removeEventListener('pointerup', up);
        if (onChange) onChange();
      };
      el.addEventListener('pointermove', move);
      el.addEventListener('pointerup', up);
    });
  }

  global.Geobulga = { STICKERS: STICKERS, STICKER_ORDER: STICKER_ORDER, renderDecoLayer: renderDecoLayer };
})(window);
