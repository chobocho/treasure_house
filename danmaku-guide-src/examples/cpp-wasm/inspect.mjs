import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
// #region wasm-inspect
export async function inspectBytes(bytes) {
  const module = await WebAssembly.compile(bytes);
  const imports = WebAssembly.Module.imports(module);
  const exports = WebAssembly.Module.exports(module);
  // 외부 가져오기가 있으면 그 목록만 확인하고 임의의 함수를 연결하지 않는다.
  const instance = imports.length === 0 ? await WebAssembly.instantiate(module, {}) : null;
  const api = instance?.exports;
  return {
    bytes: bytes.byteLength,
    imports: imports.map(({ module, name, kind }) => ({ module, name, kind })),
    exports: exports.map(({ name, kind }) => ({ name, kind })),
    memoryBytes: api?.memory instanceof WebAssembly.Memory ? api.memory.buffer.byteLength : null,
    abiVersion: typeof api?.dm_abi_version === 'function' ? api.dm_abi_version() : null
  };
}
// #endregion
// #region wasm-inspect-cli
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.length !== 3 && !(process.argv.length === 4 && process.argv[3] === '--summary')) {
      throw new Error('사용법: node examples/cpp-wasm/inspect.mjs dist/wasm-lv7.wasm [--summary]');
    }
    const report = await inspectBytes(readFileSync(process.argv[2]));
    const result = process.argv[3] === '--summary' ? {
      bytes: report.bytes, imports: report.imports.length, exports: report.exports.length,
      memoryBytes: report.memoryBytes, abiVersion: report.abiVersion,
      stepExport: report.exports.some((entry) => entry.name === 'dm_step' && entry.kind === 'function')
    } : report;
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
  }
}
// #endregion
