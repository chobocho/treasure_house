// #region surface
export function createSurface(canvas: HTMLCanvasElement): CanvasRenderingContext2D {
  canvas.width = 480;
  canvas.height = 640;
  canvas.style.maxWidth = '100%';
  canvas.style.height = 'auto';
  const context = canvas.getContext('2d');
  if (!context) throw new Error('Canvas 2D를 사용할 수 없습니다');
  return context;
}
// #endregion

// #region setup-draw
export function drawSetup(context: CanvasRenderingContext2D, frames: number): void {
  context.fillStyle = '#081523';
  context.fillRect(0, 0, 480, 640);
  context.font = '48px sans-serif';
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillText('\u{1f680}', 240, 560);
  context.font = '20px sans-serif';
  context.fillStyle = '#b8edff';
  context.fillText('Canvas 2D · TypeScript', 240, 80);
  context.canvas.dataset.frames = String(frames);
}
// #endregion
