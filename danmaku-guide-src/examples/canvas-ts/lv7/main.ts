import stage from './stage.json';
import { Game } from './game';
import { Renderer } from './render';
import { bindInput } from './input';
import { Audio } from './audio';
import { loadBest, saveBest, safeStorage } from './storage';

// #region game-mount
export function mount(canvas: HTMLCanvasElement, visible: () => boolean = () => true): () => void {
  // #region adapters-init
  const storage = safeStorage();
  let savedBest = loadBest(storage);
  const game = new Game(undefined, stage, false, savedBest);
  const renderer = new Renderer(canvas), input = bindInput(canvas), audio = new Audio();
  const unlock = () => { void audio.unlock(); };
  canvas.addEventListener('keydown', unlock); canvas.addEventListener('pointerdown', unlock);
  // #endregion
  let previous = performance.now(), accumulator = 0, frames = 0, request = 0;
  // #region fixed-loop
  const draw = (now: number) => {
    accumulator += Math.min(.25, (now - previous) / 1000); previous = now;
    const active = visible() && !document.hidden;
    audio.setActive(active);
    canvas.dataset.audioState = audio.context?.state ?? 'none';
    if (!active) {
      accumulator = 0; request = requestAnimationFrame(draw); return;
    }
    while (accumulator + 1e-12 >= 1 / 60) {
      game.step(input.read());
      // #region adapters-step
      audio.consume(game);
      if (game.highScore > savedBest && saveBest(storage, game.highScore)) savedBest = game.highScore;
      // #endregion
      accumulator = Math.max(0, accumulator - 1 / 60);
    }
    renderer.draw(game, accumulator * 60);
    canvas.dataset.frames = String(++frames);
    canvas.dataset.audio = String(audio.enabled);
    request = requestAnimationFrame(draw);
  };
  // #endregion
  request = requestAnimationFrame(draw);
  // #region adapters-close
  return () => {
    cancelAnimationFrame(request); input.dispose(); audio.close();
    canvas.removeEventListener('keydown', unlock); canvas.removeEventListener('pointerdown', unlock);
  };
  // #endregion
}
// #endregion
