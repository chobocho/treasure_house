import { mount } from './lv7/main';
declare global {
  interface Window {
    __demo(id: string, init: (host: HTMLElement) => void): void;
    __initDemos(host: Element): void;
  }
}

// #region demo-mount
window.__demo('canvas-game', (host) => {
  const canvas = document.createElement('canvas');
  canvas.setAttribute('aria-label', 'Canvas 탄막 슈팅 게임');
  host.append(canvas);
  mount(canvas, () => host.closest('article')!.getBoundingClientRect().width > 0);
});
// 해시 첫 진입 시 늦게 등록된 데모를 다시 배선한다.
document.querySelectorAll<HTMLElement>('[data-demo="canvas-game"][data-wired]').forEach((host) => {
  delete host.dataset.wired;
  window.__initDemos(host);
});
// #endregion
