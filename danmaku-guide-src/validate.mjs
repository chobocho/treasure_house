// 생성 문법이 고정된 덱을 의존성 없이 검사한다. 파싱은 O(n) 시간·O(n) 공간이다.
import { readFileSync, existsSync, readdirSync, statSync, realpathSync } from 'node:fs';
import { dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { resolveSnippet } from './snippets.mjs';

export const SRC = dirname(fileURLToPath(import.meta.url));
export const ROOT = resolve(SRC, '..');
export const OUT = join(ROOT, '탄막-슈팅-가이드.html');
export const FONT_TOOL = '/root/github/treasure_house/tools/embed_mono_font.py';
export const RULE_IDS = Array.from({ length: 23 }, (_, i) => `V${i + 1}`);
const LANGS = new Set('js ts py c cpp go rust java lua rb sh sql lisp html css json yaml http bas text'.split(' '));
export const attr = (text, key) => text.match(new RegExp(`(?:^|\\s)${key}\\s*=\\s*(["'])(.*?)\\1`))?.[2];
const classes = (attrs) => (attr(attrs, 'class') ?? '').split(/\s+/);
const ids = (text) => [...text.matchAll(/<[^!][^>]*>/g)].map((m) => attr(m[0].replace(/^<\/?[\w-]+/, ''), 'id')).filter(Boolean);
const textOnly = (html) => html.replace(/<pre\b[\s\S]*?<\/pre>/g, '').replace(/<[^>]+>/g, '').replace(/&[a-z]+;/g, ' ');
const problem = (condition, message) => condition ? [message] : [];
const codeBlocks = (html) => [...html.matchAll(/<pre\b[^>]*>\s*<code\b([^>]*)>([\s\S]*?)<\/code>\s*<\/pre>/g)];
const scripts = (html) => [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]).join('\n');
const registrations = (html) => [...scripts(html).matchAll(/\b__demo\s*\(\s*['"]([^'"]+)['"]\s*,/g)].map((m) => m[1]);
const references = (parts) => parts.flatMap((part) => [...part.matchAll(/\bdata-src\s*=\s*(["'])(.*?)\1/g)].map((m) => m[2]));
const markupOnly = (html) => html.replace(/<!--[^]*?-->/g, '').replace(/(<(script|style)\b[^>]*>)[\s\S]*?(<\/\2>)/g, '$1$3');

export function inspectDeck(input) {
  let html;
  let validUtf8 = true;
  try { html = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.isBuffer(input) ? input : Buffer.from(input)); }
  catch { validUtf8 = false; html = Buffer.from(input).toString('utf8'); }
  const main = html.match(/<main\b[^>]*class="prose"[^>]*>([\s\S]*?)<\/main>/)?.[1] ?? '';
  const slides = [...main.matchAll(/<article\b([^>]*)>([\s\S]*?)<\/article>/g)].map((m) => {
    const cls = classes(m[1]);
    return { id: attr(m[1], 'id'), attrs: m[1], body: m[2], classes: cls,
      heading: m[2].match(/<h([1-6])\b/)?.[1], cover: cls.includes('cover'), section: cls.includes('section'), quiz: cls.includes('quiz') };
  });
  return { html, main, slides, validUtf8, bytes: Buffer.isBuffer(input) ? input.length : Buffer.byteLength(input) };
}

function ranges(deck, nav) {
  return nav.map((entry) => {
    const start = deck.slides.findIndex((s) => s.id === entry.id);
    const next = deck.slides.findIndex((s, i) => i > start && nav.some((n) => n.id === s.id && (entry.kind === 'chapter' || n.kind === 'part')));
    return { entry, start, end: next < 0 ? deck.slides.length : next };
  });
}

function checkSources(parts, src) {
  const errors = [];
  for (const part of parts) {
    const preCount = [...part.matchAll(/<pre\b/g)].length;
    const blocks = codeBlocks(part);
    if (preCount !== blocks.length) errors.push('pre에는 출처를 가진 code 하나만 넣어야 한다');
    for (const [, attrs, literal] of blocks) {
      const ref = attr(attrs, 'data-src');
      if (!ref || literal.trim()) { errors.push('조각 코드에는 data-src만 있어야 한다'); continue; }
      try { resolveSnippet(join(src, 'examples'), ref); } catch (e) { errors.push(e.message); }
    }
    for (const ref of references([part]).filter((ref) => ref.startsWith('captures/'))) {
      try { resolveSnippet(src, ref, { limit: false }); } catch (e) { errors.push(e.message); }
    }
  }
  return errors;
}

function checkCoverage(parts, src) {
  return references(parts).flatMap((ref) => {
    const file = ref.split('#')[0];
    const [track] = file.split('/');
    const manifest = track === 'captures' ? join(src, 'captures', 'TESTED.txt') : join(src, 'examples', track, 'TESTED.txt');
    return problem(!existsSync(manifest) || !readFileSync(manifest, 'utf8').split(/\r?\n/).includes(file), `실행 검증 목록 누락: ${file}`);
  });
}

function checkAssets(src) {
  const dir = join(src, 'examples', 'assets');
  if (!existsSync(dir)) return [];
  const files = readdirSync(dir, { recursive: true }).filter((name) => statSync(join(dir, name)).isFile() && name !== 'LICENSES.md');
  if (!files.length) return [];
  const manifest = join(dir, 'LICENSES.md');
  if (!existsSync(manifest)) return ['에셋 목록 LICENSES.md가 없다'];
  const rows = readFileSync(manifest, 'utf8').split(/\r?\n/).filter((line) => line.startsWith('|')).map((line) => line.split('|').slice(1, -1).map((cell) => cell.trim().replace(/^`|`$/g, ''))).filter((cells) => cells.length === 6 && /^[a-f0-9]{64}$/.test(cells[3]));
  const errors = [];
  const accounted = new Set();
  for (const [path, url, revision, digest, license, licensePath] of rows) {
    const allowed = ['MIT', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0', 'CC0', 'CC0-1.0'].includes(license);
    const asset = resolve(dir, path);
    const licenseFile = resolve(dir, licensePath);
    const inside = (file) => file.startsWith(resolve(dir) + sep) && existsSync(file) && statSync(file).isFile() && realpathSync(file).startsWith(realpathSync(dir) + sep);
    if (!allowed || !/^https:\/\//.test(url) || !revision || !inside(asset) || !inside(licenseFile)) { errors.push(`에셋 출처·라이선스 오류: ${path}`); continue; }
    if (createHash('sha256').update(readFileSync(asset)).digest('hex') !== digest) errors.push(`에셋 체크섬 불일치: ${path}`);
    accounted.add(path);
    accounted.add(licensePath);
  }
  for (const file of files) if (!accounted.has(file)) errors.push(`에셋 라이선스 누락: ${file}`);
  return errors;
}

export function checkRule(id, d, nav = [], context = {}) {
  const s = d.slides;
  const src = context.src ?? SRC;
  switch (id) {
    case 'V1': return problem(!d.html || !d.validUtf8 || d.html.includes('\uFFFD') || /[\u00C3\u00C2\u00EC\u00ED\u00EA\u00EB]{2,}/.test(d.html), 'UTF-8 또는 파일 존재 오류');
    case 'V2': { const count = s.filter((slide) => slide.classes.includes('card')).length; return problem(count < 1 || count > 2000, `슬라이드 수 ${count}장: 허용 1~2000장`); }
    case 'V3': {
      const seen = new Set();
      return s.flatMap((slide) => { const bad = !slide.id || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slide.id) || seen.has(slide.id); seen.add(slide.id); return problem(bad, `잘못되거나 중복된 id: ${slide.id}`); });
    }
    case 'V4': return s.flatMap((slide) => problem(!slide.classes.includes('card') || slide.heading !== (slide.cover ? '1' : slide.section ? '2' : '3'), `제목 단계 또는 카드 클래스 오류: ${slide.id}`));
    case 'V5': return problem([...d.main.matchAll(/<[^>]+>/g)].some((m) => classes(m[0]).includes('pno')), '수동 페이지 번호');
    case 'V6': return problem(/[\u2500-\u257f]/.test(d.html), '박스 문자');
    case 'V7': return problem(/<script\b[^>]*\bsrc\s*=|<link\b[^>]*\brel\s*=\s*['"]stylesheet['"]|@import|url\(\s*['"]?https?:/i.test(d.html), '외부 리소스');
    case 'V8': { const markup = markupOnly(d.html); const targets = new Set(ids(markup)); return [...markup.matchAll(/\bhref\s*=\s*['"]#([^'"]+)['"]/g)].flatMap((m) => { let target; try { target = decodeURIComponent(m[1]); } catch { return [`잘못된 링크: #${m[1]}`]; } return problem(!targets.has(target), `깨진 링크: #${m[1]}`); }); }
    case 'V9': {
      const navIds = nav.map((x) => x.id);
      const sections = s.filter((x) => x.section).map((x) => x.id);
      const select = [...d.html.matchAll(/<select\b([^>]*)>([\s\S]*?)<\/select>/g)].find((m) => attr(m[1], 'id') === 'nav');
      const options = [...(select?.[2] ?? '').matchAll(/<option\b([^>]*)>/g)].map((m) => attr(m[1], 'value')).filter(Boolean);
      return [...problem(JSON.stringify(navIds) !== JSON.stringify(sections), 'nav.json과 구간 id·순서가 다르다'), ...problem(JSON.stringify(navIds) !== JSON.stringify(options), 'nav.json과 select 항목이 다르다'), ...problem(new Set(navIds).size !== navIds.length, 'nav.json id 중복')];
    }
    case 'V10': return codeBlocks(d.main).flatMap((m) => problem(!LANGS.has(attr(m[1], 'data-lang')), '코드 언어 오류'));
    case 'V11': return codeBlocks(d.main).flatMap((m) => problem(/<[A-Za-z/!]/.test(m[2]), '이스케이프되지 않은 코드'));
    case 'V12': return s.filter((x) => !x.cover && (textOnly(x.body).match(/[가-힣]/g) ?? []).length < 20).map((x) => `한글 부족: ${x.id}`);
    case 'V13': return s.filter((x) => textOnly(x.body).length > 6000).map((x) => `본문 과다: ${x.id}`);
    case 'V14': return [...problem(s.length > 0 && s.filter((x) => x.quiz).length / s.length > .12, '퀴즈 비율 초과'), ...ranges(d, nav).filter(({ entry }) => entry.kind === 'chapter').flatMap(({ entry, start, end }) => problem(start < 0 || s.slice(start + 1, end).filter((x) => !x.quiz && !x.section).length < 5, `장 슬라이드 부족: ${entry.id}`))];
    case 'V15': {
      const demos = [...d.main.matchAll(/\bdata-demo=['"]([^'"]+)['"]/g)].map((m) => m[1]);
      // 템플릿 스크립트는 원문 보존 계약이 있어 사용하지 않는 예제 등록도 남는다.
      const inherited = registrations(context.template ?? '');
      const regs = registrations(d.html).filter((x) => !inherited.includes(x) || demos.includes(x));
      return [...demos.filter((x) => !regs.includes(x)).map((x) => `데모 등록 누락: ${x}`), ...regs.filter((x) => !demos.includes(x)).map((x) => `데모 대상 누락: ${x}`), ...problem(new Set(demos).size !== demos.length || new Set(regs).size !== regs.length, '데모 id 중복')];
    }
    case 'V16': {
      const title = d.html.match(/<title>([^<]*)<\/title>/)?.[1];
      const brand = d.html.match(/class=['"]brand['"]>([^<]*)</)?.[1];
      return problem(!title?.trim() || !brand?.trim() || [title, brand].some((x) => x?.includes('슬라이드 덱 템플릿')), '제목·브랜드 누락 또는 템플릿 기본값');
    }
    case 'V17': return problem(d.bytes >= 12 * 1024 * 1024, '파일 크기 초과');
    case 'V18': return ['__deckInitHash', 'id="tocBtn"', 'id="bar"', 'bookmark'].flatMap((x) => problem(!d.html.includes(x), `템플릿 기능 누락: ${x}`));
    case 'V19': return context.parts ? checkSources(context.parts, src) : problem(codeBlocks(d.main).length > 0, '원본 조각을 제공해야 코드 출처를 검증할 수 있다');
    case 'V20': return checkCoverage(context.parts ?? [d.main], src);
    case 'V21': return ranges(d, nav).flatMap(({ entry, start, end }) => problem(start < 0 || end - start < entry.minSlides, `최소 장수 부족: ${entry.id}`));
    case 'V22': {
      if (typeof context.fontCheck === 'boolean') return problem(!context.fontCheck, '내장 고정폭 글꼴 검사 실패');
      if (!d.file || !existsSync(d.file)) return ['글꼴 검사 대상 파일이 없다'];
      const result = spawnSync('python3', [FONT_TOOL, '--check', d.file], { encoding: 'utf8' });
      return problem(result.status !== 0, `내장 고정폭 글꼴 검사 실패: ${result.error?.message ?? result.stderr ?? result.stdout}`);
    }
    case 'V23': return checkAssets(src);
    default: throw new Error(`알 수 없는 규칙: ${id}`);
  }
}

export function validate(deck, nav, context = {}) {
  return Object.fromEntries(RULE_IDS.map((id) => [id, checkRule(id, deck, nav, context)]));
}

export function loadContext(src = SRC) {
  return { src, parts: readdirSync(join(src, 'parts')).filter((name) => name.endsWith('.html')).sort().map((name) => readFileSync(join(src, 'parts', name), 'utf8')), template: readFileSync(join(ROOT, 'template.html'), 'utf8') };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const deck = { ...inspectDeck(existsSync(OUT) ? readFileSync(OUT) : ''), file: OUT };
  const nav = JSON.parse(readFileSync(join(SRC, 'nav.json'), 'utf8'));
  const errors = validate(deck, nav, loadContext());
  for (const [id, messages] of Object.entries(errors)) console[ messages.length ? 'error' : 'log'](`${id}: ${messages.length ? messages.join('; ') : '통과'}`);
  if (Object.values(errors).some((x) => x.length)) process.exitCode = 1;
}
