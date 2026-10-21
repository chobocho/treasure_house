import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { inspectDeck, checkRule } from './validate.mjs';

const prose = '탄막 슈팅의 규칙을 직접 실행하며 입력과 이동의 관계를 차근차근 확인합니다.';
const card = (id, classes = '', body = prose) => `<article id="${id}" class="card ${classes}"><h${classes.includes('cover') ? 1 : classes.includes('section') ? 2 : 3}>${prose}</h${classes.includes('cover') ? 1 : classes.includes('section') ? 2 : 3}><p>${body}</p></article>`;
const nav = [{ id: 'part0', label: '처음', kind: 'part', minSlides: 7 }, { id: 'ch0-start', label: '시작', kind: 'chapter', minSlides: 6 }];
const body = card('part0', 'section cover') + card('ch0-start', 'section') + Array.from({ length: 5 }, (_, i) => card(`p0-start-${i}`)).join('');
const shell = (main = body) => `<title>탄막 슈팅</title><span class="brand">탄막 슈팅</span><div id="bar"></div><button id="tocBtn"></button><select id="nav"><option value="">이동</option><option value="part0">처음</option><option value="ch0-start">시작</option></select><main class="prose">${main}</main><script>window.__deckInitHash=''; /* bookmark */</script>`;
const deck = (main = body) => inspectDeck(shell(main));
const check = (id, d, context = {}) => checkRule(id, d, nav, context);

test('V1: 잘못된 UTF-8·치환 문자·깨진 문자열·빈 파일을 거부한다', () => {
  assert.deepEqual(check('V1', deck()), []);
  for (const input of ['', '\uFFFD', '\u00C3\u00C2', Buffer.from([0xff, 0xfe])]) assert.ok(check('V1', inspectDeck(input)).length);
});
test('V2: 빈 덱과 2001장은 거부하고 1~2000장은 허용한다', () => {
  for (const n of [0, 1, 1109, 1499, 1500, 2000, 2001]) assert.equal(check('V2', deck(Array(n).fill(card('x')).join(''))).length === 0, n >= 1 && n <= 2000);
});
test('V3: 모든 article의 누락·중복·비ASCII id를 거부한다', () => {
  assert.deepEqual(check('V3', deck()), []);
  for (const bad of [card('중복'), card('same') + card('same'), '<article class="card"><h3>제목</h3></article>']) assert.ok(check('V3', deck(bad)).length);
});
test('V4: 표지·구간·일반 슬라이드 제목 단계를 검사한다', () => {
  assert.deepEqual(check('V4', deck()), []);
  assert.ok(check('V4', inspectDeck(shell().replace('<h1>', '<h3>'))).length);
});
test('V5: 다른 클래스와 함께 쓰인 수동 페이지 번호도 거부한다', () => {
  assert.deepEqual(check('V5', deck()), []);
  assert.ok(check('V5', deck(body + '<span class="extra pno">1</span>')).length);
});
test('V6: 본문 밖의 박스 문자도 거부한다', () => {
  assert.deepEqual(check('V6', deck()), []);
  assert.ok(check('V6', inspectDeck(shell() + '<!-- \u2500 -->')).length);
});
test('V7: 속성 순서·따옴표에 관계없이 외부 리소스를 거부한다', () => {
  assert.deepEqual(check('V7', deck()), []);
  for (const bad of ['<script src="a.js"></script>', "<link href='a.css' rel='stylesheet'>", '<style>@import "a.css";</style>', '<style>x{background:url(https://x)}</style>']) assert.ok(check('V7', inspectDeck(shell() + bad)).length);
});
test('V8: 셸과 본문의 해시 링크를 검사한다', () => {
  assert.deepEqual(check('V8', deck(body + '<a href="#part0">처음</a>')), []);
  assert.ok(check('V8', inspectDeck(shell() + '<a href="#lost">이동</a>')).length);
  assert.ok(check('V8', inspectDeck(shell() + '<a href="#lost">이동</a><script>const fake = "<div id=\'lost\'>";</script>')).length);
});
test('V9: nav.json·구간·select 항목이 같은 순서여야 한다', () => {
  assert.deepEqual(check('V9', deck()), []);
  assert.ok(check('V9', inspectDeck(shell().replace('<option value="ch0-start">시작</option>', ''))).length);
  assert.ok(check('V9', deck(body + card('ch0-extra', 'section'))).length);
});
test('V10: pre 속성과 공백이 있어도 지원 언어를 검사한다', () => {
  assert.deepEqual(check('V10', deck(body + '<pre class="x">\n<code data-lang="cpp">x</code></pre>')), []);
  assert.ok(check('V10', deck(body + '<pre class="x">\n<code data-lang="glsl">x</code></pre>')).length);
});
test('V11: 코드의 HTML은 이스케이프되어야 한다', () => {
  assert.deepEqual(check('V11', deck(body + '<pre><code data-lang="html">&lt;b&gt;</code></pre>')), []);
  assert.ok(check('V11', deck(body + '<pre><code data-lang="html"><b>x</b></code></pre>')).length);
});
test('V12: 일반 슬라이드의 한글 최소량을 검사하고 표지는 제외한다', () => {
  assert.deepEqual(check('V12', deck()), []);
  assert.ok(check('V12', deck('<article id="x" class="card"><h3>Hi</h3></article>')).length);
});
test('V13: 본문 길이에서 pre 코드를 제외한다', () => {
  assert.deepEqual(check('V13', deck(card('x', '', '<pre><code>' + 'x'.repeat(7000) + '</code></pre>'))), []);
  assert.ok(check('V13', deck(card('x', '', '가'.repeat(6001)))).length);
});
test('V14: 모든 장은 일반 슬라이드가 다섯 장 이상이어야 한다', () => {
  assert.deepEqual(check('V14', deck()), []);
  assert.ok(check('V14', deck(card('part0', 'section cover') + card('ch0-start', 'section'))).length);
  assert.ok(check('V14', deck(card('x', 'quiz'))).length);
});
test('V15: 새 데모 등록과 컨테이너가 일치하고 보존한 템플릿 등록은 구분한다', () => {
  assert.deepEqual(check('V15', inspectDeck(shell(body + '<div data-demo="ring"></div>') + '<script>__demo("ring", function(){})</script>')), []);
  assert.ok(check('V15', deck(body + '<div data-demo="lost"></div>')).length);
  assert.ok(check('V15', inspectDeck(shell() + '<script>__demo("lost", function(){})</script>')).length);
  const inherited = '<script>__demo("sample", function(){})</script>';
  assert.deepEqual(check('V15', inspectDeck(shell() + inherited), { template: inherited }), []);
});
test('V16: 제목·브랜드가 없거나 템플릿 기본값이면 실패한다', () => {
  assert.deepEqual(check('V16', deck()), []);
  assert.ok(check('V16', inspectDeck(shell().replace('<title>탄막 슈팅</title>', ''))).length);
  assert.ok(check('V16', inspectDeck(shell().replaceAll('탄막 슈팅', '슬라이드 덱 템플릿'))).length);
});
test('V17: 12MB 바로 아래는 허용하고 경계는 거부한다', () => {
  assert.deepEqual(check('V17', { ...deck(), bytes: 12 * 1024 * 1024 - 1 }), []);
  assert.ok(check('V17', { ...deck(), bytes: 12 * 1024 * 1024 }).length);
});
test('V18: 해시·목차·진행 막대·책갈피 표식을 모두 요구한다', () => {
  assert.deepEqual(check('V18', deck()), []);
  assert.ok(check('V18', inspectDeck(shell().replace('bookmark', ''))).length);
});

