// 데모를 브라우저 없이 실행해 본다 — 최소 DOM 스텁으로 예외만 잡는다.
//
// 렌더 결과는 확인하지 못한다. 여기서 보는 것은 "터지는가" 다. 대신 슬라이드가
// 실제로 갖고 있는 마크업(deck/sections/*.html 의 <div class="demo">)을 그대로
// 파싱해 host 로 준다. 가짜 host 를 주면 data-* 를 잘못 찾는 데모가 통과해 버린다 —
// 그 버그는 브라우저에서만 드러나고, 그때는 이미 덱이 나간 뒤다.
//
// 배선한 뒤에는 단추를 누르고 입력을 흔들고 requestAnimationFrame 을 몇 바퀴 돌린다.
// 데모의 예외는 대개 초기화가 아니라 두 번째 클릭에서 나온다.
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const VOID = { input: 1, br: 1, img: 1, hr: 1, meta: 1, link: 1 };

// ── 아주 작은 DOM ───────────────────────────────────────────────────────────
let created = [];

function El(tag, attrs) {
  this.tagName = String(tag).toUpperCase();
  this.attrs = attrs || {};
  this.children = [];
  this.style = {};
  this.dataset = {};
  this.listeners = {};
  this.width = 0;
  this.height = 0;
  this.className = this.attrs['class'] || '';
  this.textContent = '';
  this.innerHTML = '';
  this.value = this.attrs.value !== undefined ? this.attrs.value : '';
  this.checked = this.attrs.checked !== undefined;
  this.classList = {
    add() {}, remove() {}, toggle() {}, contains() { return false; }
  };
  created.push(this);
}

El.prototype.appendChild = function (n) { this.children.push(n); return n; };
El.prototype.insertBefore = function (n) { this.children.push(n); return n; };
El.prototype.removeChild = function (n) {
  const i = this.children.indexOf(n);
  if (i >= 0) this.children.splice(i, 1);
  return n;
};
El.prototype.addEventListener = function (t, f) {
  if (!this.listeners[t]) this.listeners[t] = [];
  this.listeners[t].push(f);
};
El.prototype.removeEventListener = function () {};
El.prototype.setAttribute = function (k, v) { this.attrs[k] = String(v); };
El.prototype.getAttribute = function (k) {
  return this.attrs[k] === undefined ? null : this.attrs[k];
};
El.prototype.hasAttribute = function (k) { return this.attrs[k] !== undefined; };
El.prototype.focus = function () {};
El.prototype.getBoundingClientRect = function () {
  return { left: 0, top: 0,
           width: this.width || 300, height: this.height || 200 };
};
El.prototype.getContext = function () { return ctx2d(); };
El.prototype.matches = function (sel) { return match(this, sel); };
El.prototype.dispatch = function (type, ev) {
  const ls = this.listeners[type] || [];
  for (const f of ls) f(ev);
};

function walk(el, out) {
  out.push(el);
  for (const c of el.children) if (c instanceof El) walk(c, out);
  return out;
}

// 데모가 쓰는 선택자는 세 종류뿐이다: [data-x] · .cls · tag
function match(el, sel) {
  const s = sel.trim();
  if (s.charAt(0) === '[') return el.hasAttribute(s.slice(1, -1));
  if (s.charAt(0) === '.') {
    return (' ' + el.className + ' ').indexOf(' ' + s.slice(1) + ' ') >= 0;
  }
  return el.tagName === s.toUpperCase();
}

El.prototype.querySelector = function (sel) {
  const all = walk(this, []).slice(1);
  for (const e of all) if (match(e, sel)) return e;
  return null;
};
El.prototype.querySelectorAll = function (sel) {
  return walk(this, []).slice(1).filter((e) => match(e, sel));
};

function ctx2d() {
  const noop = () => {};
  return new Proxy({}, {
    get(_t, k) {
      if (k === 'measureText') return () => ({ width: 10 });
      if (k === 'createImageData') {
        return (w, h) => ({ data: new Uint8ClampedArray(w * h * 4),
                            width: w, height: h });
      }
      if (k === 'canvas') return null;
      return noop;
    },
    set() { return true; }
  });
}

