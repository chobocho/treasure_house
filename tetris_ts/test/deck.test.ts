// test/deck.test.ts — 덱 빌드 시스템 검사.
//
// 덱은 손으로 쓰지 않는다. deck/sections/*.html 조각 + 실제 소스 파일을
// deck/build_deck.py 가 조립한다. 여기서 지키는 건 세 가지다.
//   1) 빌드가 실제로 돈다 (파이썬이 없으면 이 테스트가 먼저 운다)
//   2) 결과물이 자기완결형이다 — 외부 스크립트·폰트·CDN 참조가 하나도 없어야 한다
//   3) 지시자(<!--CODE-->…)가 남김없이 확장되고, 장수·목차·카운터가 서로 맞는다
//
// 소스 전체 커버리지는 섹션을 다 채운 뒤(§7-8)에야 100%가 되므로 여기서는
// "잘라 온 코드가 원본과 한 글자도 다르지 않다"만 확인한다.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..'); // tetris_ts/
const DECK = join(ROOT, '..', 'TypeScript_테트리스_AI_8인_대전.html');

/** 덱을 한 번만 빌드해서 재사용한다. 빌드는 1초도 안 걸리지만 출력은 두 번 볼 일이 많다. */
let built: { out: string; html: string } | null = null;
function build(): { out: string; html: string } {
  if (!built) {
    const out = execFileSync('python3', [join(ROOT, 'deck', 'build_deck.py')], {
      cwd: ROOT, encoding: 'utf8',
    });
    built = { out, html: readFileSync(DECK, 'utf8') };
  }
  return built;
}

test('build_deck.py 가 덱 파일을 만든다', () => {
  const { out } = build();
  assert.match(out, /슬라이드 \d+장/, `빌드 출력에 장수가 없다:\n${out}`);
  assert.ok(existsSync(DECK), '덱 파일이 만들어지지 않았다');
});

test('장수·목차·카운터가 서로 맞는다', () => {
  const { out, html } = build();
  const n = Number(/슬라이드 (\d+)장/.exec(out)![1]);
  const slides = html.match(/<section class="slide"/g) ?? [];
  const links = html.match(/<a href="#s\d+" data-go="\d+"/g) ?? [];
  assert.equal(slides.length, n, '실제 <section> 수와 빌드가 말한 장수가 다르다');
  assert.equal(links.length, n, '목차 항목 수가 장수와 다르다');
  assert.ok(html.includes(`1 / ${n}`), '하단 카운터가 총 장수를 모른다');
  assert.ok(html.includes(`(${n}장)`), '<title> 에 장수가 안 박혔다');
  assert.ok(html.includes(`목차 — 전체 ${n}장`));
});

