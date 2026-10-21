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
  // #region renderer-init
  readonly scene = new THREE.Scene();
  readonly camera = new THREE.OrthographicCamera(0, 480, 640, 0, .1, 100);
  readonly renderer: THREE.WebGLRenderer;
  readonly playerTexture = emojiTexture('\u{1f680}');
  readonly playerMaterial = new THREE.SpriteMaterial({ map: this.playerTexture, depthWrite: false });
  readonly player = new THREE.Sprite(this.playerMaterial);
  readonly bulletGeometry = new THREE.CircleGeometry(1, 12);
  readonly bulletMaterial = new THREE.MeshBasicMaterial({ color: '#64dcff' });
  readonly bulletMeshes: THREE.Mesh[] = [];
  readonly hitGeometry = new THREE.CircleGeometry(2, 12);
  readonly hitMaterial = new THREE.MeshBasicMaterial({ color: '#6ef0ff' });
  readonly hit = new THREE.Mesh(this.hitGeometry, this.hitMaterial);
  constructor(readonly canvas: HTMLCanvasElement) {
    this.camera.position.z = 10;
    this.scene.background = new THREE.Color('#081523');
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(1); this.renderer.setSize(480, 640, false);
    canvas.style.maxWidth = '100%'; canvas.style.height = 'auto';
    this.player.scale.set(24, 24, 1);
    this.scene.add(this.player, this.hit);
    this.createBullets();
  }
  // #endregion

  // #region bullet-create
  // 초기화에서 객체를 만들고 화면 루프에서는 재사용한다. 시간·저장 공간 O(용량).
  createBullets(): void {
    for (let i = 0; i < 4096; i++) {
      const mesh = new THREE.Mesh(this.bulletGeometry, this.bulletMaterial);
      mesh.visible = false;
      this.bulletMeshes.push(mesh);
      this.scene.add(mesh);
    }
  }
  // #endregion

  // #region draw-player
  drawPlayer(game: Game, alpha: number): void {
    const x = game.previousX + (game.playerX - game.previousX) * alpha;
    const y = game.previousY + (game.playerY - game.previousY) * alpha;
    this.player.position.set(x, 640 - y, 1);
    this.hit.position.set(x, 640 - y, 3);
  }
  // #endregion

  // #region draw-bullets
  drawBullets(game: Game, alpha: number): void {
    const p = game.bullets;
    for (let i = 0; i < this.bulletMeshes.length; i++) {
      const mesh = this.bulletMeshes[i];
      mesh.visible = i < p.count;
      if (!mesh.visible) continue;
      mesh.position.set(p.x[i] + p.vx[i] * (alpha - 1), 640 - (p.y[i] + p.vy[i] * (alpha - 1)), 2);
      mesh.scale.set(p.radius[i], p.radius[i], 1);
    }
  }
  // #endregion

  // #region draw-frame
  draw(game: Game, alpha: number): void {
    this.drawPlayer(game, alpha);
    this.drawBullets(game, alpha);
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
    this.renderer.dispose();
  }
  // #endregion
}