// ── 슬라이드에서 데모 마크업을 그대로 떠온다 ────────────────────────────────
const TAG = /<\/?([a-zA-Z][a-zA-Z0-9]*)((?:\s+[a-zA-Z-]+(?:="[^"]*")?)*)\s*\/?>/g;
const ATTR = /([a-zA-Z-]+)(?:="([^"]*)")?/g;

function parseAttrs(s) {
  const out = {};
  let m;
  ATTR.lastIndex = 0;
  while ((m = ATTR.exec(s)) !== null) out[m[1]] = m[2] === undefined ? '' : m[2];
  return out;
}

// 여는 태그 하나에서 짝이 맞는 닫는 태그까지의 조각을 트리로 만든다.
function parseFragment(html, rootAttrs) {
  const root = new El('div', rootAttrs);
  const stack = [root];
  let m;
  TAG.lastIndex = 0;
  while ((m = TAG.exec(html)) !== null) {
    const closing = m[0].charAt(1) === '/';
    const name = m[1].toLowerCase();
    if (closing) {
      if (stack.length > 1) stack.pop();
      continue;
    }
    const el = new El(name, parseAttrs(m[2] || ''));
    stack[stack.length - 1].appendChild(el);
    if (!VOID[name] && m[0].slice(-2) !== '/>') stack.push(el);
  }
  return root;
}

// deck/sections/*.html 에서 <div class="demo" data-demo="…"> 블록을 걷어 온다.
function collectHosts() {
  const dir = path.join(ROOT, 'deck', 'sections');
  const hosts = {};
  if (!fs.existsSync(dir)) return hosts;
  for (const f of fs.readdirSync(dir).sort()) {
    if (!/\.html$/.test(f)) continue;
    const src = fs.readFileSync(path.join(dir, f), 'utf8');
    const re = /<div class="demo" data-demo="([^"]+)">/g;
    let m;
    while ((m = re.exec(src)) !== null) {
      const id = m[1];
      // 짝이 맞는 </div> 찾기 — div 만 세면 된다.
      let i = re.lastIndex;
      let depth = 1;
      const dv = /<(\/?)div\b[^>]*>/g;
      dv.lastIndex = i;
      let d;
      while ((d = dv.exec(src)) !== null) {
        depth += d[1] === '/' ? -1 : 1;
        if (depth === 0) { i = d.index; break; }
      }
      hosts[id] = { html: src.slice(re.lastIndex, i), file: f };
    }
  }
  return hosts;
}

// ── 전역 ────────────────────────────────────────────────────────────────────
const rafQueue = [];
global.document = {
  createElement: (t) => new El(t, {}),
  querySelector: () => null,
  querySelectorAll: () => [],
  hidden: false
};
const win = {
  __demoRegistry: {},
  addEventListener() {},
  removeEventListener() {},
  setTimeout: setTimeout,
  clearTimeout: clearTimeout,
  document: global.document,
  requestAnimationFrame: (f) => { rafQueue.push(f); return rafQueue.length; },
  cancelAnimationFrame: () => {}
};
win.window = win;
win.globalThis = win;
win.__demo = (id, fn) => { win.__demoRegistry[id] = fn; };
global.window = win;
global.self = win;
global.requestAnimationFrame = win.requestAnimationFrame;
global.cancelAnimationFrame = win.cancelAnimationFrame;

// 엔진 번들이 먼저다 — 미니 RTS 데모가 window.__rts 를 쓴다. 노드 전역(require·
// process·__dirname)을 인자로 가려 브라우저와 같은 조건을 만든다. 진짜 vm 컨텍스트로
// 최상위 코드를 검사하는 것은 tools/check_web.js 의 몫이다.
const enginePath = path.join(ROOT, 'deck', 'engine.js');
if (fs.existsSync(enginePath)) {
  const src = fs.readFileSync(enginePath, 'utf8');
  new Function('window', 'globalThis', 'document', 'require', 'module',
               'exports', '__dirname', '__filename', 'process', src)(
    win, win, global.document, undefined, undefined, undefined, undefined,
    undefined, undefined);
} else {
  console.log('  deck/engine.js 가 없다 — 엔진을 쓰는 데모는 실패한다');
}

const demoFile = process.argv[2] || path.join(ROOT, 'deck', 'demos.js');
new Function('window', 'document', fs.readFileSync(demoFile, 'utf8'))(
  win, global.document);

