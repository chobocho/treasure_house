// 게임 상태와 틱 — SPEC §12.
//
// 한 틱은 PIT 기본 분주(18.2065 Hz) 한 번이다. 고정 타임스텝이라
// 프레임을 몇 장 그리든 결과가 같다 — 세 언어의 트레이스를 바이트로 견줄 수 있는 이유다.
import * as fs from 'fs';
import * as path from 'path';

import * as CAM from './camera';
import * as DICE from './dice';
import * as M from './gamemap';
import * as LOS from './los';
import * as P from './path';
import * as PR from './proj';
import * as RA from './raster';
import * as SV from './save';
import * as SD from './sortdag';
import { FP_ONE, fpFloor, fpMul } from './fixed';
import { Rng } from './rng';

export const ROOT = path.resolve(__dirname, '..', '..', '..');
export const GOLDEN = path.join(ROOT, 'golden');

export const SPEED = 13107; // 한 틱에 0.2타일
export const MON_SPEED = 9830; // 몬스터는 조금 느리다 (0.15타일)
export const DIAG_FACTOR = 46341; // round(65536 / sqrt(2))
export const AGGRO_R = 7;
export const ATTACK_EVERY = 12;
export const PATH_EVERY = 8;
export const GAME_SEED = 20260906;

export const K_PLAYER = 0;
export const K_MON = 1;
export const K_CHEST = 2;
export const K_NPC = 3;

// 8방향 -> 스프라이트 4방향. 화면에서 오른쪽아래/왼쪽아래/오른쪽위/왼쪽위 넷이면 족하다.
export const SPRDIR: number[] = [0, 0, 1, 1, 3, 3, 2, 2];

export class Entity {
  eid: number;
  kind: number;
  fx: number;
  fy: number;
  h = 0;
  hp = 1;
  maxhp = 1;
  lv = 1;
  xp = 0;
  atk = 0;
  dfn = 0;
  armor = 0;
  dirn = 2;
  alive = 1;
  anim = 0;
  cool = 0;
  path: Array<[number, number]> | null = null;

  constructor(eid: number, kind: number, tx: number, ty: number) {
    this.eid = eid;
    this.kind = kind;
    this.fx = tx * FP_ONE + FP_ONE / 2; // 타일 중앙
    this.fy = ty * FP_ONE + FP_ONE / 2;
  }

  tile(): [number, number] {
    return [fpFloor(this.fx), fpFloor(this.fy)];
  }
}

export const PLACE_MON: Array<[number, number]> = [
  [20, 20], [28, 21], [21, 28], [27, 27], [24, 14], [24, 40],
];
export const PLACE_CHEST: Array<[number, number]> = [[22, 22], [26, 26], [24, 20]];
export const PLACE_NPC: Array<[number, number]> = [[23, 25], [25, 23]];

// 정렬 상자에 붙는 꼬리표. 파이썬은 ('tile', tx, ty) 처럼 길이도 뜻도 제각각인
// 튜플을 그대로 쓰지만, TS 에서는 판별 union 으로 적어야 컴파일러가 붙잡아 준다.
export type Kind =
  | { t: 'tile'; tx: number; ty: number }
  | { t: 'ent'; e: Entity }
  | { t: 'spr'; sid: number; tx: number; ty: number; h: number };

export class Game {
  map: M.GameMap;
  rng: Rng;
  fog: LOS.Fog;
  tickN = 0;
  cycleBreaks = 0;
  palPhase = 0;
  slot: Uint8Array | null = null;
  inDir = -1;
  inAct = 0;
  inAtk = 0;
  ents: Entity[] = [];
  camX = 0;
  camY = 0;
  private frame: RA.Frame | null = null;
  private spr: RA.Sprite[] | null = null;

  constructor() {
    this.map = M.genMap();
    this.rng = new Rng(GAME_SEED);
    this.fog = new LOS.Fog(M.MAP_W, M.MAP_H);
    this.buildEntities();
    const p0 = this.ents[0] as Entity;
    const [px, py] = PR.worldToScreen(p0.fx, p0.fy, p0.h);
    const c = CAM.clampCam(px - PR.SCR_W / 2, py - PR.SCR_H / 2);
    this.camX = c[0];
    this.camY = c[1];
    const t0 = p0.tile();
    this.fog.update(this.map, t0[0], t0[1]);
  }

