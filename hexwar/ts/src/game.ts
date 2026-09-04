// 게임 상태와 명령 — SPEC §8, §11.3

import { canAttack, resolve } from './combat';
import { HexMap } from './hexmap';
import * as los from './los';
import * as P from './path';
import { Rng } from './rng';
import { K_MP, KINDS, NO_UNIT, Unit, UnitPool } from './units';

export const MOVE = 0, ATTACK = 1, ENDTURN = 2;
export const MAX_TURN = 20;

export interface Killed {
  id: number; side: number; kind: number; q: number; r: number;
}

export class Command {
  unit = -1;
  frm = -1;
  to = -1;
  path: number[] = [];
  mp = 0;
  ent = 0;
  moved = false;
  target = -1;
  thp = 0;
  tammo = 0;
  ahp = 0;
  aammo = 0;
  amp = 0;
  rngState = 0;
  killed: Killed[] = [];
  log = '';         // 사람이 읽는 한국어 기록
  alog = '';        // 화면 메시지 줄용 ASCII

  constructor(readonly kind: number) {}
}

export class Game {
  readonly rng: Rng;
  turn = 1;
  side = 0;
  undoStack: Command[] = [];
  log: Array<[string, string]> = [];
  over = false;
  winner = -1;

  constructor(readonly map: HexMap, readonly pool: UnitPool,
              readonly objectives: Array<[number, number]>, seed = 0x1badb002) {
    this.rng = new Rng(seed);
    los.updateFog(this.map, this.pool, 0);
  }

  private name(u: Unit): string {
    return `${KINDS[u.kind]!.name}${u.id}`;
  }

  moveUnit(uid: number, targetIdx: number): Command | null {
    const u = this.pool.get(uid);
    if (!u || u.side !== this.side || this.over) return null;
    const reach = P.reachable(this.map, this.pool, u);
    const here = this.map.axialIdx(u.q, u.r);
    if (!reach.has(targetIdx) || targetIdx === here) return null;

    const cmd = new Command(MOVE);
    cmd.unit = uid;
    cmd.frm = here;
    cmd.to = targetIdx;
    cmd.path = P.tracePath(this.map, reach, targetIdx);
    cmd.mp = u.mp; cmd.ent = u.ent; cmd.moved = u.moved;

    const cost = reach.cost.get(targetIdx)!;
    this.map.occupant[cmd.frm] = NO_UNIT;
    this.map.occupant[targetIdx] = uid;
    [u.q, u.r] = this.map.idxAxial(targetIdx);
    u.mp -= cost;
    const zoc = P.zocMask(this.map, this.pool, u.side);
    if (zoc[targetIdx] === 1) u.mp = 0;
    u.ent = 0;
    u.moved = true;
    cmd.log = `${this.name(u)} 이동 ${cmd.path.length - 1}칸`;
    cmd.alog = `MOVE U${uid} ${cmd.path.length - 1} STEP`;
    this.afterCommand(cmd);
    return cmd;
  }

  attack(uid: number, targetUid: number): Command | null {
    const u = this.pool.get(uid);
    const t = this.pool.get(targetUid);
    if (!u || !t || u.side !== this.side || this.over) return null;
    if (!canAttack(this.map, this.pool, u, t)) return null;

    const cmd = new Command(ATTACK);
    cmd.unit = uid;
    cmd.target = targetUid;
    cmd.frm = this.map.axialIdx(u.q, u.r);
    cmd.mp = u.mp; cmd.ent = u.ent; cmd.moved = u.moved;
    cmd.ahp = u.hp; cmd.aammo = u.ammo; cmd.amp = u.mp;
    cmd.thp = t.hp; cmd.tammo = t.ammo;
    cmd.rngState = this.rng.save();

    const res = resolve(this.map, this.pool, this.rng, u, t);
    const sign = res.score >= 0 ? '+' : '';
    cmd.log = `${this.name(u)} → ${this.name(t)}  2d6=${res.roll} ` +
              `점수${sign}${res.score}  피해 ${res.defenderLoss}/${res.attackerLoss}`;
    cmd.alog = `ATK U${uid}>U${targetUid} ROLL ${res.roll} ` +
               `DMG ${res.defenderLoss}/${res.attackerLoss}`;

    for (const x of [t, u]) {
      if (x.hp <= 0) {
        const i = this.map.axialIdx(x.q, x.r);
        if (i >= 0 && this.map.occupant[i] === x.id) this.map.occupant[i] = NO_UNIT;
        cmd.killed.push({ id: x.id, side: x.side, kind: x.kind, q: x.q, r: x.r });
        this.pool.kill(x.id);
      }
    }
    this.afterCommand(cmd);
    return cmd;
  }

