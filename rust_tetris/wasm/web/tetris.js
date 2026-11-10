// tetris.js — Rust 가 만든 tetris_wasm.wasm 을 브라우저에 붙이는 글루.
//
// wasm-bindgen 이 자동으로 만들어 주는 일을 직접 한다:
//   1) .wasm 바이트를 받아 인스턴스를 만든다(가져올 함수는 없다)
//   2) 매 프레임 tt_tick → tt_render 를 부르고, 돌려받은 주소에서
//      선형 메모리를 RGBA 로 읽어 캔버스에 올린다
//   3) 키보드·터치·게임패드를 입력 번호(0~8)로 바꿔 tt_input 에 넣는다
// 전역 RustTetris 하나만 만든다(모듈 번들러 없이 <script> 로 쓴다).
(function (global) {
  'use strict';

  // ANCHOR: codes
  // Rust 쪽 ACTIONS 배열과 같은 순서. 바꾸면 양쪽을 같이 바꾼다.
  const CODE = { left: 0, right: 1, soft: 2, hard: 3, cw: 4, ccw: 5,
                 hold: 6, pause: 7, restart: 8 };
  const KEYS = {
    ArrowLeft: 'left', ArrowRight: 'right', ArrowDown: 'soft',
    ArrowUp: 'cw', x: 'cw', X: 'cw', z: 'ccw', Z: 'ccw', ' ': 'hard',
    c: 'hold', C: 'hold', p: 'pause', P: 'pause', Escape: 'pause',
    r: 'restart', R: 'restart',
  };
  // 누르고 있으면 반복되는 동작
  const REPEATS = new Set(['left', 'right', 'soft']);
  // ANCHOR_END: codes

  // ANCHOR: load
  /** URL 이나 바이트(ArrayBuffer·Uint8Array)에서 exports 를 만든다. */
  async function load(src) {
    const bytes = typeof src === 'string'
      ? await (await fetch(src)).arrayBuffer()
      : src;
    const { instance } = await WebAssembly.instantiate(bytes, {});
    return instance.exports;
  }
  // ANCHOR_END: load

  // ANCHOR: keyname
  /** 키 이벤트 → 동작 이름(없으면 null). 반복 이벤트는 이동만 통과. */
  function keyName(e) {
    const name = KEYS[e.key] || null;
    if (name && e.repeat && !REPEATS.has(name)) return null;
    return name;
  }
  // ANCHOR_END: keyname

  // ANCHOR: mount
  /**
   * 캔버스에 게임을 붙이고 돌린다. 돌려주는 조종기:
   *   press(name)  동작 하나
   *   stats()      {score, lines, level, over, paused}
   *   sleep()      프레임 루프만 멈춤(상태 유지) · wake()  다시 돌림
   *   stop()       완전히 정지 ·  running  루프가 도는 중인가
   */
  function mount(canvas, ex, opts = {}) {
    const cell = opts.cell || 24;
    const seed = opts.seed ?? Date.now();
    // u64 씨앗을 32비트 둘로. >>> 0 은 "부호 없는 32비트로" 관용구
    const lo = seed >>> 0, hi = Math.floor(seed / 2 ** 32) >>> 0;
    if (!ex.tt_init(lo, hi, cell)) {
      throw new Error('tt_init 실패: cell=' + cell);
    }
    const w = ex.tt_width(), h = ex.tt_height();
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');

    let last = performance.now(), carry = 0, raf = 0;
    const ctl = {
      running: true,
      press(name) {
        return name in CODE ? ex.tt_input(CODE[name]) === 1 : false;
      },
      stats() {
        return { score: ex.tt_stat(0), lines: ex.tt_stat(1),
                 level: ex.tt_stat(2), over: ex.tt_stat(3) === 1,
                 paused: ex.tt_stat(4) === 1 };
      },
      sleep() {
        cancelAnimationFrame(raf);
        raf = 0;
        ctl.running = false;
      },
      wake() {
        if (raf) return;
        ctl.running = true;
        last = performance.now(); // 자는 동안의 시간은 버린다
        raf = requestAnimationFrame(frame);
      },
      stop() { ctl.sleep(); },
    };

  // ANCHOR_END: mount

    // ANCHOR: frame
    function frame(now) {
      raf = 0;
      if (!ctl.running) return;
      // 탭이 쉬다 돌아오면 수 초가 한꺼번에 온다 → 한 번에 100ms 까지만
      carry += Math.min(100, now - last);
      last = now;
      const ms = Math.floor(carry);
      carry -= ms;
      ex.tt_tick(ms);
      if (opts.onFrame) opts.onFrame(now);
      // onFrame 안에서 sleep() 했으면 다음 프레임을 예약하지 않는다
      if (!ctl.running) return;

      const ptr = ex.tt_render();
      // 매번 새 뷰: 메모리가 늘면 옛 memory.buffer 는 길이 0 이 된다
      const px = new Uint8ClampedArray(
        ex.memory.buffer, ptr, w * h * 4);
      ctx.putImageData(new ImageData(px, w, h), 0, 0);
      if (opts.onStats) opts.onStats(ctl.stats());
      raf = requestAnimationFrame(frame);
    }
    // ANCHOR_END: frame
    raf = requestAnimationFrame(frame);
    return ctl;
  }

  // ANCHOR: pad
  /**
   * 게임패드 → 동작. 매 프레임 불러 준다. 버튼은 "눌리는 순간"만,
   * 십자키 좌우·아래는 170ms 뒤 50ms 간격으로 반복한다.
   * 표준 배치: 0=A 1=B 2=X 3=Y 4=LB 5=RB 9=Start 12~15=십자키.
   */
  function padReader() {
    const held = {}, next = {};
    const MAP = [
      [0, 'cw'], [1, 'ccw'], [2, 'hold'], [3, 'hard'], [4, 'hold'],
      [5, 'hold'], [9, 'pause'], [12, 'hard'], [13, 'soft'],
      [14, 'left'], [15, 'right'],
    ];
    return function poll(now, press) {
      const pads = navigator.getGamepads ? navigator.getGamepads() : [];
      const down = {};
      for (const g of pads) {
        if (!g) continue;
        for (const [i, name] of MAP) {
          const b = g.buttons[i];
          if (b && (b.pressed || b.value > 0.5)) down[name] = true;
        }
        if ((g.axes[0] || 0) < -0.5) down.left = true;
        if ((g.axes[0] || 0) > 0.5) down.right = true;
        if ((g.axes[1] || 0) > 0.5) down.soft = true;
      }
      for (const name of Object.keys(CODE)) {
        if (!down[name]) { held[name] = false; continue; }
        if (!held[name]) {
          held[name] = true;
          next[name] = now + 170;
          press(name);
        } else if (REPEATS.has(name) && now >= next[name]) {
          next[name] = now + 50;
          press(name);
        }
      }
      return Object.keys(down).length > 0;
    };
  }
  // ANCHOR_END: pad

  global.RustTetris = { CODE, KEYS, load, keyName, mount, padReader };
})(typeof window !== 'undefined' ? window : globalThis);
