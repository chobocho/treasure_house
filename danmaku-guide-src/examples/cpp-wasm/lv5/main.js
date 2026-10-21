// #region lv5-browser-load
async function startGame() {
  const canvas = document.querySelector('canvas');
  const status = document.querySelector('#status');
  try {
    const bytes = Uint8Array.from(atob(document.querySelector('#wasm-bytes').textContent.trim()), (c) => c.charCodeAt(0));
    const { instance } = await WebAssembly.instantiate(bytes, {});
    const api = instance.exports;
    const game = attachGame(api, 49734321);
    const readPositions = attachPositions(api);
    const readEnemies = attachPositions({ ...api, dm_capacity: () => 128,
      dm_count: api.dm_enemies, dm_positions: api.dm_enemy_positions });
    const kinds = new DataView(api.memory.buffer, api.dm_kinds() >>> 0, 4096 * 4);
    const readItems = attachPositions({ ...api, dm_capacity: () => 64,
      dm_count: api.dm_items, dm_positions: api.dm_item_positions });
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas2D를 사용할 수 없습니다');
    // #endregion

    // #region lv5-browser-input
    const keys = new Set();
    const mapping = { ArrowLeft: 1, ArrowRight: 2, ArrowUp: 4, ArrowDown: 8,
      z: 16, Z: 16, ' ': 16, Shift: 32, x: 64, X: 64 };
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

    // #region lv5-browser-boss
    function drawBoss() {
      const hp = api.dm_boss_hp();
      if (hp > 0) {
        ctx.fillStyle = '#fb923c';
        ctx.beginPath(); ctx.arc(api.dm_boss_x(), 100, 28, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#334155'; ctx.fillRect(20, 20, 200, 8);
        ctx.fillStyle = '#fb923c'; ctx.fillRect(20, 20, 200 * Math.max(0, Math.min(1, hp / 180)), 8);
      }
      canvas.dataset.bossHp = String(hp);
      canvas.dataset.bossX = String(api.dm_boss_x());
      document.querySelector('#phase').textContent = `보스 단계 ${api.dm_phase()}`;
      drawRewards();
    }
    // #endregion
    // #region lv5-browser-rewards
    function drawRewards() {
      api.dm_item_positions();
      ctx.fillStyle = '#4ade80';
      for (const [x, y] of readItems()) ctx.fillRect(x - 6, y - 6, 12, 12);
      if (input() & 32) {
        ctx.strokeStyle = '#5eead4';
        ctx.beginPath(); ctx.arc(api.dm_player_x(), api.dm_player_y(), 16, 0, Math.PI * 2); ctx.stroke();
      }
      document.querySelector('#rewards').textContent = `파워 ${api.dm_power()} · 폭탄 ${api.dm_bombs()} · 그레이즈 ${api.dm_graze()}`;
      canvas.dataset.bombs = String(api.dm_bombs());
      canvas.dataset.power = String(api.dm_power());
      canvas.dataset.items = String(api.dm_items());
    }
    // #endregion

    // #region lv5-browser-draw
    let frames = 0;
    function draw() {
      ctx.fillStyle = '#101827'; ctx.fillRect(0, 0, 480, 640);
      ctx.fillStyle = '#5eead4';
      if (Math.floor(api.dm_invulnerable() / 6) % 2 === 0) {
        ctx.beginPath(); ctx.arc(api.dm_player_x(), api.dm_player_y(), 10, 0, Math.PI * 2); ctx.fill();
      }
      api.dm_positions();
      api.dm_kinds();
      let index = 0, enemyBullets = 0;
      for (const [x, y] of readPositions()) {
        const hostile = kinds.getUint32(index++ * 4, true) === 1;
        if (hostile) ++enemyBullets;
        ctx.fillStyle = hostile ? '#a78bfa' : '#fbbf24';
        ctx.beginPath(); ctx.arc(x, y, hostile ? 4 : 3, 0, Math.PI * 2); ctx.fill();
      }
      api.dm_enemy_positions();
      ctx.fillStyle = '#fb7185';
      for (const [x, y] of readEnemies()) {
        ctx.beginPath(); ctx.arc(x, y, 12, 0, Math.PI * 2); ctx.fill();
      }
      drawBoss();
      document.querySelector('#hud').textContent = `점수 ${api.dm_score()} · 목숨 ${api.dm_lives()}`;
      canvas.dataset.enemies = String(api.dm_enemies());
      canvas.dataset.enemyBullets = String(enemyBullets);
      canvas.dataset.frames = String(++frames);
      canvas.dataset.x = String(api.dm_player_x());
      canvas.dataset.bullets = String(api.dm_count());
      canvas.dataset.step = String(api.dm_frame());
    }
    // #endregion

    // #region lv5-browser-loop
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
    status.textContent = '화면을 클릭한 뒤 방향키 · Z 발사 · X 폭탄 · Shift 집중 이동';
    status.dataset.state = 'ready';
    requestAnimationFrame(tick);
    // #endregion
  } catch (error) {
    status.textContent = `실행 실패: ${error.message}`;
    status.dataset.state = 'error';
  }
}
startGame();
