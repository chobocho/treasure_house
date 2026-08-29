// tools/bundle_web.mjs — tsc 결과(dist/)를 덱·브라우저용 평범한 스크립트로 바꾼다.
//
// 왜 번들러가 필요한가: 덱은 단일 HTML 파일이라 <script type="module"> 이 임포트할
// 상대 경로가 없다. 그렇다고 데모를 위해 코드를 따로 손으로 옮겨 적으면 슬라이드의
// 코드와 도는 코드가 갈라진다. 그래서 컴파일 결과에서 import/export **문법만** 걷어
// 내고 순서대로 이어 붙인다. 최상위 const/class 는 클래식 스크립트끼리 서로 보이므로
// (선언적 전역 환경을 공유한다) 이것만으로 모듈 경계가 사라진다.
//
// 안전장치 둘:
//   1) 상대 임포트가 아닌 것(node:http 같은)이 있으면 멈춘다 — 브라우저에서 못 돈다.
//   2) 파일을 넘나드는 최상위 이름이 겹치면 멈춘다. 모듈이었을 땐 괜찮던 충돌이
//      한 전역에 모이는 순간 조용히 서로를 덮어쓰기 때문이다.
//
//   node tools/bundle_web.mjs

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, basename } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const DIST = join(ROOT, 'dist', 'src');
const OUTD = join(ROOT, 'web', 'js');

// 브라우저에 실을 모듈만 고른다. ws/server 는 node 전용, trace 는 검증 도구다.
const MODULES = [
  'core.js', 'ai.js', 'ga.js', 'battle.js', 'net/protocol.js', 'net/room.js',
  'view.js', 'ga_view.js', 'demo.js',   // ← 화면·데모 글루. demo.js 가 window.__mountDemo 를 건다.
];

const IMPORT_RE = /^import\s[^\n]*?from\s*['"]([^'"]+)['"];?\s*$/gm;
const BARE_IMPORT_RE = /^import\s*['"]([^'"]+)['"];?\s*$/gm;
/** 최상위 선언 이름 — 열 0에서 시작하는 것만 본다(들여쓴 건 함수 안이다). */
const DECL_RE = /^(?:export\s+)?(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)/gm;

function strip(src, file) {
  for (const m of src.matchAll(IMPORT_RE)) {
    if (!m[1].startsWith('.')) throw new Error(`${file}: 브라우저에 못 싣는 임포트 ${m[1]}`);
  }
  for (const m of src.matchAll(BARE_IMPORT_RE)) {
    throw new Error(`${file}: 부수효과 임포트 ${m[1]} 는 번들이 다루지 않는다`);
  }
  return src
    .replace(IMPORT_RE, '')            // 상대 임포트는 통째로 지운다 (같은 전역에 이미 있다)
    .replace(/^export\s+default\s+/gm, '')
    .replace(/^export\s+/gm, '')
    .replace(/^\{[^}]*\}\s*;?\s*$/gm, '') // `export { a, b };` 가 남긴 껍데기
    .replace(/\n{3,}/g, '\n\n')
    .trimStart();
}

mkdirSync(OUTD, { recursive: true });
const seen = new Map();
const made = [];
for (const rel of MODULES) {
  const src = readFileSync(join(DIST, rel), 'utf8');
  const out = strip(src, rel);
  for (const m of out.matchAll(DECL_RE)) {
    const name = m[1];
    if (seen.has(name)) throw new Error(`최상위 이름 충돌: ${name} (${seen.get(name)} ↔ ${rel})`);
    seen.set(name, rel);
  }
  const name = basename(rel);
  const head = `// 생성물 — tools/bundle_web.mjs 가 dist/src/${rel} 에서 만든다. 직접 고치지 말 것.\n`
    + `// 원본은 src/${rel.replace(/\.js$/, '.ts')} 이고, 여기서는 import/export 만 걷어냈다.\n`;
  writeFileSync(join(OUTD, name), head + out, 'utf8');
  made.push(`${name} (${(head.length + out.length) / 1024 < 1 ? '<1' : Math.round((head.length + out.length) / 1024)} KB)`);
}
console.log(`web/js/ 에 ${made.length}개 생성 — ${made.join(', ')}`);
console.log(`최상위 이름 ${seen.size}개, 충돌 없음`);
