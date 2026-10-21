import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';
import { assemble } from './build.mjs';

const src = new URL('./', import.meta.url);
const scriptBlocks = (html) => [...html.matchAll(/<script\b[^>]*>[\s\S]*?<\/script>/g)].map((m) => m[0]);
const template = '<title>슬라이드 덱 템플릿</title><meta name="description" content="기본"><span class="brand">기본</span><select id="nav"></select><main class="prose"></main><script>window.templateKept = "$&";</script></body>';
const nav = [{ id: 'part0', label: '처음 & 시작', kind: 'part', minSlides: 1 }];

test('빌드는 출처를 추출·이스케이프하고 템플릿 스크립트를 그대로 보존한다', async (t) => {
  const root = mkdtempSync(join(tmpdir(), 'danmaku-build-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, 'examples', 'canvas-ts'), { recursive: true });
  const file = join(root, 'examples', 'canvas-ts', 'main.mjs');
  writeFileSync(file, '// #region run\nconsole.log("<이동>&");\n// #endregion\n');
  assert.equal(execFileSync('node', [file], { encoding: 'utf8' }).trim(), '<이동>&');
  const output = assemble({ template, nav, src: root, parts: ['<article class="card section cover" id="part0"><h1>탄막</h1><pre><code data-lang="js" data-src="canvas-ts/main.mjs#run"></code></pre></article>'], demos: 'window.newDemo = true;' });
  assert.ok(output.includes('console.log("&lt;이동&gt;&amp;");'));
  assert.ok(!output.includes('data-src='));
  assert.ok(output.includes('처음 &amp; 시작'));
  assert.deepEqual(scriptBlocks(output).slice(0, 1), scriptBlocks(template));
  assert.ok(output.includes('window.newDemo = true;'));
  writeFileSync(file, '// #region run\nconsole.log("data-src=memory");\n// #endregion\n');
  assert.equal(execFileSync('node', [file], { encoding: 'utf8' }).trim(), 'data-src=memory');
  const textOutput = assemble({ template, nav, src: root, parts: ['<pre><code data-lang="js" data-src="canvas-ts/main.mjs#run"></code></pre>'] });
  assert.ok(textOutput.includes('console.log("data-src=memory");'));
});

test('터미널 캡처는 실제 출력 파일에서 읽고 HTML을 이스케이프한다', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'danmaku-capture-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, 'captures'));
  const capture = execFileSync('node', ['-e', 'console.log("<완료>&")'], { encoding: 'utf8' });
  writeFileSync(join(root, 'captures', 'run.txt'), capture);
  const output = assemble({ template, nav, src: root, parts: ['<div class="term" data-src="captures/run.txt"></div>'] });
  assert.ok(output.includes('<div class="term">&lt;완료&gt;&amp;</div>'));
});

test('그림은 figures 모듈의 SVG를 인라인하고 잘못된 그림 자리는 거부한다', () => {
  const output = assemble({ template, nav, parts: ['<div class="fig" data-fig="ring"></div>'] });
  assert.match(output, /<div class="fig"><svg [^>]*role="img"/);
  assert.ok(!output.includes('data-fig='));
  for (const bad of ['<div class="fig" data-fig="missing"></div>', '<div class="fig" data-fig="ring">글</div>', '<p data-fig="ring"></p>']) {
    assert.throws(() => assemble({ template, nav, parts: [bad] }));
  }
});

test('빌드는 리터럴·출처 누락·없는 파일·경로 이탈을 거부한다', async () => {
  for (const code of ['<pre><code data-lang="py">print(1)</code></pre>', '<pre><code data-lang="py"></code></pre>', '<pre><code data-lang="py" data-src="pygame/missing.py#run"></code></pre>', '<pre><code data-lang="py" data-src="../../template.html"></code></pre>']) {
    assert.throws(() => assemble({ template, nav, src: new URL('.', import.meta.url).pathname, parts: [code] }));
  }
});

test('T0 0부는 고유 id를 가진 최소 열 장과 일반 슬라이드 다섯 장을 제공한다', async () => {
  const progress = readFileSync(new URL('PROGRESS.md', src), 'utf8');
  let parts = [];
  try { parts = [readFileSync(new URL('parts/00-intro.html', src), 'utf8')]; } catch {}
  const { inspectDeck, validate } = await import('./validate.mjs');
  const actualNav = JSON.parse(readFileSync(new URL('nav.json', src), 'utf8')).filter((entry) => ['part0', 'ch0-start'].includes(entry.id));
  const actualTemplate = readFileSync(new URL('../template.html', src), 'utf8');
  const output = assemble({ template: actualTemplate, nav: actualNav, parts, src: src.pathname });
  const d = inspectDeck(output);
  assert.ok(d.slides.length >= 10);
  assert.ok(progress.includes('T0'));
  const result = validate(d, actualNav, { parts, template: actualTemplate, fontCheck: true });
  for (const id of Object.keys(result)) assert.deepEqual(result[id], [], id);
  assert.deepEqual(scriptBlocks(output).slice(0, scriptBlocks(actualTemplate).length), scriptBlocks(actualTemplate));
});

test('장수 집계는 스크립트의 article 예시 문자열을 세지 않는다', async () => {
  const { slideCounts } = await import('./build.mjs');
  const html = '<main class="prose"><article class="card" id="part0"></article></main><script>/* <article class="card" id="example"> */</script>';
  assert.deepEqual(slideCounts?.(html, nav) ?? [], [{ id: 'part0', count: 1 }]);
});

test('CSS 설명의 태그 표기는 글꼴 추출기가 실제 요소로 오인하지 않게 한다', () => {
  const source = '<style>/* <code> 요소와 \u2500 장식을 설명한다. */</style>' + template;
  const output = assemble({ template: source, nav, parts: [], src: src.pathname });
  assert.ok(!output.includes('/* <code>'));
  assert.ok(output.includes('&lt;code&gt;'));
});
