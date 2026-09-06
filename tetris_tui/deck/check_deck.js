// check_deck.js — 완성된 덱을 브라우저 없이 점검한다.
//
//   node deck/check_deck.js ../Go_Bubble_Tea_테트리스_만들기.html
//
// Playwright 는 이 기계에서 못 쓴다(node 가 platform=android 로 보고한다).
// 그래서 최소한의 DOM 스텁을 만들어 재생기를 실제로 마운트해 보고,
// 구조적으로 확인할 수 있는 것들을 훑는다.
//
// 확인하는 것:
//   1) 슬라이드 수와 목차·카운터가 서로 맞는가
//   2) 재생기가 가리키는 기록이 실제로 있는가
//   3) 모든 프레임이 빠진 줄 없이 재생되는가
//   4) 프레임이 쓰는 클래스가 스타일 표에 전부 있는가
//   5) 아직 안 만들어진 자리(플레이스홀더)가 남아 있지 않은가
//   6) 터미널 화면이 80칸을 넘지 않는가 (폴드에서 가로 스크롤이 생긴다)
'use strict';
const fs = require('fs');

const path = process.argv[2];
if (!path) {
  console.error('사용법: node deck/check_deck.js <덱.html>');
  process.exit(2);
}
const html = fs.readFileSync(path, 'utf8');

// 화면 칸 수. 한글·CJK 만 두 칸으로 센다 —
// 박스 그리기(U+2500~)와 블록(U+2580~)은 터미널에서 한 칸이다.
function cells2(s) {
  let n = 0;
  for (const ch of s) {
    const c = ch.codePointAt(0);
    const wide = (c >= 0x1100 && c <= 0x115F) || (c >= 0x2E80 && c <= 0x303E) ||
      (c >= 0x3041 && c <= 0x33FF) || (c >= 0x3400 && c <= 0x4DBF) ||
      (c >= 0x4E00 && c <= 0x9FFF) || (c >= 0xAC00 && c <= 0xD7A3) ||
      (c >= 0xF900 && c <= 0xFAFF) || (c >= 0xFF00 && c <= 0xFF60);
    n += wide ? 2 : 1;
  }
  return n;
}

let bad = 0;
function fail(msg) { console.log('  ✗ ' + msg); bad++; }
function ok(msg) { console.log('  ✓ ' + msg); }

// ── 1) 슬라이드 수 ────────────────────────────────────────────────────
const slides = html.match(/<section class="slide"/g) || [];
const counter = /<span id="counter">1 \/ (\d+)<\/span>/.exec(html);
const tocHead = /<h3>목차 — 전체 (\d+)장<\/h3>/.exec(html);
if (!counter || !tocHead) {
  fail('카운터나 목차 머리를 못 찾았다');
} else if (+counter[1] !== slides.length || +tocHead[1] !== slides.length) {
  fail(`슬라이드 ${slides.length}장인데 카운터 ${counter[1]}, 목차 ${tocHead[1]}`);
} else {
  ok(`슬라이드 ${slides.length}장 — 카운터·목차와 일치`);
}

const tocLinks = (html.match(/<a href="#s\d+" data-go="\d+">/g) || []).length;
if (tocLinks !== slides.length) fail(`목차 항목이 ${tocLinks}개 — 슬라이드는 ${slides.length}장`);
else ok(`목차 항목 ${tocLinks}개`);

// ── 2) 기록 묶음 ──────────────────────────────────────────────────────
const fm = /<script>window\.__FRAMES=(\{[\s\S]*?\});<\/script>/.exec(html);
if (!fm) {
  fail('기록 묶음(window.__FRAMES)이 없다');
} else {
  let FRAMES;
  try {
    FRAMES = JSON.parse(fm[1]);
  } catch (e) {
    fail('기록 묶음을 파싱할 수 없다: ' + e.message);
    FRAMES = {};
  }
  const names = Object.keys(FRAMES);
  ok(`기록 ${names.length}종: ${names.join(' · ')}`);

  // 재생기가 가리키는 이름이 전부 있는가
  const used = [...html.matchAll(/class="player" data-frames="([^"]+)"/g)].map((m) => m[1]);
  for (const u of used) {
    if (!FRAMES[u]) fail(`재생기가 없는 기록 ${u} 를 가리킨다`);
  }
  if (used.length) ok(`재생기 ${used.length}개 — 가리키는 기록이 전부 있다`);

  // ── 3·4) 모든 프레임을 재생해 본다 ─────────────────────────────────
  for (const name of names) {
    const rec = FRAMES[name];
    const styleKeys = new Set(Object.keys(rec.styles || {}));
    let lines = [];
    let blanks = 0;
    let maxCols = 0;
    for (let i = 0; i < rec.frames.length; i++) {
      const f = rec.frames[i];
      (f.d || []).forEach((d) => { lines[d[0]] = d[1]; });
      lines.length = f.n;
      for (let y = 0; y < lines.length; y++) {
        if (lines[y] === undefined) { blanks++; lines[y] = ''; }
        const plain = lines[y].replace(/<[^>]*>/g, '');
        const c2 = cells2(plain);
        if (c2 > maxCols) maxCols = c2;
      }
      for (const m of (f.d || [])) {
        for (const cm of m[1].matchAll(/class="(a\d+)"/g)) {
          if (!styleKeys.has(cm[1])) fail(`${name} 프레임 ${i}: 없는 클래스 ${cm[1]}`);
        }
      }
    }
    if (blanks) fail(`${name}: 채워지지 않은 줄 ${blanks}개 — 첫 프레임이 전체를 안 담았다`);
    else ok(`${name}: ${rec.frames.length}프레임 재생 정상 (${maxCols}칸 × ${rec.rows}줄)`);
    if (maxCols > 84) fail(`${name}: 화면이 ${maxCols}칸 — 80칸을 크게 넘는다`);
  }
}