  // ------------------------------------------------------------ 초기 배치
  private buildEntities(): void {
    const p = new Entity(0, K_PLAYER, 24, 34);
    p.hp = 60;
    p.maxhp = 60;
    p.atk = 4;
    p.dfn = 3;
    p.armor = 2;
    this.ents.push(p);
    PLACE_MON.forEach((pos, k) => {
      const e = new Entity(k + 1, K_MON, pos[0], pos[1]);
      e.hp = 8 + k;
      e.maxhp = 8 + k;
      e.atk = 1;
      e.dfn = 0;
      e.armor = 0;
      this.ents.push(e);
    });
    for (const pos of PLACE_CHEST) {
      this.ents.push(new Entity(this.ents.length, K_CHEST, pos[0], pos[1]));
    }
    for (const pos of PLACE_NPC) {
      this.ents.push(new Entity(this.ents.length, K_NPC, pos[0], pos[1]));
    }
    for (const e of this.ents) {
      const t = e.tile();
      e.h = this.map.height(t[0], t[1]);
    }
  }

  // ------------------------------------------------------------ 이동
  canStand(e: Entity, fx: number, fy: number): boolean {
    const tx = fpFloor(fx);
    const ty = fpFloor(fy);
    if (!P.passable(this.map, tx, ty)) return false;
    const dh = this.map.height(tx, ty) - e.h;
    return -P.CLIMB_MAX <= dh && dh <= P.CLIMB_MAX;
  }

  /** 방향 d 로 한 틱만큼. 막히면 축을 하나씩 떼어 미끄러진다.
   *
   *  도스 RPG 의 조작감은 이 '미끄러짐'에서 온다. 벽에 비스듬히 부딪혔을 때
   *  딱 멈추면 답답하고, 벽을 타고 흐르면 자연스럽다. */
  moveEntity(e: Entity, d: number, speed: number): boolean {
    let dx = (P.DIRX[d] as number) * speed;
    let dy = (P.DIRY[d] as number) * speed;
    if (P.DIAG[d]) {
      dx = fpMul(dx, DIAG_FACTOR);
      dy = fpMul(dy, DIAG_FACTOR);
    }
    const nfx = e.fx + dx;
    const nfy = e.fy + dy;
    let moved = false;
    if (this.canStand(e, nfx, nfy)) {
      e.fx = nfx;
      e.fy = nfy;
      moved = true;
    } else if (dx && this.canStand(e, nfx, e.fy)) {
      e.fx = nfx;
      moved = true;
    } else if (dy && this.canStand(e, e.fx, nfy)) {
      e.fy = nfy;
      moved = true;
    }
    e.dirn = d;
    const t = e.tile();
    e.h = this.map.height(t[0], t[1]);
    if (moved) e.anim += 1;
    return moved;
  }

  // ------------------------------------------------------------ 전투
  adjacent(a: Entity, b: Entity): boolean {
    const ta = a.tile();
    const tb = b.tile();
    const dx = ta[0] - tb[0];
    const dy = ta[1] - tb[1];
    return dx >= -1 && dx <= 1 && dy >= -1 && dy <= 1;
  }

  private levelUp(a: Entity): void {
    while (a.xp >= DICE.xpToNext(a.lv)) {
      a.xp -= DICE.xpToNext(a.lv);
      a.lv += 1;
      const v = this.rng.next();
      a.maxhp += 4 + (v - 5 * Math.floor(v / 5));
      a.hp = a.maxhp;
      a.atk += 1;
      if (a.lv % 2 === 0) a.dfn += 1;
    }
  }

  doAttack(a: Entity, b: Entity): boolean {
    const res = DICE.attack(this.rng, a.atk, b.dfn, 1, 6, a.atk, b.armor);
    if (!res.hit) return false;
    b.hp -= res.dmg;
    if (b.hp <= 0) {
      b.hp = 0;
      b.alive = 0;
      if (a.kind === K_PLAYER) {
        a.xp += 20 + 5 * b.maxhp;
        this.levelUp(a);
      }
    }
    return true;
  }

