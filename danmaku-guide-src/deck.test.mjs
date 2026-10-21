import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { Script } from 'node:vm';
import { SRC, ROOT, OUT, inspectDeck, validate, loadContext } from './validate.mjs';

test('실제 산출물의 구조·출처·에셋·글꼴 검사를 실행한다', () => {
  const d = { ...inspectDeck(readFileSync(OUT)), file: OUT };
  const nav = JSON.parse(readFileSync(join(SRC, 'nav.json'), 'utf8'));
  const result = validate(d, nav, loadContext());
  // 전체 장수 하한이 해제되어 제작 중에도 모든 규칙을 동일하게 적용한다.
  for (const [id, errors] of Object.entries(result)) assert.deepEqual(errors, [], id);
  assert.ok(d.slides.length >= 1 && d.slides.length <= 2000);
});

test('실제 산출물은 템플릿 스크립트를 보존하고 모든 스크립트 문법이 유효하다', () => {
  const html = readFileSync(OUT, 'utf8');
  const template = readFileSync(join(ROOT, 'template.html'), 'utf8');
  const blocks = (source) => [...source.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)];
  assert.deepEqual(blocks(html).slice(0, blocks(template).length).map((m) => m[0]), blocks(template).map((m) => m[0]));
  for (const [index, block] of blocks(html).entries()) assert.doesNotThrow(() => new Script(block[1], { filename: `inline-${index}.js` }));
  assert.ok(!html.includes('\r'));
  assert.ok(!html.startsWith('\uFEFF'));
});

test('부 표지는 목차 그룹을 새로 열고 덱 표지만 cover를 쓴다', () => {
  const html = readFileSync(OUT, 'utf8');
  const main = html.slice(html.indexOf('<main'));
  // 템플릿 목차는 cover가 아닌 section 슬라이드만 그룹 제목으로 삼는다. 같은 규칙을 그대로 재현한다.
  let group = '표지';
  for (const [, cls, id, body] of main.matchAll(/<article class="(card[^"]*)" id="([^"]+)"[^>]*>([\s\S]*?)<\/article>/g)) {
    const names = cls.split(/\s+/);
    if (names.includes('section') && !names.includes('cover')) {
      const h = body.match(/<h[12][^>]*>([\s\S]*?)<\/h[12]>/);
      group = h ? h[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim() : '';
    }
    if (!/^part[1-9]$/.test(id)) continue;
    assert.ok(!names.includes('cover'), id + '는 덱 표지가 아니므로 cover를 쓰지 않는다');
    const own = body.match(/<h[12][^>]*>([\s\S]*?)<\/h[12]>/);
    assert.ok(own, id + '에 제목이 있어야 한다');
    assert.equal(group, own[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim(), id + '의 목차 그룹');
  }
});

test('공개 덱에 작성 환경의 절대 경로가 남지 않는다', () => {
  const html = readFileSync(OUT, 'utf8');
  assert.equal(html.match(/\/(?:root|home)\/[^\s"<]*treasure_house[^\s"<]*/)?.[0] ?? null, null);
});
