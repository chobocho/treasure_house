import bulletVertex from './bullet.vert.glsl';
import bulletFragment from './bullet.frag.glsl';
import * as THREE from 'three';
import { Game } from './game';

// #region emoji-texture
function emojiTexture(text: string): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 128; canvas.height = 128;
  const context = canvas.getContext('2d')!;
  context.font = '96px sans-serif'; context.textAlign = 'center'; context.textBaseline = 'middle';
  context.fillText(text, 64, 64);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}
// #endregion

export class Renderer {
  // #region renderer-fields
  readonly scene = new THREE.Scene();
  readonly camera = new THREE.OrthographicCamera(0, 480, 640, 0, .1, 100);
  readonly renderer: THREE.WebGLRenderer;
  readonly playerTexture = emojiTexture('\u{1f680}');
  readonly playerMaterial = new THREE.SpriteMaterial({ map: this.playerTexture, depthWrite: false });
  readonly player = new THREE.Sprite(this.playerMaterial);
  readonly bulletGeometry = new THREE.PlaneGeometry(2, 2);
  readonly circleGeometry = new THREE.CircleGeometry(1, 12);
  readonly bulletMaterial = new THREE.ShaderMaterial({ vertexShader: bulletVertex, fragmentShader: bulletFragment,
    uniforms: { uTime: { value: 0 } } });
  readonly bulletInstances = new THREE.InstancedMesh(this.bulletGeometry, this.bulletMaterial, 4096);
  readonly matrix = new THREE.Matrix4();
  readonly color = new THREE.Color();
  readonly enemyTexture = emojiTexture('\u{1f47e}');
  readonly enemyMaterial = new THREE.SpriteMaterial({ map: this.enemyTexture, depthWrite: false });
  readonly enemySprites: THREE.Sprite[] = [];
  readonly hudCanvas = document.createElement('canvas');
  readonly hudTexture = new THREE.CanvasTexture(this.hudCanvas);
  readonly hudMaterial = new THREE.SpriteMaterial({ map: this.hudTexture, depthTest: false, depthWrite: false });
  readonly hud = new THREE.Sprite(this.hudMaterial);
  hudKey = '';
  readonly matrixRange = { start: 0, count: 0 };
  readonly colorRange = { start: 0, count: 0 };
  readonly hitGeometry = new THREE.CircleGeometry(2, 12);
  readonly hitMaterial = new THREE.MeshBasicMaterial({ color: '#6ef0ff' });
  readonly hit = new THREE.Mesh(this.hitGeometry, this.hitMaterial);
  // #endregion
  // #region rewards-render-fields
  readonly itemMaterial = new THREE.MeshBasicMaterial({ color: '#ffd250' });
  readonly itemInstances = new THREE.InstancedMesh(this.circleGeometry, this.itemMaterial, 64);
  readonly itemRange = { start: 0, count: 0 };
  readonly focusGeometry = new THREE.RingGeometry(15, 16, 48);
  readonly focusMaterial = new THREE.MeshBasicMaterial({ color: '#5096b4' });
  readonly focus = new THREE.Mesh(this.focusGeometry, this.focusMaterial);
  // #endregion

  // #region polish-render-fields
  readonly particleMaterial = new THREE.MeshBasicMaterial({ color: '#ffbe5a' });
  readonly particleInstances = new THREE.InstancedMesh(this.circleGeometry, this.particleMaterial, 2048);
  readonly particleRange = { start: 0, count: 0 };
  readonly overlayCanvas = document.createElement('canvas');
  readonly overlayTexture = new THREE.CanvasTexture(this.overlayCanvas);
  readonly overlayMaterial = new THREE.SpriteMaterial({ map: this.overlayTexture, depthTest: false, depthWrite: false });
  readonly overlay = new THREE.Sprite(this.overlayMaterial);
  overlayKey = '';
  // #endregion

  // #region renderer-init
  constructor(readonly canvas: HTMLCanvasElement) {
    this.camera.position.z = 10;
    this.scene.background = new THREE.Color('#081523');
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(1); this.renderer.setSize(480, 640, false);
    canvas.style.maxWidth = '100%'; canvas.style.height = 'auto';
    this.player.scale.set(24, 24, 1);
    this.scene.add(this.player, this.hit);
    this.createBullets();
    this.createEnemies();
    this.createHud();
    this.itemInstances.count = 0; this.itemInstances.frustumCulled = false;
    this.itemInstances.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.scene.add(this.itemInstances, this.focus);
    this.createPolish();
  }
  // #endregion

