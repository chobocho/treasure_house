import { attachGame } from './replay.mjs';
import { attachPositions } from '../memory-glue.mjs';
import { Audio } from './audio.ts';
import { loadBest, saveBest, safeStorage } from './storage.ts';
// #region lv7-browser-load
export async function startGame(root, base64, stage, isActive = () => true) {
  const canvas = root.querySelector('canvas');
  const status = root.querySelector('#status');
  try {
    const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
    const { instance } = await WebAssembly.instantiate(bytes, {});
    const api = instance.exports;
    const game = attachGame(api, 49734321, stage);
    api.dm_menu();
    const storage = safeStorage();
    let savedBest = loadBest(storage);
    api.dm_set_high_score(savedBest);
    const readPositions = attachPositions(api);
    const readEnemies = attachPositions({ ...api, dm_capacity: () => 128,
      dm_count: api.dm_enemies, dm_positions: api.dm_enemy_positions });
    const kinds = new DataView(api.memory.buffer, api.dm_kinds() >>> 0, 4096 * 4);
    const readItems = attachPositions({ ...api, dm_capacity: () => 64,
      dm_count: api.dm_items, dm_positions: api.dm_item_positions });
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas2D를 사용할 수 없습니다');
    const audio = new Audio();
    const readParticles = attachPositions({ ...api, dm_capacity: () => 2048,
      dm_count: api.dm_particles, dm_positions: api.dm_particle_positions });
    const eventStride = api.dm_event_stride();
    if (eventStride < 20) throw new Error('이벤트 ABI 간격 오류');
    const eventData = new DataView(api.memory.buffer, api.dm_events() >>> 0, eventStride * 64);
    const eventKind = new Int32Array(64);
    // #endregion

    // #region lv7-browser-input
    const keys = new Set();
    let pressed = 0;
    const mapping = { ArrowLeft: 1, ArrowRight: 2, ArrowUp: 4, ArrowDown: 8,
      z: 16, Z: 16, ' ': 16, Shift: 32, x: 64, X: 64, Enter: 128, p: 256, P: 256 };
    canvas.addEventListener('keydown', (event) => {
      if (mapping[event.key]) {
        if (!event.repeat) pressed |= mapping[event.key];
        keys.add(event.key); event.preventDefault(); event.stopPropagation();
        void audio.unlock();
      }
    });
    canvas.addEventListener('keyup', (event) => {
      if (mapping[event.key]) { keys.delete(event.key); event.preventDefault(); event.stopPropagation(); }
    });
    const clearInput = () => { keys.clear(); pressed = 0; };
    canvas.addEventListener('blur', clearInput);
    const visibility = () => { if (document.hidden) clearInput(); };
    document.addEventListener('visibilitychange', visibility);
    canvas.addEventListener('pointerdown', () => { void audio.unlock(); });
    const input = () => [...keys].reduce((bits, key) => bits | mapping[key], pressed);
    // #endregion

    // #region lv7-browser-boss
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
      root.querySelector('#phase').textContent = `보스 단계 ${api.dm_phase()}`;
      drawRewards();
    }
    // #endregion
    // #region lv7-browser-rewards
    function drawRewards() {
      api.dm_item_positions();
      ctx.fillStyle = '#4ade80';
      for (const [x, y] of readItems()) ctx.fillRect(x - 6, y - 6, 12, 12);
      if (input() & 32) {
        ctx.strokeStyle = '#5eead4';
        ctx.beginPath(); ctx.arc(api.dm_player_x(), api.dm_player_y(), 16, 0, Math.PI * 2); ctx.stroke();
      }
      root.querySelector('#rewards').textContent = `파워 ${api.dm_power()} · 폭탄 ${api.dm_bombs()} · 그레이즈 ${api.dm_graze()}`;
      canvas.dataset.bombs = String(api.dm_bombs());
      canvas.dataset.power = String(api.dm_power());
      canvas.dataset.items = String(api.dm_items());
      drawPolish();
    }
    // #endregion

    // #region lv7-browser-polish
    function drawPolish() {
      api.dm_particle_positions(); ctx.fillStyle = '#e2e8f0';
      for (const [x, y] of readParticles()) ctx.fillRect(x - 2, y - 2, 4, 4);
      const state = api.dm_status(), paused = api.dm_paused() === 1;
      if (state !== 1 || paused) {
        ctx.fillStyle = '#0f172a'; ctx.fillRect(70, 240, 340, 140);
        ctx.fillStyle = '#ffffff'; ctx.font = '22px sans-serif'; ctx.textAlign = 'center';
        ctx.fillText(paused ? '일시 정지 · P 재개' : ['Enter로 시작', '', '게임 오버 · Enter 재시작', '클리어 · Enter 재시작'][state], 240, 300);
      }
      root.querySelector('#best').textContent = `최고 점수 ${api.dm_high_score()}`;
      canvas.dataset.gameStatus = String(state);
      canvas.dataset.paused = String(paused);
      canvas.dataset.time = String(api.dm_time());
      canvas.dataset.particles = String(api.dm_particles());
      canvas.dataset.audio = String(audio.enabled);
      canvas.dataset.audioState = audio.context?.state ?? 'none';
    }
    // #endregion
    // #region lv7-browser-consume
    function consume() {
      const count = api.dm_event_count();
      for (let i = 0; i < count; ++i) eventKind[i] = eventData.getUint32(i * eventStride + 16, true);
      audio.consume({ eventCount: count, eventKind, status: api.dm_status(), paused: api.dm_paused() === 1 });
      const best = api.dm_high_score();
      if (best > savedBest && saveBest(storage, best)) savedBest = best;
    }
    // #endregion

    // #region lv7-browser-draw
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
      root.querySelector('#hud').textContent = `점수 ${api.dm_score()} · 목숨 ${api.dm_lives()}`;
      canvas.dataset.enemies = String(api.dm_enemies());
      canvas.dataset.enemyBullets = String(enemyBullets);
      canvas.dataset.frames = String(++frames);
      canvas.dataset.x = String(api.dm_player_x());
      canvas.dataset.bullets = String(api.dm_count());
      canvas.dataset.step = String(api.dm_frame());
    }
    // #endregion

    // #region lv7-browser-loop
    const DT = 1 / 60;
    let previous = performance.now(), accumulated = 0, wasActive = false, request = 0;
    function tick(now) {
      const active = !document.hidden && document.activeElement === canvas && isActive();
      if (!active) clearInput();
      audio.setActive(active && api.dm_paused() === 0);
      const elapsed = active && wasActive ? Math.min(0.25, (now - previous) / 1000) : 0;
      previous = now; wasActive = active;
      if (!active) accumulated = 0;
      accumulated += elapsed;
      while (accumulated + 1e-12 >= DT) {
        game.step(input());
        pressed = 0; consume();
        accumulated -= DT;
      }
      draw();
      request = requestAnimationFrame(tick);
    }
    status.textContent = '화면 클릭 · Enter 시작 · 방향키 이동 · Z 발사 · X 폭탄 · Shift 집중 · P 정지';
    status.dataset.state = 'ready';
    request = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(request); audio.close(); document.removeEventListener('visibilitychange', visibility); };
    // #endregion
  } catch (error) {
    status.textContent = `실행 실패: ${error.message}`;
    status.dataset.state = 'error';
  }
}