function fixture(t) {
  const src = mkdtempSync(join(tmpdir(), 'danmaku-rules-'));
  t.after(() => rmSync(src, { recursive: true, force: true }));
  mkdirSync(join(src, 'examples', 'pygame'), { recursive: true });
  writeFileSync(join(src, 'examples', 'pygame', 'main.py'), '# region move\nprint("이동")\n# endregion\n');
  return src;
}
test('V19: 조각의 리터럴·없는 영역·없는 출처를 거부한다', (t) => {
  const src = fixture(t);
  const code = '<pre><code data-lang="py" data-src="pygame/main.py#move"></code></pre>';
  assert.deepEqual(check('V19', deck(), { src, parts: [code] }), []);
  for (const part of [code.replace('#move', '#missing'), code.replace('></code>', '>print(1)</code>'), '<pre><code data-lang="py"></code></pre>']) assert.ok(check('V19', deck(), { src, parts: [part] }).length);
});
test('V20: 출처 속성을 제거한 출력에서도 원본 조각을 통해 실행 목록을 검사한다', (t) => {
  const src = fixture(t);
  const context = { src, parts: ['<pre><code data-lang="py" data-src="pygame/main.py#move"></code></pre>'] };
  assert.ok(check('V20', deck(), context).length);
  writeFileSync(join(src, 'examples', 'pygame', 'TESTED.txt'), 'pygame/main.py\n');
  assert.deepEqual(check('V20', deck(), context), []);
});
test('V21: 부와 장의 독립적인 최소 장수를 검사한다', () => {
  assert.deepEqual(check('V21', deck()), []);
  assert.ok(check('V21', deck(card('part0', 'section cover') + card('ch0-start', 'section'))).length);
});
test('V22: 글꼴 검사의 실패나 미실행을 통과시키지 않는다', () => {
  assert.deepEqual(check('V22', deck(), { fontCheck: true }), []);
  assert.ok(check('V22', deck(), { fontCheck: false }).length);
  assert.ok(check('V22', deck()).length);
});
test('V23: 에셋별 라이선스·체크섬·라이선스 파일을 확인한다', (t) => {
  const src = fixture(t);
  const dir = join(src, 'examples', 'assets');
  mkdirSync(dir);
  writeFileSync(join(dir, 'star.txt'), '별');
  writeFileSync(join(dir, 'LICENSE'), 'MIT License');
  const digest = createHash('sha256').update('별').digest('hex');
  const row = `| star.txt | https://example.com/star.txt | v1 | ${digest} | MIT | LICENSE |\n`;
  writeFileSync(join(dir, 'LICENSES.md'), row);
  assert.deepEqual(check('V23', deck(), { src }), []);
  for (const bad of [row.replace('MIT', 'GPL-3.0') + '<!-- MIT -->', row.replace(digest, '0'.repeat(64)), row.replace('LICENSE |', 'missing |')]) {
    writeFileSync(join(dir, 'LICENSES.md'), bad);
    assert.ok(check('V23', deck(), { src }).length);
  }
});