  // ------------------------------------------------------------ 한 틱
  /** SPEC §12.2 의 순서를 그대로. 순서가 곧 명세다. */
  tick(): void {
    const p = this.ents[0] as Entity;
    // 1~2. 입력과 플레이어 이동
    if (this.inDir >= 0) this.moveEntity(p, this.inDir, SPEED);
    // 3. 몬스터
    const pt = p.tile();
    const ptx = pt[0];
    const pty = pt[1];
    for (const e of this.ents) {
      if (e.kind !== K_MON || !e.alive) continue;
      const et = e.tile();
      const etx = et[0];
      const ety = et[1];
      const dx = etx - ptx;
      const dy = ety - pty;
      const near = dx >= -AGGRO_R && dx <= AGGRO_R && dy >= -AGGRO_R && dy <= AGGRO_R;
      if (!(near && LOS.visible(this.map, etx, ety, ptx, pty))) {
        e.path = null;
        continue;
      }
      if (this.adjacent(e, p)) {
        if (e.cool <= 0) {
          this.doAttack(e, p);
          e.cool = ATTACK_EVERY;
        } else {
          e.cool -= 1;
        }
        continue;
      }
      if (e.cool > 0) e.cool -= 1;
      if (e.path === null || this.tickN % PATH_EVERY === 0) {
        e.path = P.astar(this.map, etx, ety, ptx, pty).path;
      }
      if (e.path !== null && e.path.length > 1) {
        const nxt = e.path[1] as [number, number];
        const nx = nxt[0];
        const ny = nxt[1];
        let d = -1;
        for (let k = 0; k < 8; k++) {
          if (P.DIRX[k] === nx - etx && P.DIRY[k] === ny - ety) {
            d = k;
            break;
          }
        }
        if (d >= 0) {
          this.moveEntity(e, d, MON_SPEED);
          const nt = e.tile();
          if (nt[0] === nx && nt[1] === ny) e.path = e.path.slice(1);
        }
      }
    }
    // 4. 플레이어 명령
    if (this.inAtk) {
      for (const e of this.ents) {
        if (e.kind === K_MON && e.alive && this.adjacent(p, e)) {
          this.doAttack(p, e);
          break;
        }
      }
    }
    if (this.inAct) {
      for (const e of this.ents) {
        if (e.kind === K_CHEST && e.alive && this.adjacent(p, e)) {
          e.alive = 0;
          p.xp += 30;
          this.levelUp(p);
          break;
        }
      }
    }
    // 5. 안개와 조명
    this.fog.update(this.map, ptx, pty);
    // 6. 카메라
    const s = PR.worldToScreen(p.fx, p.fy, p.h);
    const c = CAM.follow(this.camX, this.camY, s[0], s[1]);
    this.camX = c[0];
    this.camY = c[1];
    // 7. 틱
    this.tickN += 1;
    this.palPhase = Math.floor(this.tickN / 4);
  }

  // ------------------------------------------------------------ 트레이스
  traceLine(): string {
    const p = this.ents[0] as Entity;
    let mon = 0;
    for (const e of this.ents) if (e.kind === K_MON && e.alive) mon += 1;
    // 세이브 끝에 붙은 CRC 를 그대로 읽는다. 세이브 전체를 다시 crc16 하면
    // 언제나 0이 나온다 — CCITT-FALSE 의 성질이라 값으로는 쓸모가 없다.
    const blob = SV.packState(this);
    const crc = (blob[blob.length - 2] as number) * 256 + (blob[blob.length - 1] as number);
    return '{"t":' + this.tickN + ',"px":' + p.fx + ',"py":' + p.fy + ',"ph":' + p.h
      + ',"hp":' + p.hp + ',"lv":' + p.lv + ',"xp":' + p.xp
      + ',"rng":' + this.rng.s + ',"cam":[' + this.camX + ',' + this.camY + ']'
      + ',"seen":' + this.fog.countSeen() + ',"vis":' + this.fog.countVisible()
      + ',"mon":' + mon + ',"crc":' + crc + '}';
  }

