import { readFileSync, existsSync } from 'node:fs';
// #region replay-run
const level = Number(process.argv[2]);
if (!Number.isInteger(level) || level < 1 || level > 7) throw new Error('잘못된 레벨');
const src = new URL('../../', import.meta.url);
const { Game } = await import(new URL('dist/canvas-lv' + level + '-logic.mjs', src));
const events = JSON.parse(readFileSync(new URL('lv' + level + '/replay.json', import.meta.url)));
const stagePath = new URL('lv' + level + '/stage.json', import.meta.url);
const stage = existsSync(stagePath) ? JSON.parse(readFileSync(stagePath)) : undefined;
const game = new Game(undefined, stage);
let bits = 0, cursor = 0;
const checkpoints = [];
for (let frame = 0; frame < 1800; frame++) {
  if (cursor < events.length && events[cursor].frame === frame) bits = events[cursor++].bits;
  game.step(bits);
  if ([60, 600, 1800].includes(game.frame)) checkpoints.push(game.snapshot());
}
console.log(JSON.stringify({ checkpoints, state: game.snapshot() }));
// #endregion
