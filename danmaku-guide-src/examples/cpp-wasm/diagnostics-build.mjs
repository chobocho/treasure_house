import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { mkdirSync } from 'node:fs';
const src = new URL('../../', import.meta.url);
const file = (p) => fileURLToPath(new URL(p, src));
mkdirSync(new URL('dist/', src), { recursive: true });
// #region wasm-traps-build
execFileSync(process.env.WASM_CXX || 'clang++', ['--target=wasm32', '-std=c++20',
  '-ffreestanding', '-nostdlib', '-fno-exceptions', '-fno-rtti', '-O2', '-Wall', '-Wextra', '-Werror',
  '-c', file('examples/cpp-wasm/traps.cpp'), '-o', file('dist/wasm-traps.o')]);
execFileSync(process.env.WASM_LD || 'wasm-ld', ['--no-entry', '--export-memory',
  '--initial-memory=131072', '--max-memory=131072', file('dist/wasm-traps.o'),
  '-o', file('dist/wasm-traps.wasm')]);
// #endregion