// ── 데모 틀이 주는 api 와 같은 모양 ─────────────────────────────────────────
function out(host) { return host.querySelector('.out'); }
const api = {
  out: out,
  w(host, html) { const o = out(host); if (o) o.innerHTML = String(html); },
  add(host, html) { const o = out(host); if (o) o.innerHTML += String(html); },
  esc: (s) => String(s),
  show: (v) => String(v),
  num: (n) => String(n)
};

// ── 실행 ────────────────────────────────────────────────────────────────────
const hosts = collectHosts();
const ids = Object.keys(win.__demoRegistry).sort();
let ok = 0;
let bad = 0;

function fireAll(host, label) {
  const all = walk(host, []).concat(created);
  const seen = new Set();
  for (const el of all) {
    if (seen.has(el)) continue;
    seen.add(el);
    for (const type of ['click', 'input', 'change', 'mousedown', 'mousemove',
                        'mouseup', 'keydown', 'contextmenu']) {
      if (!el.listeners[type]) continue;
      const ev = { clientX: 90, clientY: 70, button: type === 'contextmenu' ? 2 : 0,
                   key: 'ArrowRight', shiftKey: false, preventDefault() {},
                   stopPropagation() {} };
      try {
        el.dispatch(type, ev);
      } catch (e) {
        console.log('  [' + label + '] ' + type + ' 핸들러 예외: ' + e.message);
        bad += 1;
        return;
      }
    }
  }
}

function drainRaf(label, rounds) {
  let now = 0;
  for (let i = 0; i < rounds && rafQueue.length > 0; i += 1) {
    const f = rafQueue.shift();
    now += 60;
    try {
      f(now);
    } catch (e) {
      console.log('  [' + label + '] rAF 예외: ' + e.message);
      bad += 1;
      return;
    }
  }
  rafQueue.length = 0;
}

for (const id of ids) {
  created = [];
  const src = hosts[id];
  const host = src
    ? parseFragment(src.html, { 'class': 'demo', 'data-demo': id })
    : parseFragment('<div class="out"></div>', { 'class': 'demo',
                                                 'data-demo': id });
  const mark = src ? src.file : '(마크업 없음)';
  const before = bad;
  try {
    win.__demoRegistry[id](host, api);
    fireAll(host, id);
    // 마지막에 "돌리기/한 걸음" 을 한 번 더 누른다. 앞의 무차별 발사가 초기화
    // 단추까지 눌러 버리므로, 덤프에 남는 것이 뜻 있는 상태가 되도록.
    for (const sel of ['[data-run]', '[data-step]']) {
      const b = host.querySelector(sel);
      if (b) {
        try {
          b.dispatch('click', { preventDefault() {}, clientX: 40, clientY: 30 });
        } catch (e) {
          console.log('  [' + id + '] ' + sel + ' 재클릭 예외: ' + e.message);
          bad += 1;
        }
      }
    }
    drainRaf(id, 120);
  } catch (e) {
    console.log('demo ' + id + ' 실패: ' + e.message);
    console.log(String(e.stack).split('\n').slice(1, 4).join('\n'));
    bad += 1;
    continue;
  }
  if (bad === before) {
    console.log('demo ' + id + ' OK  ' + mark);
    ok += 1;
  } else {
    console.log('demo ' + id + ' 실패  ' + mark);
  }
  // --dump 은 데모가 실제로 적은 글을 보여 준다. 예외가 없다고 해서 숫자가
  // 맞는다는 뜻은 아니다 — 눈으로 한 번은 읽어야 한다.
  if (process.argv.indexOf('--dump') >= 0) {
    for (const el of created) {
      if (typeof el.innerHTML === 'string' && el.innerHTML.length > 0
          && el.tagName === 'DIV') {
        console.log('    | ' + el.innerHTML.replace(/<[^>]*>/g, '')
                    .split('\n').join('\n    | '));
      }
    }
  }
}

// 슬라이드가 부르는데 등록되지 않은 데모는 조용히 빈 칸이 된다 — 잡아야 한다.
const missing = Object.keys(hosts).filter((id) => ids.indexOf(id) < 0);
if (missing.length > 0) {
  console.log('  등록되지 않은 데모: ' + missing.join(', '));
  bad += missing.length;
}

console.log(ok + '개 통과 · ' + bad + '건 실패');
process.exit(bad ? 1 : 0);
