import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inspectDeck, checkRule, RULE_IDS } from './validate.mjs';

const nav = [{ id: 'part0', label: '0부', kind: 'part', minSlides: 1 }, { id: 'ch0-start', label: '시작', kind: 'chapter', minSlides: 1 }];
const article = (id, cls, heading, body = '<p>탄막 슈팅을 직접 만들며 입력과 이동의 관계를 차근차근 확인합니다.</p>') => `<article class="card ${cls}" id="${id}"><${heading}>제목</${heading}>${body}</article>`;
const main = article('part0', 'section cover', 'h1') + article('ch0-start', 'section', 'h2') + article('p0-start-first', '', 'h3');
const html = `<title>탄막 슈팅</title><span class="brand">탄막 슈팅</span><div id="bar"></div><button id="tocBtn"></button><script>__deckInitHash()</script><select id="nav"><option value="part0">0부</option><option value="ch0-start">시작</option></select><main class="prose">${main}</main>`;

test('V1~V23 검사를 모두 제공한다', () => assert.deepEqual(RULE_IDS, Array.from({ length: 23 }, (_, i) => `V${i + 1}`)));
test('중복 id, 잘못된 제목, 깨진 링크를 잡는다', () => {
  const d = inspectDeck(html.replace('p0-start-first', 'part0').replace('<h3>', '<h2>').replace('</h3>', '</h2>').replace('</main>', '<a href="#missing">x</a></main>'));
  assert.ok(checkRule('V3', d, nav).length);
  assert.ok(checkRule('V4', d, nav).length);
  assert.ok(checkRule('V8', d, nav).length);
});
test('전체 덱 상한과 출처 계약을 지킨다', () => {
  const d = inspectDeck(html);
  assert.deepEqual(checkRule('V2', d, nav), []);
  assert.ok(checkRule('V19', inspectDeck(html.replace('</main>', '<pre><code data-lang="py">x</code></pre></main>')), nav).length);
});
