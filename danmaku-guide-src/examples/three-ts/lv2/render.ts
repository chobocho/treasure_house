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
  readonly bulletGeometry = new THREE.CircleGeometry(1, 12);
  readonly bulletMaterial = new THREE.MeshBasicMaterial({ color: '#ffffff' });
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
  readonly hitGeometry = new THREE.CircleGeometry(2, 12);
  readonly hitMaterial = new THREE.MeshBasicMaterial({ color: '#6ef0ff' });
  readonly hit = new THREE.Mesh(this.hitGeometry, this.hitMaterial);
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
    this.hudCanvas.width = 480; this.hudCanvas.height = 64;
    this.hudTexture.colorSpace = THREE.SRGBColorSpace;
    this.hud.scale.set(480, 64, 1); this.hud.position.set(240, 608, 4);
    this.hud.renderOrder = 10; this.scene.add(this.hud);
  }
  // #endregion

  // #region draw-player
  drawPlayer(game: Game, alpha: number): void {
    const x = game.previousX + (game.playerX - game.previousX) * alpha;
    const y = game.previousY + (game.playerY - game.previousY) * alpha;
    this.player.position.set(x, 640 - y, 1);
    this.player.visible = Math.floor(game.invulnerable / 6) % 2 === 0;
    this.hit.position.set(x, 640 - y, 3);
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
    this.bulletInstances.instanceMatrix.needsUpdate = true;
    this.bulletInstances.instanceColor!.needsUpdate = true;
  }
  // #endregion

  // #region draw-enemies
  drawEnemies(game: Game, alpha: number): void {
    const p = game.enemies;
    for (let i = 0; i < this.enemySprites.length; i++) {
      const sprite = this.enemySprites[i];
      sprite.visible = i < p.count;
      if (sprite.visible) sprite.position.set(p.x[i] + p.vx[i] * (alpha - 1), 640 - (p.y[i] + p.vy[i] * (alpha - 1)), 0);
    }
  }
  // #endregion

  // #region draw-hud
  drawHud(game: Game): void {
    const key = game.score + ':' + game.lives;
    if (key === this.hudKey) return;
    this.hudKey = key;
    const c = this.hudCanvas.getContext('2d')!;
    c.clearRect(0, 0, 480, 64); c.fillStyle = '#b8edff'; c.font = '14px sans-serif';
    c.fillText('WASD / 방향키 · Z 발사 · Shift 집중', 10, 20);
    c.fillText('S ' + game.score + '  L ' + game.lives, 10, 44);
    this.hudTexture.needsUpdate = true;
  }
  // #endregion

  // #region draw-frame
  draw(game: Game, alpha: number): void {
    this.drawEnemies(game, alpha);
    this.drawPlayer(game, alpha);
    this.drawBullets(game, alpha);
    this.drawHud(game);
    this.renderer.render(this.scene, this.camera);
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
    this.renderer.dispose();
  }
  // #endregion
}
