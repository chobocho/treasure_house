// 템플릿 엔진을 그대로 보존하면서 본문·출처·목차만 조립한다.
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { resolveSnippet } from './snippets.mjs';
import { writeAppendix } from './appendix.mjs';
import { figureSvg } from './examples/foundations/figures.mjs';

const SRC = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(SRC, '..');
const OUT = join(ROOT, '탄막-슈팅-가이드.html');
const attr = (text, key) => text.match(new RegExp(`(?:^|\\s)${key}\\s*=\\s*(["'])(.*?)\\1`))?.[2];
const esc = (text) => String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function fillSources(part, src) {
  let count = 0;
  // 그림은 예제와 같은 함수로 좌표를 계산한 SVG를 그대로 넣어 공식과 그림이 어긋나지 않게 한다.
  part = part.replace(/<div class="fig" data-fig="([A-Za-z0-9]+)">([\s\S]*?)<\/div>/g, (_match, name, literal) => {
    if (literal.trim()) throw new Error('그림 자리는 비어 있어야 한다');
    return `<div class="fig">${figureSvg(name)}</div>`;
  });
  if (/\bdata-fig\s*=/.test(part)) throw new Error('그림은 빈 div.fig와 data-fig로만 넣는다');
  const html = part.replace(/<pre\b([^>]*)>\s*<code\b([^>]*)>([\s\S]*?)<\/code>\s*<\/pre>/g, (_match, preAttrs, codeAttrs, literal) => {
    count++;
    const ref = attr(codeAttrs, 'data-src');
    if (!ref || literal.trim()) throw new Error('모든 코드 블록은 빈 내용과 data-src를 가져야 한다');
    const code = resolveSnippet(join(src, 'examples'), ref);
    const attrs = codeAttrs.replace(/\s+data-src\s*=\s*(["']).*?\1/, '');
    return `<pre${preAttrs}><code${attrs}>${code}</code></pre>`;
  }).replace(/<(div|p)\b([^>]*\bdata-src\s*=\s*(["']).*?\3[^>]*)>([\s\S]*?)<\/\1>/g, (_match, tag, attrs, _quote, literal) => {
    const ref = attr(attrs, 'data-src');
    if (!(attr(attrs, 'class') ?? '').split(/\s+/).includes('term') || !ref.startsWith('captures/') || literal.trim()) throw new Error('터미널 캡처는 빈 .term과 captures/ 출처를 사용해야 한다');
    const text = resolveSnippet(src, ref, { limit: false });
    return `<${tag}${attrs.replace(/\s+data-src\s*=\s*(["']).*?\1/, '')}>${text}</${tag}>`;
  });
  if (count !== [...part.matchAll(/<pre\b/g)].length) throw new Error('pre에는 출처를 가진 code 하나만 넣어야 한다');
  if (/<[^>]*\bdata-src\s*=/.test(html)) throw new Error('해결하지 못한 data-src가 있다');
  return html;
}

function replaceRequired(html, pattern, value, name) {
  if (!pattern.test(html)) throw new Error(`템플릿 위치를 찾을 수 없다: ${name}`);
  return html.replace(pattern, () => value);
}

export function assemble({ template, parts, nav, src = SRC, demos = '' }) {
  if (!nav.length || new Set(nav.map((entry) => entry.id)).size !== nav.length) throw new Error('목차가 비었거나 id가 중복된다');
  const main = parts.map((part) => fillSources(part.trim(), src)).join('\n\n');
  let html = template;
  html = replaceRequired(html, /<title>[^<]*<\/title>/, '<title>탄막 슈팅 가이드 · 네 가지 구현과 일곱 단계</title>', 'title');
  html = replaceRequired(html, /<meta name="description" content="[^"]*">/, '<meta name="description" content="pygame, Canvas, Three.js, C++ wasm으로 같은 탄막 슈팅을 만드는 실습 가이드">', 'description');
  html = replaceRequired(html, /<span class="brand">[^<]*<\/span>/, '<span class="brand">🎮 탄막 슈팅 가이드</span>', 'brand');
  const options = ['<option value="">챕터 이동…</option>', ...nav.map((entry) => `<option value="${esc(entry.id)}">${entry.kind === 'chapter' ? '· ' : ''}${esc(entry.label)}</option>`)];
  html = replaceRequired(html, /<select id="nav"[^>]*>[\s\S]*?<\/select>/, `<select id="nav" aria-label="챕터 이동">\n${options.join('\n')}\n</select>`, 'nav');
  html = replaceRequired(html, /<main class="prose">[\s\S]*?<\/main>/, `<main class="prose">\n${main}\n</main>`, 'main');
  // CSS 설명의 태그가 글꼴 추출 범위를 본문까지 늘리지 않도록 주석 안에서만 이스케이프한다.
  html = html.replace(/<style\b[^>]*>[\s\S]*?<\/style>/g, (style) => style.replace(/\/\*[\s\S]*?\*\//g, (comment) => comment.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/[\u2500-\u257f]/g, (c) => `U+${c.codePointAt(0).toString(16).toUpperCase()}`)));
  if (/<\/script/i.test(demos)) throw new Error('데모 소스에 script 종료 태그가 있다');
  if (demos.trim()) html = replaceRequired(html, /<\/body>/, `<script>\n${demos}\n</script>\n</body>`, 'body');
  return html.replace(/\r\n/g, '\n');
}

export function slideCounts(html, nav) {
  const main = html.match(/<main class="prose">([\s\S]*?)<\/main>/)?.[1] ?? '';
  const articles = [...main.matchAll(/<article\b([^>]*)>/g)].filter((m) => (attr(m[1], 'class') ?? '').split(/\s+/).includes('card')).map((m) => attr(m[1], 'id'));
  const groups = nav.filter((entry) => entry.kind === 'part');
  return groups.map((entry, index) => {
    const start = articles.indexOf(entry.id);
    const end = index + 1 < groups.length ? articles.indexOf(groups[index + 1].id) : articles.length;
    if (start < 0 || end < start) throw new Error(`부 경계가 잘못되었다: ${entry.id}`);
    return { id: entry.id, count: end - start };
  });
}

export function build() {
  writeAppendix();
  const nav = JSON.parse(readFileSync(join(SRC, 'nav.json'), 'utf8'));
  const files = readdirSync(join(SRC, 'parts')).filter((name) => name.endsWith('.html')).sort();
  const parts = files.map((name) => readFileSync(join(SRC, 'parts', name), 'utf8'));
  const demoFiles = ['demos.js', 'dist/pattern-demo.js', 'dist/canvas-demo.js', 'dist/three-demo.js', 'dist/wasm-demo.js'];
  const demos = demoFiles.filter((name) => existsSync(join(SRC, name))).map((name) => readFileSync(join(SRC, name), 'utf8')).join('\n');
  const html = assemble({ template: readFileSync(join(ROOT, 'template.html'), 'utf8'), parts, nav, demos });
  writeFileSync(OUT, html, 'utf8');
  execFileSync('python3', ['/root/github/treasure_house/tools/embed_mono_font.py', OUT], { stdio: 'inherit' });
  const counts = slideCounts(html, nav);
  for (const { id, count } of counts) {
    const entry = nav.find((item) => item.id === id);
    console.log(`${entry.label}: ${count}장 / 최소 ${entry.minSlides}장`);
  }
  console.log(`총 ${counts.reduce((sum, item) => sum + item.count, 0)}장 → ${OUT}`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) build();
