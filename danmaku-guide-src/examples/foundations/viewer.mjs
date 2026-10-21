import { Pool, FixedStep, PATTERN_PERIODS, emitPattern, stepPool } from './core.mjs';

window.__demo('pattern-viewer', (host, api) => {
  const canvas = host.querySelector('canvas');
  const context = canvas.getContext('2d');
  const pool = new Pool(4096);
  const clock = new FixedStep();
  let tick = 0, last = null;
  const mode = host.querySelector('[data-pattern]');
  const count = host.querySelector('[data-count]');
  const speed = host.querySelector('[data-speed]');
  // #region viewer-spawn
  function spawn() {
    const n = Math.max(1, Math.min(64, Number(count.value) || 1));
    const v = Math.max(.5, Math.min(6, Number(speed.value) || 2));
    emitPattern(pool, mode.value, n, v, 240, 100, tick, 240, 360);
  }
  function reset() { pool.count = 0; tick = 0; spawn(); }
  host.querySelector('[data-reset]').addEventListener('click', reset);
  mode.addEventListener('change', reset);
  count.addEventListener('input', reset);
  speed.addEventListener('input', reset);
  reset();
  // #endregion
  // #region viewer-step
  function step() {
    stepPool(pool, canvas.width, canvas.height);
    tick++;
    if (tick % PATTERN_PERIODS[mode.value] === 0) spawn();
  }
  // #endregion
  // #region viewer-draw
  function draw() {
    context.fillStyle = '#081523';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = '#ff6e7c';
    for (let i = 0; i < pool.count; i++) {
      context.beginPath();
      context.arc(pool.x[i], pool.y[i], 3, 0, 6.283185307179586);
      context.fill();
    }
    context.fillStyle = '#6de3ff';
    context.fillRect(236, 356, 8, 8);
    canvas.dataset.frames = String(Number(canvas.dataset.frames || 0) + 1);
    canvas.dataset.bullets = String(pool.count);
    api.w(host, `${pool.count}개 탄환 · ${tick}스텝`);
  }
  // #endregion
  // #region viewer-loop
  function frame(now) {
    const visible = host.closest('article').getBoundingClientRect().width > 0 && !document.hidden;
    if (last !== null && visible) clock.advance((now - last) / 1000, step);
    last = now;
    if (visible) draw();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  // #endregion
});

// 해시로 처음 연 슬라이드는 템플릿 초기화 시점에 아직 등록되지 않았으므로 다시 배선한다.
document.querySelectorAll('[data-demo="pattern-viewer"][data-wired]').forEach((host) => {
  delete host.dataset.wired;
  window.__initDemos(host);
});
