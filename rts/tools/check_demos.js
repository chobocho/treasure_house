// 데모를 브라우저 없이 실행해 본다 — 최소 DOM 스텁으로 예외만 잡는다.
// (렌더 결과는 확인하지 못한다. 논리 오류가 아니라 '터지는지'를 본다.)
'use strict';
const fs = require('fs');

const listeners = [];
function stubCtx() {
  const noop = () => {};
  return new Proxy({}, {
    get(_t, k) {
      if (k === 'canvas') return null;
      if (k === 'measureText') return () => ({ width: 10 });
      if (k === 'createImageData') {
        return (w, h) => ({ data: new Uint8ClampedArray(w * h * 4), width: w, height: h });
      }
      return noop;
    },
    set() { return true; }
  });
}
function mkEl(tag) {
  const el = {
    tagName: tag, style: {}, children: [], width: 0, height: 0,
    getContext: () => stubCtx(), focus: () => {}, innerHTML: '',
    getBoundingClientRect: () => ({ left: 0, top: 0, width: el.width || 300, height: el.height || 200 }),
    addEventListener: (t, f) => listeners.push([el, t, f]),
    removeEventListener: () => {},
    querySelector: () => null,
    querySelectorAll: () => [],
    insertBefore: (n) => { el.children.push(n); return n; },
    appendChild: (n) => { el.children.push(n); return n; },
    setAttribute: () => {}, getAttribute: () => null,
    textContent: ''
  };
  return el;
}
global.document = { createElement: mkEl };
global.window = {
  addEventListener: (t, f) => listeners.push([global.window, t, f]),
  __demoRegistry: {}
};
global.window.__demo = (id, fn) => { global.window.__demoRegistry[id] = fn; };
global.self = global.window;

// 엔진 번들이 먼저다 — 미니 RTS 데모가 window.__rts 를 쓴다.
// require() 로 부르면 노드가 __dirname 과 process 를 주므로, 브라우저에서만 터지는
// 버그를 놓친다. 빈 VM 컨텍스트에서 돌려 브라우저와 같은 조건을 만든다.
global.requestAnimationFrame = () => 0;
const path = require('path');
const vm = require('vm');
const engine = path.join(__dirname, '..', 'deck', 'engine.js');
if (fs.existsSync(engine)) {
  const win = global.window;
  win.window = win;
  win.globalThis = win;
  win.document = global.document;
  win.requestAnimationFrame = global.requestAnimationFrame;
  win.setTimeout = setTimeout;
  win.clearTimeout = clearTimeout;
  vm.runInContext(fs.readFileSync(engine, 'utf8'), vm.createContext(win),
                  { filename: 'deck/engine.js' });
}

const src = fs.readFileSync(process.argv[2] || 'deck/demos.js', 'utf8');
new Function('window', 'document', src)(global.window, global.document);

const api = {
  w: () => {}, add: () => {}, esc: (s) => s, show: () => {}
};
let ok = 0, bad = 0;
for (const [id, fn] of Object.entries(global.window.__demoRegistry)) {
  const host = mkEl('div');
  host.querySelector = (sel) => (sel === '.out' ? mkEl('div') : null);
  host.querySelectorAll = () => [];
  try {
    fn(host, api);
    // 등록된 이벤트 핸들러를 몇 개 흉내내 본다
    for (const [el, t, f] of listeners) {
      if (el !== host && (t === 'mousemove' || t === 'click' || t === 'mousedown')) {
        try { f({ clientX: 120, clientY: 90, preventDefault() {}, shiftKey: false }); } catch (e) {
          console.log('  [' + id + '] ' + t + ' 핸들러에서 예외: ' + e.message);
          bad++;
        }
      }
    }
    console.log('demo ' + id + ' OK');
    ok++;
  } catch (e) {
    console.log('demo ' + id + ' 실패: ' + e.message);
    console.log(e.stack.split('\n').slice(0, 4).join('\n'));
    bad++;
  }
  listeners.length = 0;
}
console.log(ok + '개 통과 · ' + bad + '건 실패');
process.exit(bad ? 1 : 0);
