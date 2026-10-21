import stage from './stage.json';
import { Game } from './game';
import { Renderer } from './render';
import { bindInput } from './input';

// #region game-mount
export function mount(canvas: HTMLCanvasElement): () => void {
  // #region stage-load
  const game = new Game(undefined, stage);
  // #endregion
  const renderer = new Renderer(canvas), input = bindInput(canvas);
  let previous = performance.now(), accumulator = 0, frames = 0, request = 0;
  // #region fixed-loop
  const draw = (now: number) => {
    accumulator += Math.min(.25, (now - previous) / 1000);
    previous = now;
    const bits = input.read();
    while (accumulator + 1e-12 >= 1 / 60) {
      game.step(bits);
      accumulator = Math.max(0, accumulator - 1 / 60);
    }
    renderer.draw(game, accumulator * 60);
    canvas.dataset.frames = String(++frames);
    request = requestAnimationFrame(draw);
  };
  // #endregion
  request = requestAnimationFrame(draw);
  return () => { cancelAnimationFrame(request); input.dispose(); renderer.dispose(); };
}
// #endregion

// #region browser-entry
const canvas = document.createElement('canvas');
document.body.append(canvas);
const stop = mount(canvas);
window.addEventListener('beforeunload', stop);
// #endregion
