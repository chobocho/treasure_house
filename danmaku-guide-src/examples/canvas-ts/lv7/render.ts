import { Game } from './game';

// #region renderer-init
export class Renderer {
  readonly context: CanvasRenderingContext2D;
  constructor(readonly canvas: HTMLCanvasElement) {
    canvas.width = 480; canvas.height = 640;
    canvas.style.maxWidth = '100%'; canvas.style.height = 'auto';
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Canvas 2D를 사용할 수 없습니다');
    this.context = context;
  }
// #endregion

  // #region draw-player
  drawPlayer(game: Game, alpha: number): void {
    const c = this.context;
    const x = game.previousX + (game.playerX - game.previousX) * alpha;
    const y = game.previousY + (game.playerY - game.previousY) * alpha;
    if (game.previousInput & 32) {
      c.strokeStyle = '#5096b4'; c.beginPath(); c.arc(x, y, 16, 0, 6.283185307179586); c.stroke();
    }
    c.font = '24px sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle';
    if (Math.floor(game.invulnerable / 6) % 2 === 0) c.fillText('\u{1f680}', x, y);
    c.fillStyle = '#6ef0ff';
    c.beginPath(); c.arc(x, y, 2, 0, 6.283185307179586); c.fill();
  }
  // #endregion

  // #region draw-bullets
  drawBullets(game: Game, alpha: number): void {
    const c = this.context, p = game.bullets;
    c.fillStyle = '#64dcff';
    for (let i = 0; i < p.count; i++) {
      const x = p.x[i] + p.vx[i] * (alpha - 1);
      const y = p.y[i] + p.vy[i] * (alpha - 1);
      c.fillStyle = p.kind[i] === 1 ? '#ff6464' : '#64dcff';
      c.beginPath(); c.arc(x, y, p.radius[i], 0, 6.283185307179586); c.fill();
    }
  }
  // #endregion

  // #region draw-enemies
  drawEnemies(game: Game, alpha: number): void {
    const c = this.context, p = game.enemies;
    c.fillStyle = '#ffffff';
    c.font = '32px sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle';
    for (let i = 0; i < p.count; i++) {
      c.font = p.kind[i] === 1 ? '64px sans-serif' : '32px sans-serif';
      c.fillText('\u{1f47e}', p.x[i] + p.vx[i] * (alpha - 1), p.y[i] + p.vy[i] * (alpha - 1));
    }
  }
  // #endregion

  // #region boss-bar
  drawBossBar(game: Game): void {
    const index = game.findBoss();
    if (index < 0) return;
    const c = this.context, ratio = Math.max(0, Math.min(1, game.enemies.hp[index] / 180));
    c.fillStyle = '#1e283c'; c.fillRect(12, 58, 456, 10);
    c.fillStyle = '#ff6478'; c.fillRect(12, 58, Math.round(456 * ratio), 10);
    c.font = '14px sans-serif'; c.textAlign = 'left'; c.textBaseline = 'top';
    c.fillText('보스 ' + game.phase + '단계', 12, 74);
  }
  // #endregion

  // #region draw-items
  drawItems(game: Game, alpha: number): void {
    const c = this.context, p = game.items;
    c.fillStyle = '#ffd250';
    for (let i = 0; i < p.count; i++) {
      c.beginPath();
      c.arc(p.x[i] + p.vx[i] * (alpha - 1), p.y[i] + p.vy[i] * (alpha - 1), 6, 0, 6.283185307179586);
      c.fill();
    }
  }
  // #endregion

  // #region draw-particles
  drawParticles(game: Game, alpha: number): void {
    const c = this.context, p = game.particles;
    c.fillStyle = '#ffbe5a';
    for (let i = 0; i < p.count; i++) {
      c.beginPath();
      c.arc(p.x[i] + p.vx[i] * (alpha - 1), p.y[i] + p.vy[i] * (alpha - 1), 2, 0, 6.283185307179586);
      c.fill();
    }
  }
  // #endregion

  // #region draw-overlay
  drawOverlay(game: Game): void {
    if (game.status === 1 && !game.paused) return;
    const c = this.context;
    c.fillStyle = '#14283c'; c.fillRect(60, 260, 360, 120);
    c.fillStyle = '#ffe6a0'; c.font = '20px sans-serif'; c.textAlign = 'left'; c.textBaseline = 'top';
    c.fillText(game.paused ? '일시 정지 · P' : ['탄막 슈팅', '', '게임 오버', '스테이지 완료'][game.status], 90, 285);
    c.fillText('Enter · BEST ' + game.highScore, 90, 325);
  }
  // #endregion

  // #region draw-frame
  draw(game: Game, alpha: number): void {
    if (game.paused || game.status !== 1) alpha = 1;
    const c = this.context;
    c.fillStyle = '#081523'; c.fillRect(0, 0, 480, 640);
    this.drawEnemies(game, alpha);
    this.drawBullets(game, alpha);
    this.drawItems(game, alpha);
    this.drawParticles(game, alpha);
    this.drawPlayer(game, alpha);
    c.font = '14px sans-serif'; c.textAlign = 'left'; c.textBaseline = 'top';
    c.fillStyle = '#b8edff'; c.fillText('WASD / 방향키 · Z 발사 · Shift 집중 · X 폭탄', 10, 10);
    c.fillText('S ' + game.score + '  L ' + game.lives + '  P ' + game.power + '  B ' + game.bombs, 10, 32);
    this.drawBossBar(game);
    this.drawOverlay(game);
    this.canvas.dataset.paused = String(game.paused);
    this.canvas.dataset.status = String(game.status);
    this.canvas.dataset.x = String(game.playerX);
    this.canvas.dataset.bullets = String(game.bullets.count);
  }
  // #endregion
}
