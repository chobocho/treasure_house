import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { buildSync } from 'esbuild';
const src = new URL('../../../', import.meta.url);
const file = (p) => fileURLToPath(new URL(p, src));
const run = (cmd, args) => execFileSync(cmd, args, { cwd: src, stdio: 'inherit' });
mkdirSync(new URL('dist/', src), { recursive: true });
// #region lv7-build
const common = ['-std=c++20', '-O2', '-Wall', '-Wextra', '-Werror', '-ffp-contract=off'];
run(process.env.NATIVE_CXX || 'g++', [...common,
  file('examples/cpp-wasm/lv7/game.cpp'), file('examples/cpp-wasm/lv7/test_game.cpp'),
  '-o', file('dist/wasm-lv7-native')]);
run(file('dist/wasm-lv7-native'), []);
run(process.env.WASM_CXX || 'clang++', [...common, '--target=wasm32',
  '-ffreestanding', '-nostdlib', '-fno-exceptions', '-fno-rtti',
  '-c', file('examples/cpp-wasm/lv7/game.cpp'), '-o', file('dist/wasm-lv7.o')]);
run(process.env.WASM_LD || 'wasm-ld', ['--no-entry', '--export-memory',
  '--initial-memory=1048576', '--max-memory=1048576',
  file('dist/wasm-lv7.o'), '-o', file('dist/wasm-lv7.wasm')]);
// #endregion

// #region lv7-offline-page
const bytes = readFileSync(new URL('dist/wasm-lv7.wasm', src));
const stage = readFileSync(new URL('examples/cpp-wasm/lv7/stage.json', src), 'utf8');
const scripts = buildSync({ entryPoints: [file('examples/cpp-wasm/lv7/main.js')], bundle: true,
  format: 'iife', globalName: 'DanmakuWasm', target: 'es2022', write: false }).outputFiles[0].text;
const html = `<!doctype html><html lang="ko"><meta charset="utf-8">
<title>C++ wasm Lv7 · 완성 게임</title>
<style>body{background:#101827;color:white;font-family:sans-serif}canvas{max-width:100%;height:auto;outline:2px solid #64748b}canvas:focus{outline-color:#5eead4}</style>
<h1>C++ wasm Lv7 · 완성 게임</h1><p id="status" role="status">불러오는 중입니다.</p><p id="hud"></p><p id="phase"></p><p id="rewards"></p><p id="best"></p>
<canvas width="480" height="640" tabindex="0" aria-label="탄막 게임 화면"></canvas>
<script id="wasm-bytes" type="application/octet-stream">${bytes.toString('base64')}</script>
<script id="stage" type="application/json">${stage}</script>
<script>${scripts}\nDanmakuWasm.startGame(document, ${JSON.stringify(bytes.toString('base64'))}, ${stage});</script></html>`;
writeFileSync(new URL('dist/wasm-lv7.html', src), html);
// #endregion

// #region lv7-demo-build
buildSync({ entryPoints: [file('examples/cpp-wasm/demo.mjs')], bundle: true, format: 'iife',
  target: 'es2022', loader: { '.wasm': 'base64' }, outfile: file('dist/wasm-demo.js') });
buildSync({ entryPoints: [file('examples/cpp-wasm/lv7/audio.ts'), file('examples/cpp-wasm/lv7/storage.ts')],
  format: 'esm', outdir: file('dist/wasm-lv7-modules'), outExtension: { '.js': '.mjs' } });
// #endregion
