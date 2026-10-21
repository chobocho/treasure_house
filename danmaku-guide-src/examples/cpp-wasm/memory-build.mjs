import { execFileSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const src = new URL('../../', import.meta.url);
const file = (p) => fileURLToPath(new URL(p, src));
const run = (cmd, args) => execFileSync(cmd, args, { cwd: src, stdio: 'inherit' });
mkdirSync(new URL('dist/', src), { recursive: true });
// #region memory-build
const common = ['-std=c++20', '-O2', '-Wall', '-Wextra', '-Werror', '-ffp-contract=off'];
run(process.env.NATIVE_CXX || 'g++', [...common,
  file('examples/cpp-wasm/memory.cpp'), file('examples/cpp-wasm/test_memory.cpp'),
  '-o', file('dist/wasm-memory-native')]);
run(file('dist/wasm-memory-native'), []);
run(process.env.WASM_CXX || 'clang++', [...common, '--target=wasm32',
  '-ffreestanding', '-nostdlib', '-fno-exceptions', '-fno-rtti',
  '-c', file('examples/cpp-wasm/memory.cpp'), '-o', file('dist/wasm-memory.o')]);
run(process.env.WASM_LD || 'wasm-ld', ['--no-entry', '--export-memory',
  '--initial-memory=131072', '--max-memory=131072',
  file('dist/wasm-memory.o'), '-o', file('dist/wasm-memory.wasm')]);
// #endregion
