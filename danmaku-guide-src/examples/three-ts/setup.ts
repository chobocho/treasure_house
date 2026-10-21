import * as THREE from 'three';

// #region scene-camera
export function setup(canvas: HTMLCanvasElement) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#081523');
  const camera = new THREE.OrthographicCamera(0, 480, 640, 0, .1, 100);
  camera.position.z = 10;
  // #endregion
  // #region renderer
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1);
  renderer.setSize(480, 640, false);
  canvas.style.maxWidth = '100%'; canvas.style.height = 'auto';
  // #endregion
  // #region mesh
  const geometry = new THREE.CircleGeometry(16, 24);
  const material = new THREE.MeshBasicMaterial({ color: '#6ef0ff' });
  const player = new THREE.Mesh(geometry, material);
  player.position.set(240, 640 - 560, 0);
  scene.add(player);
  // #endregion
  // #region draw
  let frames = 0;
  return {
    draw(): void {
      renderer.render(scene, camera);
      canvas.dataset.frames = String(++frames);
      canvas.dataset.calls = String(renderer.info.render.calls);
    },
    // #endregion
    // #region dispose
    dispose(): void {
      geometry.dispose(); material.dispose(); renderer.dispose();
    }
    // #endregion
  };
}
