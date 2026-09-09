// check_deck.js — 완성된 덱을 브라우저 없이 점검한다.
//
//   node deck/check_deck.js ../Keycloak_AD_연동_쉽게_배우기.html
//
// Playwright 는 이 기계에서 못 쓴다(node 가 platform=android 로 보고한다).
// 그래서 정규식과 최소한의 DOM 스텁으로 구조적으로 확인할 수 있는 것만 훑는다.
// 여기서 잡는 것은 "사람이 넘겨 보다가 발견하면 이미 늦은" 종류의 결함이다.
//
// 확인하는 것:
//   1) 슬라이드 수와 id 가 유일한가 / 챕터 이동 select 가 실재하는 id 를 가리키는가
//   2) 플레이스홀더(아직 안 채운 자리)가 남아 있지 않은가
//   3) 모든 <div class="demo" data-demo="x"> 가 __demo('x', …) 로 배선돼 있는가
//   4) 모든 퀴즈에 답이 달려 있는가
//   5) 덱 안 상호참조 href="#id" 와 다른 덱으로 가는 href="./덱.html#id" 가
//      실재하는 자리를 가리키는가
//   6) 외부 자원(CDN 스크립트·폰트·이미지) 참조가 없는가 — 자기완결형 계약
//   7) 데모 프레임워크를 DOM 스텁 위에서 실제로 돌려 본다 (throw 하지 않는가)
'use strict';
const fs = require('fs');
const path = require('path');

const target = process.argv[2];
if (!target) {
  console.error('사용법: node deck/check_deck.js <덱.html>');
  process.exit(2);
}
const html = fs.readFileSync(target, 'utf8');
const ROOT = path.dirname(path.resolve(target));
// 구조를 셀 때는 <script> 안을 빼고 본다. 덱 엔진의 주석에도 <article ...> 이라는
// 글자가 있어서, 그냥 세면 열림/닫힘이 하나 어긋난 것처럼 보인다.
const struct = html.replace(/<script[\s\S]*?<\/script>/g, '');

let bad = 0;
const fail = (m) => { console.log('  ✗ ' + m); bad++; };
const ok = (m) => console.log('  ✓ ' + m);

// ── 1) 슬라이드·id ────────────────────────────────────────────────────
const arts = [...struct.matchAll(/<article[^>]*\sid="([^"]+)"[^>]*>/g)].map((m) => m[1]);
const dup = arts.filter((v, i) => arts.indexOf(v) !== i);
if (!arts.length) fail('슬라이드(<article id=…>)가 하나도 없다');
else if (dup.length) fail(`중복 id ${dup.length}개: ${[...new Set(dup)].slice(0, 8).join(', ')}`);
else ok(`슬라이드 ${arts.length}장 · id 전부 유일`);

if (struct.split('<article').length - 1 !== struct.split('</article>').length - 1) {
  fail('<article> 열림/닫힘 개수가 다르다');
}

const ids = new Set(arts);
const navOpts = [...struct.matchAll(/<option value="([^"]+)">/g)].map((m) => m[1]);
const deadNav = navOpts.filter((v) => v !== 'top' && !ids.has(v));
if (deadNav.length) fail(`챕터 이동이 없는 id 를 가리킨다: ${deadNav.slice(0, 8).join(', ')}`);
else ok(`챕터 이동 항목 ${navOpts.length}개 — 전부 실재하는 슬라이드`);

// ── 2) 플레이스홀더 ──────────────────────────────────────────────────
// 뼈대 단계에서는 부 표지에 '준비 중' 이 남아 있는 것이 정상이다.
// --skeleton 을 주면 개수만 보고하고 오류로 세지 않는다.
const skeleton = process.argv.includes('--skeleton');
const holes = (struct.match(/아직 없습니다|TODO|준비 중입니다/g) || []).length;
if (!holes) ok('플레이스홀더 없음');
else if (skeleton) ok(`플레이스홀더 ${holes}개 (뼈대 단계라 넘어간다)`);
else fail(`아직 안 채운 자리 ${holes}개가 남아 있다`);

