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
