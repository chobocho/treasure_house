import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { inspectDeck } from './validate.mjs';
import { resolveSnippet } from './snippets.mjs';

test('성능 장 앞부분은 비교 조건과 측정 절차를 실제 코드로 설명한다', () => {
  const html = readFileSync(new URL('parts/48-three-wrap.html', import.meta.url), 'utf8');
  const slides = inspectDeck('<main class="prose">' + html + '</main>').slides;
  assert.ok(slides.length >= 12);
  assert.ok(html.includes('id="ch4-wrap"'));
  assert.ok(html.includes('gl.finish'));
  assert.ok(html.includes('게임 FPS'));
  const refs = [...html.matchAll(/data-src="([^"]+)"/g)].map((match) => match[1]);
  assert.ok(refs.length >= 8);
  for (const ref of refs) assert.ok(resolveSnippet(new URL(ref.startsWith('captures/') ? './' : 'examples/', import.meta.url).pathname, ref, { limit: !ref.startsWith('captures/') }).length > 0, ref);
  assert.equal(new Set(slides.map((slide) => slide.id)).size, slides.length);
});

test('성능 장 중간은 측정 범위와 실제 게임의 갱신 비용을 구분한다', () => {
  const html = readFileSync(new URL('parts/48-three-wrap.html', import.meta.url), 'utf8');
  const { slides } = inspectDeck('<main class="prose">' + html + '</main>');
  const middle = slides.filter((slide) => /^p4-wrap-(1[2-9]|2[0-3])$/.test(slide.id));
  assert.equal(middle.length, 12);
  for (const slide of middle) {
    assert.equal(slide.heading, '3');
    assert.ok((slide.body.replace(/<pre[\s\S]*?<\/pre>/g, '').match(/[가-힣]/g) ?? []).length >= 20, slide.id);
  }
  assert.ok(html.includes('three-ts/profile.mjs#profile'));
  assert.ok(html.includes('three-ts/lv7/render.ts#instance-upload'));
  assert.ok(html.includes('three-ts/lv7/render.ts#draw-hud'));
});

test('완성 성능 장은 목차와 실제 측정 캡처를 연결한다', () => {
  const html = readFileSync(new URL('parts/48-three-wrap.html', import.meta.url), 'utf8');
  const nav = JSON.parse(readFileSync(new URL('nav.json', import.meta.url)));
  assert.equal(inspectDeck('<main class="prose">' + html + '</main>').slides.length, 35);
  assert.equal(nav.find((entry) => entry.id === 'ch4-wrap')?.minSlides, 35);
  assert.equal(nav.find((entry) => entry.id === 'part4')?.minSlides, 335);
  const capture = JSON.parse(readFileSync(new URL('captures/three-profile.txt', import.meta.url)));
  assert.equal(capture.count, 1000);
  assert.deepEqual(capture.results.map((row) => row.calls), [1000, 1]);
  for (const row of capture.results) assert.equal(row.samplesMs.length, 5);
  assert.ok(capture.renderer && capture.browser);
  const captured = readFileSync(new URL('captures/TESTED.txt', import.meta.url), 'utf8').split('\n');
  const tested = readFileSync(new URL('examples/three-ts/TESTED.txt', import.meta.url), 'utf8').split('\n');
  for (const [, ref] of html.matchAll(/data-src="([^"]+)"/g)) {
    const path = ref.split('#')[0];
    assert.ok((path.startsWith('captures/') ? captured : tested).includes(path), ref);
  }
});