// ── 5) 플레이스홀더 ──────────────────────────────────────────────────
const placeholders = (html.match(/아직 없습니다/g) || []).length;
if (placeholders) fail(`아직 안 만들어진 자리 ${placeholders}개가 남아 있다`);
else ok('플레이스홀더 없음');

// ── 6) 터미널 캡처의 폭 ──────────────────────────────────────────────
let capMax = 0, capCount = 0;
for (const m of html.matchAll(/<pre class="term"><code>([\s\S]*?)<\/code><\/pre>/g)) {
  capCount++;
  for (const line of m[1].split('\n')) {
    const plain = line.replace(/<[^>]*>/g, '')
      .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
    const c2 = cells2(plain);
    if (c2 > capMax) capMax = c2;
  }
}
if (capMax > 84) fail(`터미널 캡처가 ${capMax}칸 — 80칸을 넘는다`);
else ok(`터미널 캡처 ${capCount}개 · 최대 ${capMax}칸`);

// ── 6b) 내장 글꼴 ──────────────────────────────────────────────────
// 캡처는 "한글 2칸·나머지 1칸" 규칙 위의 그림이라, 보는 기기의 글꼴에 맡기면 깨진다.
// 덱이 D2Coding 서브셋을 woff2 로 싣고, 고정폭 글꼴 목록마다 그것을 맨 앞에 둬야 한다.
const styleHead = html.split('</style>')[0];
const faces = (styleHead.match(/@font-face\{font-family:"DeckMono"/g) || []).length;
const isWoff2 = /src:url\(data:font\/woff2;base64,d09GMg/.test(styleHead);   // 'wOF2' 의 base64
const stacks = [...styleHead.matchAll(/font-family:([^;}]*monospace[^;}]*)/g)].map(m => m[1]);
const badStacks = stacks.filter(s => !s.startsWith('"DeckMono"'));
if (faces !== 1) fail(`내장 글꼴 @font-face 가 ${faces}개 — 정확히 1개여야 한다`);
else if (!isWoff2) fail('내장 글꼴이 woff2 가 아니다');
else if (badStacks.length) fail(`DeckMono 로 시작하지 않는 고정폭 글꼴 목록 ${badStacks.length}개`);
else ok(`내장 글꼴 DeckMono(woff2) · 고정폭 목록 ${stacks.length}개 전부 그것을 먼저 본다`);

// ── 7) 재생기를 실제로 마운트해 본다 ─────────────────────────────────
// 재생기 스크립트 조각을 찾는다 — __player 를 노출하는 <script> 하나다.
const pm = (function () {
  for (const m of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    if (m[1].indexOf('window.__player') >= 0) return m;
  }
  return null;
})();
if (!pm) {
  fail('재생기 스크립트를 못 찾았다');
} else {
  const hosts = [];
  function mkEl(tag) {
    const el = {
      tagName: tag, style: {}, dataset: {}, classList: { add() {} },
      children: [], innerHTML: '', textContent: '', value: 0,
      appendChild(n) { el.children.push(n); return n; },
      addEventListener() {}, focus() {},
      querySelector(sel) {
        // 재생기가 만드는 조각들을 흉내 낸다
        const stub = mkEl('div');
        stub.__sel = sel;
        return stub;
      },
    };
    return el;
  }
  const host = mkEl('div');
  host.dataset.frames = '1p';
  hosts.push(host);
  global.document = {
    readyState: 'complete',
    createElement: mkEl,
    head: mkEl('head'),
    addEventListener() {},
    querySelectorAll: () => hosts,
  };
  const FRAMES = fm ? JSON.parse(fm[1]) : {};
  global.window = { __FRAMES: FRAMES };
  try {
    new Function('window', 'document', pm[1])(global.window, global.document);
    if (!global.window.__player) throw new Error('__player 가 안 만들어졌다');
    const one = global.window.__player.frameAt(FRAMES['1p'], 5);
    if (!one || one.indexOf('\n') < 0) throw new Error('프레임이 비었다');
    ok('재생기 마운트 정상 — frameAt 이 화면을 만든다');
  } catch (e) {
    fail('재생기 실행 실패: ' + e.message);
  }
}

console.log(bad ? `\n오류 ${bad}건` : '\n오류 0건');
process.exit(bad ? 1 : 0);
