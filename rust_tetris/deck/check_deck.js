// check_deck.js — 조립된 덱을 jsdom 으로 띄워 엔진·목차·WASM 데모를 실제로 돌려 본다.
//
//   node deck/check_deck.js [../Rust_테트리스_만들기.html]
//
// 이 기계에서는 Playwright 를 못 쓴다(node 가 platform=android). jsdom 은 레이아웃이 없으므로
// 폭·넘침은 못 보고(→ tools/layout_snap.py), 스크립트가 하는 일을 본다.
// jsdom 위치: JSDOM 환경 변수, 없으면 이 기계의 다른 프로젝트 것을 빌려 쓴다.
'use strict';
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require(process.env.JSDOM || '/root/github/drug/node_modules/jsdom');

const file = process.argv[2] || path.join(__dirname, '..', '..', 'Rust_테트리스_만들기.html');
const html = fs.readFileSync(file, 'utf8');
let fails = 0, passes = 0;
const ok = (cond, msg) => { if (cond) passes++; else { fails++; console.log('FAIL', msg); } };
const sleep = ms => new Promise(r => setTimeout(r, ms));

const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => errors.push(String(e.message || e)));
vc.on('error', e => errors.push(String(e)));

const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://example.test/deck.html',
  virtualConsole: vc,
  beforeParse(win) {
    win.WebAssembly = WebAssembly;
    win.ImageData = class { constructor(d, w, h) { this.data = d; this.width = w; this.height = h; } };
    win.__puts = 0;
    win.HTMLCanvasElement.prototype.getContext = function () {
      return { putImageData: () => { win.__puts++; } };
    };
    win.HTMLElement.prototype.scrollIntoView = function () {};
    win.HTMLElement.prototype.scrollBy = function () {};
    win.indexedDB = undefined; // 책갈피 셸은 조용히 빠진다
  },
});
const { window: w } = dom;
const doc = w.document;

function key(k) {
  const e = new w.KeyboardEvent('keydown', { key: k, code: k, bubbles: true, cancelable: true });
  doc.body.dispatchEvent(e);
  return e;
}
const current = () => [...doc.querySelectorAll('main.prose > article')].findIndex(a => a.classList.contains('on'));

(async () => {
  await sleep(300);
  const slides = [...doc.querySelectorAll('main.prose > article')];
  const n = slides.length;
  ok(n > 0, '슬라이드가 없다');
  ok(doc.getElementById('counter').textContent.trim() === `1 / ${n}`, '카운터: ' + doc.getElementById('counter').textContent);
  ok(doc.querySelectorAll('#tocBody a').length === n, `목차 링크 ${doc.querySelectorAll('#tocBody a').length} ≠ ${n}`);
  for (const o of doc.querySelectorAll('#nav option')) ok(doc.getElementById(o.value), '없는 nav 대상 ' + o.value);
  ok(html.includes('if (window.__deckPadOwner) return;'), '게임패드 셸 고리 없음');
  ok(!/PLACEHOLDER|TODO|\(작성 중\)/.test(html), '자리표시가 남았다');
  for (const s of slides) ok(s.querySelector('h1, h2, h3'), '제목 없는 슬라이드 ' + s.id);

  // 슬라이드를 하나씩 다 열어 본다 — 하이라이트·데모 배선이 예외 없이 도는지
  for (let i = 0; i < n; i++) { doc.getElementById('nextBtn').click(); }
  await sleep(50);
  const unhl = [...doc.querySelectorAll('pre > code[data-lang]')].filter(c => !c.dataset.hl).length;
  ok(unhl === 0, `하이라이트 안 된 코드 ${unhl}개`);

  // WASM 데모: 첫 데모 슬라이드로 가서 시작
  const host = doc.querySelector('.demo[data-demo="tetris"]');
  ok(host, '테트리스 데모가 없다');
  const sid = host.closest('article').id;
  w.location.hash = '#' + sid;
  await sleep(100);
  const at = current();
  ok(slides[at].id === sid, '데모 슬라이드로 못 갔다');
  ok(/시작/.test(host.querySelector('.out').textContent), '데모 안내 문구: ' + host.querySelector('.out').textContent);
  host.querySelector('[data-start]').click();
  await sleep(400);
  ok(w.__puts > 3, `캔버스에 그린 횟수 ${w.__puts}`);
  ok(w.__deckPadOwner === true, '시작했는데 패드를 안 쥐었다');
  ok(/점수 0/.test(host.querySelector('.out').textContent), '점수 표시: ' + host.querySelector('.out').textContent);
  const canvas = host.querySelector('canvas');
  ok(canvas.width === 396 && canvas.height === 504, `캔버스 ${canvas.width}×${canvas.height}`);

  let e = key('ArrowRight');
  ok(e.defaultPrevented, '게임 중 → 키를 가로채야 한다');
  ok(current() === at, '게임 중 → 슬라이드가 넘어가면 안 된다');
  key(' ');
  await sleep(100);
  ok(/점수 [1-9]/.test(host.querySelector('.out').textContent), '하드 드롭 뒤 점수: ' + host.querySelector('.out').textContent);
  ok(current() === at, 'Space 로 슬라이드가 넘어갔다');

  key('q');
  await sleep(50);
  ok(w.__deckPadOwner === false, 'Q 뒤에도 패드를 쥐고 있다');
  ok(/멈춤/.test(host.querySelector('.out').textContent), 'Q 뒤 상태: ' + host.querySelector('.out').textContent);
  const puts = w.__puts;
  await sleep(200);
  ok(w.__puts === puts, '놓은 뒤에도 프레임이 돈다');
  e = key('ArrowRight');
  await sleep(50);
  ok(current() === at + 1, '놓은 뒤 → 슬라이드가 넘어가야 한다');

  // 다시 와서 시작하면 이어서(멈춤 풀림), 슬라이드를 떠나면 저절로 놓는다
  w.location.hash = '#' + sid;
  await sleep(100);
  host.querySelector('[data-start]').click();
  await sleep(200);
  ok(!/멈춤/.test(host.querySelector('.out').textContent), '다시 시작했는데 멈춤');
  doc.getElementById('nextBtn').click();
  await sleep(200);
  ok(w.__deckPadOwner === false, '슬라이드를 떠났는데 패드를 쥐고 있다');

  const real = errors.filter(m => !/Not implemented: (window\.scrollTo|HTMLCanvasElement)/.test(m));
  ok(real.length === 0, '스크립트 오류: ' + real.slice(0, 3).join(' | '));
  console.log(`슬라이드 ${n}장 · 검사 ${passes} 통과 · ${fails} 실패`);
  w.close();
  process.exit(fails ? 1 : 0);
})();
