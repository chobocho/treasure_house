import * as THREE from 'three';

declare global {
  interface Window { benchmark: typeof benchmark; }
}

// #region benchmark-scene
function benchmark(count: number, rounds: number) {
  if (!Number.isInteger(count) || count < 0 || count > 4096) throw new RangeError('탄환 수 범위');
  if (!Number.isInteger(rounds) || rounds < 1 || rounds > 20) throw new RangeError('표본 수 범위');
  const renderer = new THREE.WebGLRenderer({ antialias: false });
  renderer.setSize(480, 640);
  renderer.setPixelRatio(1);
  const gl = renderer.getContext();
  const geometry = new THREE.CircleGeometry(3, 12);
  const material = new THREE.MeshBasicMaterial({ color: 0xff7799 });
  const camera = new THREE.OrthographicCamera(0, 480, 640, 0, 0.1, 100);
  camera.position.z = 10;
  const debug = gl.getExtension('WEBGL_debug_renderer_info');
  const driver = String(gl.getParameter(debug ? debug.UNMASKED_RENDERER_WEBGL : gl.RENDERER));
  const results = [];
  // #endregion
  try {
    // #region benchmark-objects
    // O(n) 시간·공간. 두 경로의 기하·재질·좌표·해상도를 맞추고 생성 비용은 제외한다.
    for (const mode of ['mesh', 'instanced'] as const) {
      const scene = new THREE.Scene();
      const instances = mode === 'instanced' ? new THREE.InstancedMesh(geometry, material, Math.max(1, count)) : null;
      if (instances) { instances.count = count; instances.frustumCulled = false; scene.add(instances); }
      const matrix = new THREE.Matrix4();
      for (let i = 0; i < count; i++) {
        const x = 5 + (i % 64) * 7.4, y = 5 + Math.floor(i / 64) * 9.8;
        if (instances) instances.setMatrixAt(i, matrix.makeTranslation(x, y, 0));
        else {
          const mesh = new THREE.Mesh(geometry, material);
          mesh.position.set(x, y, 0); mesh.frustumCulled = false; scene.add(mesh);
        }
      }
      if (instances) instances.instanceMatrix.needsUpdate = true;
      // #endregion
      try {
        // #region benchmark-samples
        const samplesMs: number[] = [];
        let calls = 0;
        for (let round = -2; round < rounds; round++) {
          gl.finish();
          const start = performance.now();
          renderer.render(scene, camera);
          gl.finish();
          const elapsed = performance.now() - start;
          if (gl.isContextLost()) throw new Error('측정 중 WebGL 컨텍스트 손실');
          if (round >= 0) samplesMs.push(elapsed);
          calls = renderer.info.render.calls;
        }
        // 정렬 복사 O(r log r) 시간·O(r) 공간. 원시 표본 순서는 보존한다.
        const ordered = [...samplesMs].sort((a, b) => a - b), mid = Math.floor(rounds / 2);
        const medianMs = rounds % 2 ? ordered[mid] : (ordered[mid - 1] + ordered[mid]) / 2;
        results.push({ mode, calls, samplesMs, medianMs });
        // #endregion
      } finally { instances?.dispose(); scene.clear(); }
    }
    return { count, renderer: driver, userAgent: navigator.userAgent, results,
      method: '정적 장면·경로별 준비2회·render+gl.finish·생성/브라우저 시작/로직/전송 갱신 제외·게임 FPS 아님' };
  } finally {
    geometry.dispose(); material.dispose(); renderer.dispose(); renderer.forceContextLoss();
  }
}
window.benchmark = benchmark;