  // #region bullet-create
  createBullets(): void {
    this.bulletInstances.count = 0;
    this.bulletInstances.frustumCulled = false;
    this.bulletInstances.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.bulletInstances.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(4096 * 3), 3);
    this.bulletInstances.instanceColor.setUsage(THREE.DynamicDrawUsage);
    this.scene.add(this.bulletInstances);
  }
  // #endregion

  // #region enemy-create
  createEnemies(): void {
    for (let i = 0; i < 128; i++) {
      const sprite = new THREE.Sprite(this.enemyMaterial);
      sprite.visible = false; sprite.scale.set(32, 32, 1);
      this.enemySprites.push(sprite); this.scene.add(sprite);
    }
  }
  // #endregion

  // #region hud-init
  createHud(): void {
    this.hudCanvas.width = 480; this.hudCanvas.height = 128;
    this.hudTexture.colorSpace = THREE.SRGBColorSpace;
    this.hud.scale.set(480, 128, 1); this.hud.position.set(240, 576, 4);
    this.hud.renderOrder = 10; this.scene.add(this.hud);
  }
  // #endregion

  // #region polish-create
  createPolish(): void {
    this.particleInstances.count = 0; this.particleInstances.frustumCulled = false;
    this.particleInstances.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.overlayCanvas.width = 480; this.overlayCanvas.height = 128;
    this.overlayTexture.colorSpace = THREE.SRGBColorSpace;
    this.overlay.scale.set(480, 128, 1); this.overlay.position.set(240, 320, 5);
    this.overlay.renderOrder = 20;
    this.scene.add(this.particleInstances, this.overlay);
  }
  // #endregion

  // #region draw-player
  drawPlayer(game: Game, alpha: number): void {
    const x = game.previousX + (game.playerX - game.previousX) * alpha;
    const y = game.previousY + (game.playerY - game.previousY) * alpha;
    this.player.position.set(x, 640 - y, 1);
    this.player.visible = Math.floor(game.invulnerable / 6) % 2 === 0;
    this.hit.position.set(x, 640 - y, 3);
    this.focus.position.set(x, 640 - y, 2.5);
    this.focus.visible = Boolean(game.previousInput & 32);
  }
  // #endregion

  // #region draw-bullets
  // 행렬과 색 객체를 재사용한다. 시간 O(활성 탄환), 추가 공간 O(1).
  drawBullets(game: Game, alpha: number): void {
    const p = game.bullets;
    this.bulletInstances.count = p.count;
    for (let i = 0; i < p.count; i++) {
      this.matrix.makeScale(p.radius[i], p.radius[i], 1);
      this.matrix.setPosition(p.x[i] + p.vx[i] * (alpha - 1), 640 - (p.y[i] + p.vy[i] * (alpha - 1)), 2);
      this.bulletInstances.setMatrixAt(i, this.matrix);
      this.color.setHex(p.kind[i] === 1 ? 0xff6464 : 0x64dcff);
      this.bulletInstances.setColorAt(i, this.color);
    }
    // #region instance-upload
    const matrices = this.bulletInstances.instanceMatrix, colors = this.bulletInstances.instanceColor!;
    matrices.clearUpdateRanges(); colors.clearUpdateRanges();
    if (p.count > 0) {
      this.matrixRange.count = p.count * 16; this.colorRange.count = p.count * 3;
      matrices.updateRanges.push(this.matrixRange); colors.updateRanges.push(this.colorRange);
      matrices.needsUpdate = true; colors.needsUpdate = true;
    }
    // #endregion
  }
  // #endregion

  // #region draw-enemies
  drawEnemies(game: Game, alpha: number): void {
    const p = game.enemies;
    for (let i = 0; i < this.enemySprites.length; i++) {
      const sprite = this.enemySprites[i];
      sprite.visible = i < p.count;
      if (sprite.visible) {
        const size = p.kind[i] === 1 ? 64 : 32;
        sprite.scale.set(size, size, 1);
        sprite.position.set(p.x[i] + p.vx[i] * (alpha - 1), 640 - (p.y[i] + p.vy[i] * (alpha - 1)), 0);
      }
    }
  }
  // #endregion

  // #region draw-hud
  drawHud(game: Game): void {
    const boss = game.findBoss(), hp = boss >= 0 ? game.enemies.hp[boss] : 0;
    const key = game.score + ':' + game.lives + ':' + game.phase + ':' + hp + ':' + game.power + ':' + game.bombs;
    if (key === this.hudKey) return;
    this.hudKey = key;
    const c = this.hudCanvas.getContext('2d')!;
    c.clearRect(0, 0, 480, 128); c.fillStyle = '#b8edff'; c.font = '14px sans-serif';
    c.fillText('WASD / 방향키 · Z 발사 · Shift 집중 · X 폭탄', 10, 20);
    c.fillText('S ' + game.score + '  L ' + game.lives + '  P ' + game.power + '  B ' + game.bombs, 10, 44);
    this.drawBossBar(game, c);
    this.hudTexture.needsUpdate = true;
  }
  // #endregion

  // #region boss-bar
  drawBossBar(game: Game, c: CanvasRenderingContext2D): void {
    const boss = game.findBoss();
    if (boss < 0) return;
    const ratio = Math.max(0, Math.min(1, game.enemies.hp[boss] / 180));
    c.fillStyle = '#1e283c'; c.fillRect(12, 58, 456, 10);
    c.fillStyle = '#ff6478'; c.fillRect(12, 58, Math.round(456 * ratio), 10);
    c.fillText('보스 ' + game.phase + '단계', 12, 90);
  }
  // #endregion

  // #region draw-items
  // 표시용 행렬만 갱신하고 게임의 수집 판정은 건드리지 않는다. 시간 O(i), 추가 공간 O(1).
  drawItems(game: Game, alpha: number): void {
    const p = game.items, matrices = this.itemInstances.instanceMatrix;
    this.itemInstances.count = p.count;
    for (let i = 0; i < p.count; i++) {
      this.matrix.makeScale(6, 6, 1);
      this.matrix.setPosition(p.x[i] + p.vx[i] * (alpha - 1), 640 - (p.y[i] + p.vy[i] * (alpha - 1)), 2.2);
      this.itemInstances.setMatrixAt(i, this.matrix);
    }
    matrices.clearUpdateRanges();
    if (p.count > 0) {
      this.itemRange.count = p.count * 16;
      matrices.updateRanges.push(this.itemRange); matrices.needsUpdate = true;
    }
  }
  // #endregion

  // #region draw-particles
  // 효과도 고정 인스턴스 배열을 사용한다. 시간 O(p), 추가 공간 O(1).
  drawParticles(game: Game, alpha: number): void {
    const p = game.particles, matrices = this.particleInstances.instanceMatrix;
    this.particleInstances.count = p.count;
    for (let i = 0; i < p.count; i++) {
      this.matrix.makeScale(p.radius[i], p.radius[i], 1);
      this.matrix.setPosition(p.x[i] + p.vx[i] * (alpha - 1), 640 - (p.y[i] + p.vy[i] * (alpha - 1)), 2.8);
      this.particleInstances.setMatrixAt(i, this.matrix);
    }
    matrices.clearUpdateRanges();
    if (p.count > 0) {
      this.particleRange.count = p.count * 16;
      matrices.updateRanges.push(this.particleRange); matrices.needsUpdate = true;
    }
  }
  // #endregion

  // #region draw-overlay
  drawOverlay(game: Game): void {
    this.overlay.visible = game.status !== 1 || game.paused;
    const key = game.status + ':' + game.paused + ':' + game.highScore;
    if (!this.overlay.visible || key === this.overlayKey) return;
    this.overlayKey = key;
    const c = this.overlayCanvas.getContext('2d')!;
    c.clearRect(0, 0, 480, 128);
    c.fillStyle = '#14283c'; c.fillRect(60, 4, 360, 120);
    c.fillStyle = '#ffe6a0'; c.font = '20px sans-serif'; c.textBaseline = 'top';
    c.fillText(game.paused ? '일시 정지 · P' : ['탄막 슈팅', '', '게임 오버', '스테이지 완료'][game.status], 90, 29);
    c.fillText('Enter · BEST ' + game.highScore, 90, 69);
    this.overlayTexture.needsUpdate = true;
  }
  // #endregion

  // #region draw-frame
  draw(game: Game, alpha: number): void {
    if (game.paused || game.status !== 1) alpha = 1;
    this.bulletMaterial.uniforms.uTime.value = game.time / 60;
    this.drawEnemies(game, alpha);
    this.drawPlayer(game, alpha);
    this.drawBullets(game, alpha);
    this.drawItems(game, alpha);
    this.drawParticles(game, alpha);
    this.drawHud(game);
    this.drawOverlay(game);
    this.renderer.render(this.scene, this.camera);
    this.canvas.dataset.paused = String(game.paused);
    this.canvas.dataset.status = String(game.status);
    this.canvas.dataset.x = String(game.playerX);
    this.canvas.dataset.bullets = String(game.bullets.count);
    this.canvas.dataset.calls = String(this.renderer.info.render.calls);
  }
  // #endregion

  // #region dispose
  dispose(): void {
    this.playerTexture.dispose(); this.playerMaterial.dispose();
    this.bulletGeometry.dispose(); this.bulletMaterial.dispose();
    this.hitGeometry.dispose(); this.hitMaterial.dispose();
    this.enemyTexture.dispose(); this.enemyMaterial.dispose();
    this.hudTexture.dispose(); this.hudMaterial.dispose();
    this.bulletInstances.dispose();
    this.itemMaterial.dispose(); this.itemInstances.dispose();
    this.focusGeometry.dispose(); this.focusMaterial.dispose();
    this.circleGeometry.dispose(); this.particleMaterial.dispose(); this.particleInstances.dispose();
    this.overlayTexture.dispose(); this.overlayMaterial.dispose();
    this.renderer.dispose();
  }
  // #endregion
}
