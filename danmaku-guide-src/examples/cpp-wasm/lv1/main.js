// #region lv1-browser-load
async function startGame() {
  const canvas = document.querySelector('canvas');
  const status = document.querySelector('#status');
  try {
    const bytes = Uint8Array.from(atob(document.querySelector('#wasm-bytes').textContent.trim()), (c) => c.charCodeAt(0));
    const { instance } = await WebAssembly.instantiate(bytes, {});
    const api = instance.exports;
    const game = attachGame(api, 49734321);
    const readPositions = attachPositions(api);
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas2D를 사용할 수 없습니다');
    // #endregion

    // #region lv1-browser-input
    const keys = new Set();
    const mapping = { ArrowLeft: 1, ArrowRight: 2, ArrowUp: 4, ArrowDown: 8,
      z: 16, Z: 16, ' ': 16, Shift: 32 };
    canvas.addEventListener('keydown', (event) => {
      if (mapping[event.key]) { keys.add(event.key); event.preventDefault(); }
    });
    canvas.addEventListener('keyup', (event) => {
      if (mapping[event.key]) { keys.delete(event.key); event.preventDefault(); }
    });
    canvas.addEventListener('blur', () => keys.clear());
    document.addEventListener('visibilitychange', () => { if (document.hidden) keys.clear(); });
    const input = () => [...keys].reduce((bits, key) => bits | mapping[key], 0);
    // #endregion

    // #region lv1-browser-draw
    let frames = 0;
    function draw() {
      ctx.fillStyle = '#101827'; ctx.fillRect(0, 0, 480, 640);
      ctx.fillStyle = '#5eead4';
      ctx.beginPath(); ctx.arc(api.dm_player_x(), api.dm_player_y(), 10, 0, Math.PI * 2); ctx.fill();
      api.dm_positions();
      ctx.fillStyle = '#fbbf24';
      for (const [x, y] of readPositions()) {
        ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.fill();
      }
      canvas.dataset.frames = String(++frames);
      canvas.dataset.x = String(api.dm_player_x());
      canvas.dataset.bullets = String(api.dm_count());
      canvas.dataset.step = String(api.dm_frame());
    }
    // #endregion

    // #region lv1-browser-loop
    const DT = 1 / 60;
    let previous = performance.now(), accumulated = 0, wasActive = false;
    function tick(now) {
      const active = !document.hidden && document.activeElement === canvas;
      const elapsed = active && wasActive ? Math.min(0.25, (now - previous) / 1000) : 0;
      previous = now; wasActive = active;
      if (!active) accumulated = 0;
      accumulated += elapsed;
      while (accumulated + 1e-12 >= DT) {
        game.step(input());
        accumulated -= DT;
      }
      draw();
      requestAnimationFrame(tick);
    }
    status.textContent = '화면을 클릭한 뒤 방향키 · Z 발사 · Shift 집중 이동';
    status.dataset.state = 'ready';
    requestAnimationFrame(tick);
    // #endregion
  } catch (error) {
    status.textContent = `실행 실패: ${error.message}`;
    status.dataset.state = 'error';
  }
}
startGame();
