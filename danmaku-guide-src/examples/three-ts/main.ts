import { setup } from './setup';

// #region setup-loop
const canvas = document.createElement('canvas');
document.body.append(canvas);
const view = setup(canvas);
let request = 0;
function draw(): void {
  view.draw();
  request = requestAnimationFrame(draw);
}
request = requestAnimationFrame(draw);
window.addEventListener('beforeunload', () => {
  cancelAnimationFrame(request);
  view.dispose();
});
// #endregion