  private checkVictoryOnEnd(): void {
    if (this.pool.count(1) === 0) { this.over = true; this.winner = 0; }
    else if (this.pool.count(0) === 0) { this.over = true; this.winner = 1; }
    else if (this.side === 0) {
      let held = 0;
      for (const [q, r] of this.objectives) {
        const i = this.map.axialIdx(q, r);
        const uid = i >= 0 ? this.map.occupant[i]! : NO_UNIT;
        const u = this.pool.get(uid);
        if (u && u.side === 0) held++;
      }
      if (held === this.objectives.length) { this.over = true; this.winner = 0; }
    }
  }

  endTurn(): Command {
    const cmd = new Command(ENDTURN);
    cmd.log = `${this.turn}턴 ${this.side === 0 ? '청군' : '적군'} 종료`;
    cmd.alog = `END TURN ${this.turn} SIDE ${this.side}`;
    this.undoStack = [];
    this.checkVictoryOnEnd();
    if (this.over) {
      this.log.push([cmd.log, cmd.alog]);
      return cmd;
    }
    this.side = 1 - this.side;
    if (this.side === 0) {
      this.turn++;
      if (this.turn > MAX_TURN) { this.over = true; this.winner = -1; }
    }
    for (const uid of this.pool.aliveIds(this.side)) {
      const u = this.pool.get(uid)!;
      if (!u.moved) u.ent = Math.min(3, u.ent + 1);
      u.mp = K_MP[u.kind]!;
      u.moved = false;
    }
    los.updateFog(this.map, this.pool, 0);
    this.log.push([cmd.log, cmd.alog]);
    return cmd;
  }

  private revive(k: Killed): void {
    const u = new Unit(k.id, k.side, k.kind, k.q, k.r);
    this.pool.slots[k.id] = u;
    if (this.pool.freehead === k.id) {
      this.pool.freehead = this.pool.nextfree[k.id]!;
    } else {
      let prev = this.pool.freehead;
      while (prev >= 0 && this.pool.nextfree[prev]! !== k.id) prev = this.pool.nextfree[prev]!;
      if (prev >= 0) this.pool.nextfree[prev] = this.pool.nextfree[k.id]!;
    }
    const i = this.map.axialIdx(k.q, k.r);
    if (i >= 0) this.map.occupant[i] = k.id;
  }

  undo(): boolean {
    const cmd = this.undoStack.pop();
    if (!cmd) return false;
    if (cmd.kind === MOVE) {
      const u = this.pool.get(cmd.unit)!;
      this.map.occupant[cmd.to] = NO_UNIT;
      this.map.occupant[cmd.frm] = cmd.unit;
      [u.q, u.r] = this.map.idxAxial(cmd.frm);
      u.mp = cmd.mp; u.ent = cmd.ent; u.moved = cmd.moved;
    } else if (cmd.kind === ATTACK) {
      for (const k of cmd.killed) {
        this.pool.slots[k.id] = null;
        this.revive(k);
      }
      const u = this.pool.get(cmd.unit)!;
      const t = this.pool.get(cmd.target)!;
      u.hp = cmd.ahp; u.ammo = cmd.aammo; u.mp = cmd.amp;
      u.ent = cmd.ent; u.moved = cmd.moved;
      t.hp = cmd.thp; t.ammo = cmd.tammo;
      this.rng.restore(cmd.rngState);
    } else {
      return false;
    }
    los.updateFog(this.map, this.pool, 0);
    this.log.pop();
    return true;
  }

  private afterCommand(cmd: Command): void {
    this.undoStack.push(cmd);
    this.log.push([cmd.log, cmd.alog]);
    los.updateFog(this.map, this.pool, 0);
    this.assertConsistent();
  }

  assertConsistent(): void {
    const seen = new Set<number>();
    for (const uid of this.pool.aliveIds()) {
      const u = this.pool.get(uid)!;
      const i = this.map.axialIdx(u.q, u.r);
      if (i < 0) throw new Error(`유닛 ${uid} 가 맵 밖에 있다`);
      if (this.map.occupant[i] !== u.id) {
        throw new Error(`occupant[${i}] 와 유닛 ${uid} 좌표가 어긋났다`);
      }
      if (seen.has(i)) throw new Error(`${i} 칸에 유닛 둘`);
      seen.add(i);
    }
    for (let i = 0; i < this.map.n; i++) {
      const uid = this.map.occupant[i]!;
      if (uid !== NO_UNIT && !this.pool.get(uid)) {
        throw new Error(`occupant[${i}] 가 죽은 유닛`);
      }
    }
  }

  serializeUnits(): string {
    return this.pool.serialize();
  }
}
