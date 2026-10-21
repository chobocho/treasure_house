import { createSurface, drawSetup } from './setup';

// #region setup-loop
const canvas = document.createElement('canvas');
document.body.append(canvas);
const context = createSurface(canvas);
let frames = 0;
function draw(): void {
  drawSetup(context, ++frames);
  requestAnimationFrame(draw);
}
requestAnimationFrame(draw);
// #endregion
