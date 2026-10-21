// #region setup-load
async function loadSetup(base64) {
  const bytes = Uint8Array.from(atob(base64), (ch) => ch.charCodeAt(0));
  const { instance } = await WebAssembly.instantiate(bytes, {});
  if (instance.exports.dm_abi_version() !== 1) {
    throw new Error('지원하지 않는 ABI 버전');
  }
  return instance.exports;
}
// #endregion

// #region setup-display
async function showSetup() {
  const output = document.querySelector('#result');
  try {
    const api = await loadSetup(document.querySelector('#wasm-bytes').textContent.trim());
    const position = api.dm_advance(240, 4);
    output.textContent = `ABI ${api.dm_abi_version()} · 240 + 4 = ${position}`;
    output.dataset.state = 'ready';
  } catch (error) {
    output.textContent = `wasm 로딩 실패: ${error.message}`;
    output.dataset.state = 'error';
  }
}
showSetup();
// #endregion
