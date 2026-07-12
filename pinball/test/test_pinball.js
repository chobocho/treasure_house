// Headless test: extract the <script> from pinball.html, stub browser APIs,
// run the physics loop, and assert basic invariants.
const fs = require("fs");
const html = fs.readFileSync(__dirname + "/../pinball.html", "utf8");
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no script found"); process.exit(1); }
let src = m[1];

// --- Browser stubs ---
const ctxStub = new Proxy({}, {
  get(t, prop) {
    if (prop === "createRadialGradient" || prop === "createLinearGradient")
      return () => ({ addColorStop() {} });
    return () => {};
  },
  set() { return true; }
});
const canvasStub = { width: 480, height: 800, getContext: () => ctxStub };
global.document = { getElementById: () => canvasStub };
const keyHandlers = { keydown: [], keyup: [] };
global.addEventListener = (ev, fn) => { (keyHandlers[ev] ||= []).push(fn); };
let now = 0;
global.performance = { now: () => now };
let rafCb = null;
global.requestAnimationFrame = cb => { rafCb = cb; };

// Run the game script as a CommonJS module so classes are exported
fs.writeFileSync(__dirname + "/_game_module.js",
  src + "\nmodule.exports = { Game, Vec2, reflect, closestPointOnSegment };\n");
const { Game, Vec2, reflect, closestPointOnSegment } = require("./_game_module.js");

// Helper to fire keys
const fire = (type, code) => keyHandlers[type].forEach(f => f({ code, repeat: false }));

// Step N frames at 60fps
function step(frames) {
  for (let i = 0; i < frames; i++) {
    now += 1000 / 60;
    const cb = rafCb; rafCb = null;
    cb(now);
  }
}

// Grab the game instance: the script does `new Game(...)` without keeping a ref,
// so re-create one for testing.
const game = new Game(canvasStub);

// 1) Launch the ball at full power
fire("keydown", "Space");
step(90); // charge ~1.5s -> full power
fire("keyup", "Space");
console.log("launched, inPlay =", game.ball.inPlay, "vel =", game.ball.vel.y.toFixed(0));

// 2) Simulate 30 seconds with flippers mashing
let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
let nanSeen = false, drains = 0, lastBalls = game.balls;
for (let s = 0; s < 30 * 60; s++) {
  if (s % 40 === 0) { fire("keydown", "ArrowLeft"); fire("keydown", "ArrowRight"); }
  if (s % 40 === 20) { fire("keyup", "ArrowLeft"); fire("keyup", "ArrowRight"); }
  // relaunch if ball returned to launcher or was lost
  if (!game.ball.inPlay && !game.gameOver) {
    fire("keydown", "Space"); step(60); fire("keyup", "Space");
  }
  step(1);
  const p = game.ball.pos, v = game.ball.vel;
  if (!isFinite(p.x) || !isFinite(p.y) || !isFinite(v.x) || !isFinite(v.y)) { nanSeen = true; break; }
  if (game.ball.inPlay) {
    minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x);
    minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y);
  }
  if (game.balls < lastBalls) { drains++; lastBalls = game.balls; }
  if (game.gameOver) break;
}

console.log("NaN seen:", nanSeen);
console.log("ball x range: [%s, %s]  (walls at 6 / 474)", minX.toFixed(1), maxX.toFixed(1));
console.log("ball y range: [%s, %s]", minY.toFixed(1), maxY.toFixed(1));
console.log("score:", game.score, " drains:", drains, " gameOver:", game.gameOver);

// Invariants
let fail = 0;
const check = (cond, msg) => { if (!cond) { console.error("FAIL:", msg); fail++; } else console.log("PASS:", msg); };
check(!nanSeen, "no NaN in physics state");
check(minX > 6 - 12 && maxX < 474 + 12, "ball stayed within side walls (± ball radius)");
check(minY > -12, "ball never escaped through the top arch");
check(game.score > 0, "bumpers/slingshots produced score");

// 3) Flipper tip math sanity: tips must not overlap, gap must exceed ball diameter
const g2 = new Game(canvasStub);
const [L, R] = g2.flippers;
const gap = R.tip().x - L.tip().x;
console.log("flipper tip gap:", gap.toFixed(1), "px (ball diameter 22)");
check(gap > 22, "flipper gap wider than ball diameter (drain possible)");
check(gap < 80, "flipper gap not absurdly wide");

// 4) reflect() unit test: 45° incoming on floor normal (0,-1), e=1 -> mirrored
const v = new Vec2(3, 4), n = new Vec2(0, -1);
const r = reflect(v, n, 1);
check(r.x === 3 && r.y === -4, "reflect() mirrors velocity across normal (e=1)");

// 5) closestPointOnSegment clamps to endpoints
const cp = closestPointOnSegment(new Vec2(-5, 0), new Vec2(0, 0), new Vec2(10, 0));
check(cp.x === 0 && cp.y === 0, "closestPointOnSegment clamps t to [0,1]");

process.exit(fail ? 1 : 0);
