// 덱 안에서 도는 미니 RPG — 14~16부에 실린 그 엔진 그대로다.
//
// 다시 만든 것이 아니다. `dist/src/*.js` 를 그대로 묶어 넣었고, 이 파일은
// 파일 대신 문자열에서 골든 데이터를 넣어 주고 캔버스에 올리는 일만 한다.
// 그래서 여기서 걸어 다니는 캐릭터의 좌표는 `golden/trace.jsonl` 의 좌표와
// 같은 코드가 계산한 값이다.

import { Game } from '../game';
import * as RA from '../raster';
import { CanvasView } from './canvas';
import { PALETTE_TXT, SCRIPT_TXT, TILES_RLE } from './data';

const TICK_US = 54925;

// 화면 방향키 -> 타일 방향. 6부에서 다룬 45도 어긋남을 여기서 흡수한다.
// 위 화살표를 누르면 화면에서 위로 가야 하는데, 타일 축으로는 NW 다.
const KEY_DIR: { [k: string]: number } = {
  ArrowUp: 5, ArrowRight: 7, ArrowDown: 1, ArrowLeft: 3,
  w: 5, d: 7, s: 1, a: 3,
  q: 6, e: 0, z: 4, c: 2,
};

interface DemoApi {
  w(host: HTMLElement, html: string, cls?: string): void;
}

function el(tag: string, cls?: string): HTMLElement {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}

export function boot(host: HTMLElement, api: DemoApi): void {
  const out = host.querySelector('.out');
  if (!out) return;

  const pal = RA.parsePalette(PALETTE_TXT);
  RA.setLight(RA.buildLight(pal));
  const view = new CanvasView(pal, 2);
  const g = new Game();
  g.setSprites(RA.parseSprites(TILES_RLE));

  const wrap = el('div');
  wrap.appendChild(view.canvas);
  const hud = el('div', 'lbl');
  hud.style.marginTop = '6px';
  wrap.appendChild(hud);
  out.innerHTML = '';
  out.appendChild(wrap);

  let held = -1;
  let act = 0;
  let atk = 0;
  let acc = 0;
  let last = 0;
  let running = true;

  function status(): void {
    const p = g.ents[0];
    if (!p) return;
    const mon = g.ents.filter((e) => e.kind === 1 && e.alive).length;
    const chest = g.ents.filter((e) => e.kind === 2 && e.alive).length;
    hud.textContent =
      '틱 ' + String(g.tickN) + '   체력 ' + String(p.hp) + '/' + String(p.maxhp) +
      '   레벨 ' + String(p.lv) + '   경험치 ' + String(p.xp) +
      '   남은 몬스터 ' + String(mon) + '   안 연 상자 ' + String(chest) +
      '   본 칸 ' + String(g.fog.countSeen());
  }

  function step(now: number): void {
    if (!running) return;
    if (last === 0) last = now;
    let dt = (now - last) * 1000;
    last = now;
    // 탭을 오래 놔뒀다 돌아오면 dt 가 몇 초씩 된다. 한 번에 다섯 틱까지만 따라잡는다.
    if (dt > TICK_US * 5) dt = TICK_US * 5;
    acc += dt;
    let did = false;
    while (acc >= TICK_US) {
      acc -= TICK_US;
      g.inDir = held;
      g.inAct = act;
      g.inAtk = atk;
      act = 0;
      atk = 0;
      g.tick();
      did = true;
    }
    if (did) {
      view.setPhase(g.palPhase);
      view.draw(g.render());
      status();
    }
    requestAnimationFrame(step);
  }

  function onKey(e: KeyboardEvent, down: boolean): void {
    const d = KEY_DIR[e.key];
    if (d !== undefined) {
      // 방향키를 먹지 않으면 덱이 슬라이드를 넘겨 버린다.
      e.preventDefault();
      held = down ? d : (held === d ? -1 : held);
      return;
    }
    if (!down) return;
    if (e.key === ' ') { e.preventDefault(); atk = 1; }
    else if (e.key === 'Enter' || e.key === 'f') { e.preventDefault(); act = 1; }
  }

  // 캔버스가 포커스를 받아야 방향키가 여기로 온다.
  view.canvas.tabIndex = 0;
  view.canvas.style.outline = 'none';
  view.canvas.addEventListener('keydown', (e) => onKey(e as KeyboardEvent, true));
  view.canvas.addEventListener('keyup', (e) => onKey(e as KeyboardEvent, false));
  view.canvas.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    view.canvas.focus();
    // 터치에서는 캔버스를 눌러 방향을 준다 — 누른 지점이 가운데서 어느 쪽인지로.
    const r = view.canvas.getBoundingClientRect();
    const dx = (e as PointerEvent).clientX - (r.left + r.width / 2);
    const dy = (e as PointerEvent).clientY - (r.top + r.height / 2);
    if (Math.abs(dx) < r.width * 0.12 && Math.abs(dy) < r.height * 0.12) { atk = 1; act = 1; return; }
    // 화면 방향을 타일 방향으로 되돌린다. 4부의 역투영과 같은 식이다.
    const a = dx + 2 * dy;
    const b = 2 * dy - dx;
    if (Math.abs(a) > Math.abs(b) * 2) held = a > 0 ? 0 : 4;
    else if (Math.abs(b) > Math.abs(a) * 2) held = b > 0 ? 2 : 6;
    else if (a > 0 && b > 0) held = 1;
    else if (a > 0) held = 7;
    else if (b > 0) held = 3;
    else held = 5;
  });
  view.canvas.addEventListener('pointerup', () => { held = -1; });
  view.canvas.addEventListener('pointerleave', () => { held = -1; });

  const btnStop = host.querySelector('[data-stop]');
  if (btnStop) {
    btnStop.addEventListener('click', () => {
      running = !running;
      (btnStop as HTMLElement).textContent = running ? '멈춤' : '계속';
      if (running) { last = 0; requestAnimationFrame(step); }
    });
  }
  const btnAuto = host.querySelector('[data-auto]');
  if (btnAuto) {
    btnAuto.addEventListener('click', () => {
      // 골든 시나리오 222틱을 그대로 재생한다. 트레이스와 같은 길을 걷는다.
      running = false;
      const g2 = new Game();
      g2.setSprites(g.sprites());
      let i = 0;
      const frames: Uint8Array[] = [];
      g2.runScriptText(SCRIPT_TXT, () => {
        if (i % 3 === 0) frames.push(g2.render().slice());
        i++;
      });
      let k = 0;
      const play = (): void => {
        if (k >= frames.length) { running = true; last = 0; requestAnimationFrame(step); return; }
        view.setPhase(Math.floor(k / 2));
        view.draw(frames[k] as Uint8Array);
        k++;
        setTimeout(play, 40);
      };
      play();
    });
  }

  window.addEventListener('resize', () => view.fit(host.clientWidth || 320));
  view.fit(host.clientWidth || 320);
  api.w(host, '', 'dim');
  out.innerHTML = '';
  out.appendChild(wrap);
  view.draw(g.render());
  status();
  requestAnimationFrame(step);
}
