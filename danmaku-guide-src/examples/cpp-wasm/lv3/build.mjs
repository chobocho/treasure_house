import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const src = new URL('../../../', import.meta.url);
const file = (p) => fileURLToPath(new URL(p, src));
const run = (cmd, args) => execFileSync(cmd, args, { cwd: src, stdio: 'inherit' });
mkdirSync(new URL('dist/', src), { recursive: true });
// #region lv3-build
const common = ['-std=c++20', '-O2', '-Wall', '-Wextra', '-Werror', '-ffp-contract=off'];
run(process.env.NATIVE_CXX || 'g++', [...common,
  file('examples/cpp-wasm/lv3/game.cpp'), file('examples/cpp-wasm/lv3/test_game.cpp'),
  '-o', file('dist/wasm-lv3-native')]);
run(file('dist/wasm-lv3-native'), []);
run(process.env.WASM_CXX || 'clang++', [...common, '--target=wasm32',
  '-ffreestanding', '-nostdlib', '-fno-exceptions', '-fno-rtti',
  '-c', file('examples/cpp-wasm/lv3/game.cpp'), '-o', file('dist/wasm-lv3.o')]);
run(process.env.WASM_LD || 'wasm-ld', ['--no-entry', '--export-memory',
  '--initial-memory=1048576', '--max-memory=1048576',
  file('dist/wasm-lv3.o'), '-o', file('dist/wasm-lv3.wasm')]);
// #endregion

// #region lv3-offline-page
const bytes = readFileSync(new URL('dist/wasm-lv3.wasm', src));
const scripts = ['examples/cpp-wasm/lv3/replay.mjs', 'examples/cpp-wasm/memory-glue.mjs',
  'examples/cpp-wasm/lv3/main.js'].map((p) => readFileSync(new URL(p, src), 'utf8')).join('\n');
const html = `<!doctype html><html lang="ko"><meta charset="utf-8">
<title>C++ wasm Lv3 · 이동과 발사</title>
<style>body{background:#101827;color:white;font-family:sans-serif}canvas{max-width:100%;height:auto;outline:2px solid #64748b}canvas:focus{outline-color:#5eead4}</style>
<h1>C++ wasm Lv3 · 네 가지 탄막 패턴</h1><p id="status" role="status">불러오는 중입니다.</p><p id="hud"></p>
<canvas width="480" height="640" tabindex="0" aria-label="탄막 게임 화면"></canvas>
<script id="wasm-bytes" type="application/octet-stream">${bytes.toString('base64')}</script>
<script type="module">${scripts}</script></html>`;
writeFileSync(new URL('dist/wasm-lv3.html', src), html);
// #endregion