  /** 골든 시나리오를 돌린다. emit 이 있으면 매 틱 한 줄씩 넘긴다.
   *
   *  limit 을 주면 그만큼 '진행한 틱' 뒤에 멈춘다. tick_n 이 아니라
   *  실제로 돌린 횟수다 — load 가 시계를 되돌리기 때문이다. */
  runScript(
    scriptPath?: string | null,
    emit?: ((line: string) => void) | null,
    limit?: number | null,
  ): Game {
    let done = 0;
    const text = fs.readFileSync(scriptPath ?? path.join(GOLDEN, 'script.txt'), 'utf8');
    for (const raw of text.split('\n')) {
      const line = raw.trim();
      if (!line || line.startsWith('#')) continue;
      const q = line.split(/\s+/);
      const cmd = q[0] as string;
      if (cmd === 'mark') {
        if (emit) emit('{"mark":"' + (q[1] as string) + '","t":' + this.tickN + '}');
        continue;
      }
      if (cmd === 'save') {
        this.slot = SV.packState(this);
        continue;
      }
      if (cmd === 'load') {
        if (this.slot !== null) SV.unpackState(this.slot, this);
        continue;
      }
      let n: number;
      if (cmd === 'hold') {
        const d = P.DIR_NAME.indexOf(q[1] as string);
        n = parseInt(q[2] as string, 10);
        this.inDir = d;
        this.inAct = 0;
        this.inAtk = 0;
      } else if (cmd === 'wait') {
        n = parseInt(q[1] as string, 10);
        this.inDir = -1;
        this.inAct = 0;
        this.inAtk = 0;
      } else if (cmd === 'act') {
        n = 1;
        this.inDir = -1;
        this.inAct = 1;
        this.inAtk = 0;
      } else if (cmd === 'atk') {
        n = 1;
        this.inDir = -1;
        this.inAct = 0;
        this.inAtk = 1;
      } else {
        throw new Error('모르는 명령: ' + cmd);
      }
      for (let k = 0; k < n; k++) {
        this.tick();
        done += 1;
        if (emit) emit(this.traceLine());
        if (limit !== undefined && limit !== null && done >= limit) {
          this.inDir = -1;
          this.inAct = 0;
          this.inAtk = 0;
          return this;
        }
      }
    }
    this.inDir = -1;
    this.inAct = 0;
    this.inAtk = 0;
    return this;
  }

  // ------------------------------------------------------------ 렌더
  sprites(): RA.Sprite[] {
    if (this.spr === null) this.spr = RA.loadSprites();
    return this.spr;
  }

  /** 정렬에 넣을 상자들. 지형 기둥과 물체를 한 통에 넣는다.
   *
   *  지형을 빼고 물체끼리만 정렬하면 절벽 뒤에 선 캐릭터가 절벽 위로 뜬다. */
  private boxes(): [SD.Box[], Kind[]] {
    const m = this.map;
    const [tx0, ty0, tx1, ty1] = PR.visibleRange(
      this.camX, this.camY, this.camX + PR.SCR_W, this.camY + PR.SCR_H,
    );
    const boxes: SD.Box[] = [];
    const kinds: Kind[] = [];
    for (let ty = ty0; ty <= ty1; ty++) {
      for (let tx = tx0; tx <= tx1; tx++) {
        const h = m.height(tx, ty);
        boxes.push([boxes.length, tx, ty, 0, tx + 1, ty + 1, h + 1]);
        kinds.push({ t: 'tile', tx, ty });
      }
    }
    for (const e of this.ents) {
      if (!e.alive && e.kind === K_MON) continue;
      const t = e.tile();
      const tx = t[0];
      const ty = t[1];
      if (!(tx0 <= tx && tx <= tx1 && ty0 <= ty && ty <= ty1)) continue;
      boxes.push([boxes.length, tx, ty, e.h, tx + 1, ty + 1, e.h + 3]);
      kinds.push({ t: 'ent', e });
    }
    // 장식: 숲에는 나무, 바위 지형에는 바위. 배치는 좌표만으로 정해 결정적이다.
    for (let ty = ty0; ty <= ty1; ty++) {
      for (let tx = tx0; tx <= tx1; tx++) {
        const t = m.terrain(tx, ty);
        const h = m.height(tx, ty);
        if (t === M.T_FOREST && (tx * 7 + ty * 13) % 5 === 0) {
          boxes.push([boxes.length, tx, ty, h, tx + 1, ty + 1, h + 4]);
          kinds.push({ t: 'spr', sid: 46, tx, ty, h });
        } else if (t === M.T_ROCK && (tx * 11 + ty * 5) % 7 === 0) {
          boxes.push([boxes.length, tx, ty, h, tx + 1, ty + 1, h + 2]);
          kinds.push({ t: 'spr', sid: 47, tx, ty, h });
        }
      }
    }
    return [boxes, kinds];
  }

