// demo.js — 덱 안의 테트리스 데모. 템플릿의 __demo 틀에 붙는다.
// 글루(wasm/web/tetris.js)와 .wasm(base64)은 build.py 가 바로 앞에 싣는다.
(function () {
  'use strict';

  // 모듈 컴파일은 한 번만 — 데모가 여럿이어도 인스턴스만 따로 만든다
  let modP = null;
  function wasmModule() {
    if (!modP) {
      const bin = atob(window.__TT_WASM);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      modP = WebAssembly.compile(bytes);
    }
    return modP;
  }

  // 지금 키보드·게임패드를 쥔 데모. 쥐고 있는 동안만 키를 가로챈다.
  let owner = null;
  addEventListener('keydown', function (e) {
    if (!owner) return;
    if (!owner.visible()) { owner.release(); return; }
    const k = e.key;
    if (k !== 'q' && k !== 'Q' && !(k in RustTetris.KEYS)) return;
    // 캡처 단계에서 멈춰야 덱 엔진(←→·Space 로 페이지 넘김)까지 가지 않는다
    e.preventDefault();
    e.stopPropagation();
    if (k === 'q' || k === 'Q') { owner.release(); return; }
    const name = RustTetris.keyName(e); // 반복 이벤트는 이동만 통과
    if (name) owner.press(name);
  }, true);

  __demo('tetris', function (host, api) {
    const canvas = host.querySelector('canvas');
    const slide = host.closest('article');
    const pad = RustTetris.padReader();
    let game = null, last = '';

    function show() {
      if (!game) { api.w(host, '▶ 시작을 누르거나 판을 누르세요.', 'dim'); return; }
      const s = game.stats();
      const t = '점수 ' + s.score + ' · 줄 ' + s.lines + ' · 레벨 ' + s.level +
        (s.over ? ' · 게임 오버 — ↻ 또는 R' : s.paused ? ' · 멈춤' : '') +
        (owner === me ? '' : ' · (조작 꺼짐)');
      if (t !== last) { last = t; api.w(host, api.esc(t), s.over ? 'bad' : 'ok'); }
    }

    const me = {
      visible: function () { return slide.classList.contains('on'); },
      press: function (n) { return game ? game.press(n) : false; },
      release: function () {
        if (owner === me) { owner = null; window.__deckPadOwner = false; }
        if (game) {
          const s = game.stats();
          if (!s.paused && !s.over) game.press('pause');
          game.sleep();
        }
        host.classList.remove('live');
        show();
      },
    };

    async function start() {
      if (owner && owner !== me) owner.release();
      if (!game) {
        const inst = await WebAssembly.instantiate(await wasmModule(), {});
        game = RustTetris.mount(canvas, inst.exports, {
          cell: 24,
          onStats: show,
          onFrame: function (now) {
            if (!me.visible()) { me.release(); return; }
            if (owner === me) pad(now, function (n) { game.press(n); });
          },
        });
      } else {
        game.wake();
        if (game.stats().paused) game.press('pause');
      }
      owner = me;
      window.__deckPadOwner = true;
      host.classList.add('live');
      last = '';
      canvas.focus({ preventScroll: true });
    }
    function go() {
      start().catch(function (e) { api.w(host, api.esc('WASM 을 열지 못했다: ' + e.message), 'bad'); });
    }

    host.querySelector('[data-start]').addEventListener('click', go);
    host.querySelector('[data-stop]').addEventListener('click', function () { me.release(); });
    canvas.addEventListener('pointerdown', function () { if (owner !== me) go(); });

    // 화면 버튼: 이동·소프트 드롭은 누르고 있으면 반복(170ms 뒤 50ms 간격)
    host.querySelectorAll('[data-a]').forEach(function (b) {
      const name = b.dataset.a;
      let timer = 0;
      const stop = function () { clearTimeout(timer); timer = 0; };
      b.addEventListener('pointerdown', function (e) {
        e.preventDefault();
        if (owner !== me) { go(); return; }
        me.press(name);
        if (name === 'left' || name === 'right' || name === 'soft') {
          const again = function () { me.press(name); timer = setTimeout(again, 50); };
          timer = setTimeout(again, 170);
        }
      });
      ['pointerup', 'pointerleave', 'pointercancel'].forEach(function (ev) { b.addEventListener(ev, stop); });
    });
    show();
  });
})();