test('지시자가 남김없이 확장된다', () => {
  const { html } = build();
  for (const d of ['<!--CODE', '<!--SLIDE', '<!--RUN', '<!--BOARD']) {
    assert.ok(!html.includes(d), `${d} 지시자가 그대로 남았다`);
  }
  assert.ok(!html.includes('{{N}}') && !html.includes('{{TOTAL}}'), '치환자가 남았다');
  assert.ok(!/\{\{LINES:/.test(html), 'LINES 치환자가 남았다');
});

/**
 * 코드 블록(인용된 소스)을 걷어 낸 나머지 = 덱 자신의 마크업.
 *
 * 이 덱은 자기 테스트 코드까지 통째로 싣는다. 그래서 여기 적힌 검사 문자열이 덱 본문에
 * 그대로 등장한다 — 외부 리소스를 부르는 게 아니라 **인용된 글자**다. 마크업을 볼 때는
 * 코드 블록을 먼저 걷어 내야 그 둘을 구분할 수 있다.
 */
function markupOnly(html: string): string {
  return html.replace(/<pre class="code[^"]*"><code>[\s\S]*?<\/code><\/pre>/g, '');
}

test('자기완결형이다 — 외부 리소스를 하나도 안 부른다', () => {
  const { html } = build();
  const m = markupOnly(html);
  // <script src> 와 <link> 는 코드 블록 안이면 &lt; 로 이스케이프되므로 전체에서 봐도 안전하다.
  assert.ok(!/<script[^>]+\ssrc=/i.test(html), '외부 <script src> 가 있다');
  assert.ok(!/<link[^>]+rel=["\']?stylesheet/i.test(html), '외부 스타일시트를 참조한다');
  assert.ok(!/@import\s/i.test(m), 'CSS @import 가 있다');
  assert.ok(!/(?:src|href)=["\']https?:\/\//i.test(m), 'http(s) 리소스를 참조한다');
});

test('한글이 깨지지 않는다 (UTF-8 왕복)', () => {
  const { html } = build();
  // 진짜 성질은 "파일 바이트가 올바른 UTF-8 인가"다. 엄격 디코더가 그걸 직접 확인한다.
  new TextDecoder('utf-8', { fatal: true }).decode(readFileSync(DECK));
  assert.ok(!markupOnly(html).includes('\uFFFD'), '치환 문자(U+FFFD)가 있다 — 인코딩이 깨졌다');
  assert.ok(html.includes('테트리스'), '한글 제목이 사라졌다');
});

test('코드 블록은 실제 소스에서 잘라 온 것이다', () => {
  const { html } = build();
  // 뼈대 덱은 tsconfig.json 첫 줄들을 잘라 싣는다. 원문과 한 글자라도 다르면 실패한다.
  const src = readFileSync(join(ROOT, 'tsconfig.json'), 'utf8').split('\n');
  // 하이라이터는 html.escape 를 쓴다 — 따옴표까지 &quot; 로 바뀐다.
  const needle = src.slice(0, 3).join('\n')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const plain = html.replace(/<i class="\w+">/g, '').replace(/<\/i>/g, '');
  assert.ok(plain.includes(needle), 'tsconfig.json 원문이 덱에 그대로 실려 있지 않다');
});

test('커버리지·오버플로 점검이 빌드에 붙어 있다', () => {
  const { out } = build();
  assert.match(out, /소스 커버리지/, '커버리지 보고가 없다');
  assert.match(out, /오버플로 점검/, '오버플로 점검이 없다');
  assert.ok(!out.includes('중복 줄'), `같은 줄을 두 번 실었다:\n${out}`);
});

test('하이라이터가 TypeScript 를 안다', () => {
  const code = 'interface Cfg { readonly n: number }\nexport type X = keyof Cfg;';
  const py = `import sys; sys.path.insert(0, ${JSON.stringify(join(ROOT, 'deck'))});\n` +
    `from hl import highlight; sys.stdout.write(highlight(${JSON.stringify(code)}, 'ts'))`;
  const outHtml = execFileSync('python3', ['-c', py], { encoding: 'utf8' });
  for (const kw of ['interface', 'readonly', 'type', 'export', 'keyof']) {
    assert.ok(outHtml.includes(`<i class="kw">${kw}</i>`), `${kw} 를 키워드로 안 칠했다`);
  }
  assert.ok(outHtml.includes('<i class="ty">number</i>'), 'number 를 타입으로 안 칠했다');
});

test('학습 곡선은 ga_log.json 의 실측값으로 그린다', () => {
  const { html } = build();
  const log = JSON.parse(readFileSync(join(ROOT, 'ga_log.json'), 'utf8')) as
    { gen: number; best: number; mean: number }[];
  assert.ok(html.includes('class="chart"'), '학습 곡선 차트가 덱에 없다');
  const m = /<polyline[^>]*data-series="best"[^>]*points="([^"]+)"/.exec(html);
  assert.ok(m, 'best 계열이 없다');
  const pts = (m as RegExpExecArray)[1]!.trim().split(/\s+/);
  assert.equal(pts.length, log.length, `점 개수가 세대 수와 다르다 (${pts.length} vs ${log.length})`);
  // 최고 적합도는 지어낸 수가 아니라 로그의 최대값이어야 한다.
  const best = Math.max(...log.map((r) => r.best));
  assert.ok(html.includes(String(best)), `최고 적합도 ${best} 가 덱에 안 보인다`);
});