  /** 한 프레임. 정렬 결과대로 지형 기둥과 물체를 차례로 올린다. */
  render(): Uint8Array {
    const spr = this.sprites();
    if (this.frame === null) this.frame = new RA.Frame();
    const f = this.frame;
    f.clear(0);
    const m = this.map;
    const [boxes, kinds] = this.boxes();
    const [order, breaks] = SD.topoSort(boxes);
    this.cycleBreaks += breaks;
    const pt = (this.ents[0] as Entity).tile();
    const ptx = pt[0];
    const pty = pt[1];
    for (const bid of order) {
      const kind = kinds[bid] as Kind;
      if (kind.t === 'tile') {
        const tx = kind.tx;
        const ty = kind.ty;
        const lv = this.fog.lightOf(tx, ty, ptx, pty);
        if (lv === 0) continue;
        const t = m.terrain(tx, ty);
        const h = m.height(tx, ty);
        if (h === 0) {
          const s = PR.tileToScreen(tx, ty, 0);
          f.blitRle(spr[t] as RA.Sprite, s[0] - this.camX, s[1] - this.camY, lv);
        } else {
          for (let k = 1; k <= h; k++) {
            const s = PR.tileToScreen(tx, ty, k);
            f.blitRle(spr[16 + t] as RA.Sprite, s[0] - this.camX, s[1] - this.camY, lv);
          }
        }
      } else if (kind.t === 'ent') {
        const e = kind.e;
        const t = e.tile();
        const lv = this.fog.lightOf(t[0], t[1], ptx, pty);
        if (lv === 0) continue;
        const s = PR.worldToScreen(e.fx, e.fy, e.h);
        const sy = s[1] + PR.HH;
        let sid: number;
        if (e.kind === K_PLAYER) {
          sid = 32 + (SPRDIR[e.dirn] as number) * 2 + (Math.floor(e.anim / 4) % 2);
        } else if (e.kind === K_MON) {
          sid = 40 + ((Math.floor(this.tickN / 6) + e.eid) % 2);
        } else if (e.kind === K_CHEST) {
          sid = e.alive ? 42 : 43;
        } else {
          sid = 44 + (e.eid % 2);
        }
        f.blitRle(spr[sid] as RA.Sprite, s[0] - this.camX, sy - this.camY, lv);
      } else {
        const lv = this.fog.lightOf(kind.tx, kind.ty, ptx, pty);
        if (lv === 0) continue;
        const s = PR.tileToScreen(kind.tx, kind.ty, kind.h);
        f.blitRle(spr[kind.sid] as RA.Sprite, s[0] - this.camX, s[1] + PR.HH - this.camY, lv);
      }
    }
    return f.fb;
  }

  renderPpm(): Uint8Array {
    const pal = RA.cyclePalette(RA.loadPalette(), this.palPhase);
    return RA.toPpm(this.render(), pal);
  }
}

export function runScriptTrace(scriptPath?: string | null): string {
  const g = new Game();
  const out: string[] = [];
  g.runScript(scriptPath ?? null, (l) => out.push(l));
  return out.join('\n') + '\n';
}
