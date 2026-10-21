import { startGame } from './lv7/main.js';
import bytes from '../../dist/wasm-lv7.wasm';
import stage from './lv7/stage.json';
// #region wasm-demo-mount
window.__demo('wasm-game', (host) => {
  host.innerHTML = '<div style="flex:1 1 200px"><p id="status" role="status"></p><p id="hud"></p><p id="phase"></p><p id="rewards"></p><p id="best"></p></div><canvas width="480" height="640" tabindex="0" aria-label="C++ wasm 탄막 게임"></canvas>';
  host.style.display = 'flex'; host.style.flexWrap = 'wrap'; host.style.gap = '12px';
  const canvas = host.querySelector('canvas');
  canvas.style.maxHeight = '420px'; canvas.style.maxWidth = '100%'; canvas.style.width = 'auto';
  void startGame(host, bytes, stage, () => host.closest('article').getBoundingClientRect().width > 0)
    .then((dispose) => { if (dispose) addEventListener('pagehide', dispose, { once: true }); });
});
// #endregion
document.querySelectorAll('[data-demo="wasm-game"][data-wired]').forEach((host) => {
  delete host.dataset.wired;
  window.__initDemos(host);
});
