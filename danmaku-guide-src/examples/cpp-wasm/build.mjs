import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const src = new URL('../../', import.meta.url);
const file = (path) => fileURLToPath(new URL(path, src));
const run = (command, args = []) => execFileSync(command, args, { encoding: 'utf8', cwd: src });
const clang = process.env.WASM_CXX || 'clang++';
const native = process.env.NATIVE_CXX || 'g++';
const linker = process.env.WASM_LD || 'wasm-ld';
mkdirSync(new URL('dist/', src), { recursive: true });

// #region setup-native-build
// 같은 소스를 사용해 JS를 거치지 않은 실행 결과도 확인한다.
run(native, ['-std=c++20', '-Wall', '-Wextra', '-Werror', '-O2', '-ffp-contract=off',
  file('examples/cpp-wasm/setup.cpp'), file('examples/cpp-wasm/test_setup.cpp'),
  '-o', file('dist/wasm-setup-native')]);
run(file('dist/wasm-setup-native'));
// #endregion

// #region setup-wasm-build
run(clang, ['--target=wasm32', '-std=c++20', '-ffreestanding', '-nostdlib',
  '-fno-exceptions', '-fno-rtti', '-ffp-contract=off', '-O2', '-Wall', '-Wextra', '-Werror',
  '-c', file('examples/cpp-wasm/setup.cpp'), '-o', file('dist/wasm-setup.o')]);
run(linker, ['--no-entry', '--export-memory', '--initial-memory=131072',
  '--max-memory=131072', file('dist/wasm-setup.o'), '-o', file('dist/wasm-setup.wasm')]);
// #endregion

// #region setup-instantiate
const bytes = readFileSync(new URL('dist/wasm-setup.wasm', src));
const { instance } = await WebAssembly.instantiate(bytes, {});
if (instance.exports.dm_abi_version() !== 1 || instance.exports.dm_advance(240, 4) !== 244) {
  throw new Error('wasm 설치 예제의 실행 결과가 예상과 다릅니다');
}
// #endregion

// #region setup-offline-page
const glue = readFileSync(new URL('examples/cpp-wasm/setup.js', src), 'utf8');
const page = `<!doctype html><html lang="ko"><meta charset="utf-8">
<title>C++ wasm 설치 확인</title><h1>C++ wasm 설치 확인</h1>
<p id="result" role="status">wasm을 불러오는 중입니다.</p>
<script id="wasm-bytes" type="application/octet-stream">${bytes.toString('base64')}</script>
<script>${glue}</script></html>`;
writeFileSync(new URL('dist/wasm-setup.html', src), page);
// #endregion

console.log(JSON.stringify({
  clang: run(clang, ['--version']).split('\n')[0],
  linker: run(linker, ['--version']).trim(), native: 'passed',
  bytes: bytes.length, abiVersion: instance.exports.dm_abi_version()
}, null, 2));