// ── 3) 데모 배선 ─────────────────────────────────────────────────────
const hosts = [...struct.matchAll(/<div class="demo"[^>]*\bdata-demo="([^"]+)"/g)].map((m) => m[1]);
const regs = new Set([...html.matchAll(/__demo\(\s*'([^']+)'/g)].map((m) => m[1]));
const unwired = [...new Set(hosts)].filter((h) => !regs.has(h));
if (unwired.length) fail(`배선되지 않은 데모 ${unwired.length}개: ${unwired.slice(0, 8).join(', ')}`);
else ok(`데모 자리 ${hosts.length}개 · 등록 함수 ${regs.size}개 — 전부 배선됨`);

// ── 4) 퀴즈 ──────────────────────────────────────────────────────────
// 퀴즈 한 장에는 반드시 답이 붙어 있어야 한다. <details> 든 .quiz-a 든 하나는 있어야.
// 템플릿의 퀴즈는 슬라이드 자체다: <article class="card quiz" data-quiz> 안에
// 질문(.q) · 답 보기 단추 · 답(.a) 셋이 있어야 한다. 하나라도 빠지면
// 독자에게는 눌러도 아무 일 없는 상자로 보인다.
let quiz = 0, quizNoAns = 0, quizNoWire = 0;
for (const m of struct.matchAll(/<article[^>]*\bclass="[^"]*\bquiz\b[^"]*"[^>]*>([\s\S]*?)<\/article>/g)) {
  quiz++;
  if (!/\bdata-quiz\b/.test(m[0].slice(0, m[0].indexOf('>')))) quizNoWire++;
  if (!/class="a"/.test(m[1]) || !/<button/.test(m[1]) || !/class="q"/.test(m[1])) {
    quizNoAns++;
  }
}
if (quizNoWire) fail(`data-quiz 가 없는 퀴즈 ${quizNoWire}개 — 단추가 배선되지 않는다`);
if (quizNoAns) fail(`질문(.q)·단추·답(.a) 이 다 갖춰지지 않은 퀴즈 ${quizNoAns}개`);
if (!quizNoWire && !quizNoAns) ok(`퀴즈 ${quiz}개 — 질문·단추·답이 모두 있다`);


// ── 5) 상호참조 ──────────────────────────────────────────────────────
// 링크는 늘어나기만 하고 아무도 다시 눌러 보지 않는다. 기계가 눌러 본다.
//
// 덱 안 링크(#id)부터. 12부의 용어집·치트시트·FAQ 는 거의 전부가
// "이건 몇 부 몇 장에서 봤다" 는 화살표라, 이게 어긋나면 그 부가 통째로
// 쓸모없어진다. 조립기가 용어집의 화살표만 검사하므로, 나머지는 여기서 본다.
const inner = [...struct.matchAll(/href="#([^"]+)"/g)].map((m) => m[1]);
let ibad = 0;
for (const a of inner) {
  if (a === 'top') continue;              // 맨 위로 — 엔진이 처리한다
  if (!ids.has(a)) { fail(`덱 안 링크가 가리키는 #${a} 가 없다`); ibad++; }
}
if (!ibad) ok(`덱 안 상호참조 ${inner.length}개 — 전부 실재하는 자리를 가리킨다`);

const xrefs = [...struct.matchAll(/href="\.\/([^"#]+\.html)#([^"]+)"/g)];
const cache = new Map();
let xbad = 0;
for (const [, file, anchor] of xrefs) {
  const p = path.join(ROOT, file);
  if (!cache.has(file)) {
    cache.set(file, fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : null);
  }
  const doc = cache.get(file);
  if (doc === null) { fail(`상호참조 대상이 없다: ${file}`); xbad++; continue; }
  if (!doc.includes(`id="${anchor}"`)) { fail(`${file} 에 #${anchor} 가 없다`); xbad++; }
}
if (!xbad) ok(`상호참조 ${xrefs.length}개 — 전부 실재하는 자리를 가리킨다`);

// ── 6) 자기완결형 ────────────────────────────────────────────────────
const outside = [
  [/<script[^>]+\bsrc=/, '외부 스크립트'],
  [/<link[^>]+href="https?:/, '외부 스타일시트'],
  [/<img[^>]+src="https?:/, '외부 이미지'],
  [/@import\s+url\(/, '외부 CSS import'],
  [/url\(\s*['"]?https?:/, '외부 자원 url()'],
];
let ext = 0;
for (const [re, why] of outside) if (re.test(html)) { fail(`${why} 참조가 있다 — 자기완결형이 아니다`); ext++; }
if (!ext) ok('외부 자원 참조 없음 — 파일 하나로 열린다');

// ── 7) 데모 프레임워크를 실제로 돌려 본다 ────────────────────────────
// 등록 스크립트가 문법 오류거나 이름을 잘못 쓰면 여기서 throw 한다.
const demoScripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)]
  .map((m) => m[1])
  .filter((s) => s.includes("__demo('") || s.includes('window.__demo ='));
if (!demoScripts.length) {
  ok('등록된 데모 없음 (뼈대 단계)');
} else {
  // 데모가 만지는 화면 조각의 최소 흉내. 값은 전부 비어 있다 —
  // 사용자가 아무것도 입력하지 않은 첫 순간이 데모가 가장 잘 깨지는 때다.
  const el = () => {
    const e = {
      style: {}, dataset: {}, value: '', checked: false,
      classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
      children: [], innerHTML: '', textContent: '',
      appendChild(n) { e.children.push(n); return n; },
      setAttribute() {}, getAttribute: () => null, removeAttribute() {},
      addEventListener() {}, removeEventListener() {}, focus() {}, blur() {},
      querySelector: () => el(), querySelectorAll: () => [], closest: () => null,
      getBoundingClientRect: () => ({ width: 320, height: 200, left: 0, top: 0 }),
      getContext: () => null,
    };
    return e;
  };
  global.document = {
    readyState: 'complete', createElement: el, createElementNS: el,
    head: el(), body: el(), documentElement: el(),
    addEventListener() {}, querySelector: () => el(), querySelectorAll: () => [],
    getElementById: () => null,
  };
  global.window = {
    addEventListener() {}, matchMedia: () => ({ matches: false, addListener() {} }),
    requestAnimationFrame: () => 0, location: { hash: '' }, localStorage: null,
    // Web Crypto 는 node 에도 있다. 없으면 데모가 스스로 비켜 가야 한다.
    crypto: global.crypto,
    TextEncoder, btoa,
  };
  global.TextEncoder = TextEncoder;
  if (typeof global.btoa !== 'function') {
    global.btoa = (s) => Buffer.from(s, 'binary').toString('base64');
  }
  const REG = {};
  global.window.__demo = (id, fn) => { REG[id] = fn; };
  try {
    for (const s of demoScripts) {
      if (s.includes('window.__demo =')) continue;     // 프레임워크 본체는 건너뛴다
      new Function('window', 'document', '__demo', s)(global.window, global.document, global.window.__demo);
    }
    const missing = [...new Set(hosts)].filter((h) => !REG[h]);
    if (missing.length) fail(`돌려 보니 등록되지 않은 데모: ${missing.slice(0, 8).join(', ')}`);

    // 등록만 확인하면 문법 오류밖에 못 잡는다. 실제로 한 번씩 돌려 봐야
    // "빈 입력에서 죽는" 데모를 잡을 수 있다 — 사용자가 처음 보는 그 상태다.
    const api = {
      w() {}, add() {}, out: () => null,
      esc: (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'),
      show: (v) => String(v), num: (n) => String(n),
    };
    let ran = 0;
    for (const [id, fn] of Object.entries(REG)) {
      try { fn(el(), api); ran++; } catch (e) {
        fail(`데모 '${id}' 가 빈 입력에서 죽는다: ${e.message}`);
      }
    }
    if (ran === Object.keys(REG).length) {
      ok(`데모 ${ran}개 — 스텁 위에서 전부 예외 없이 돈다`);
    }
  } catch (e) {
    fail('데모 스크립트 실행 실패: ' + e.message);
  }
}

console.log(bad ? `\n오류 ${bad}건` : '\n오류 0건');
process.exit(bad ? 1 : 0);
