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
    c.font = '24px sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle';
    c.fillText('\u{1f680}', x, y);
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
      c.beginPath(); c.arc(x, y, p.radius[i], 0, 6.283185307179586); c.fill();
    }
  }
  // #endregion

  // #region draw-frame
  draw(game: Game, alpha: number): void {
    const c = this.context;
    c.fillStyle = '#081523'; c.fillRect(0, 0, 480, 640);
    this.drawBullets(game, alpha);
    this.drawPlayer(game, alpha);
    c.font = '14px sans-serif'; c.textAlign = 'left'; c.textBaseline = 'top';
    c.fillStyle = '#b8edff'; c.fillText('WASD / 방향키 · Z 발사 · Shift 집중', 10, 10);
    this.canvas.dataset.x = String(game.playerX);
    this.canvas.dataset.bullets = String(game.bullets.count);
  }
  // #endregion
}
