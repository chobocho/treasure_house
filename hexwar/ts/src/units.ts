// 유닛 풀 — SPEC §3

export const MAX_UNITS = 64;
export const NO_UNIT = -1;

export const INF = 0, TANK = 1, ARTY = 2, RECON = 3;

interface KindDef {
  key: string; name: string; mp: number; atk: number; def: number;
  rng: number; vis: number; hp: number; ammo: number; ch: string;
}

export const KINDS: ReadonlyArray<KindDef> = [
  { key: 'INF', name: '보병', mp: 6, atk: 4, def: 5, rng: 1, vis: 2, hp: 10, ammo: 6, ch: 'I' },
  { key: 'TANK', name: '전차', mp: 12, atk: 8, def: 6, rng: 1, vis: 2, hp: 10, ammo: 6, ch: 'T' },
  { key: 'ARTY', name: '포병', mp: 6, atk: 10, def: 2, rng: 3, vis: 2, hp: 8, ammo: 5, ch: 'A' },
  { key: 'RECON', name: '정찰', mp: 16, atk: 3, def: 3, rng: 1, vis: 4, hp: 10, ammo: 4, ch: 'R' },
];

export const K_MP = KINDS.map((k) => k.mp);
export const K_ATK = KINDS.map((k) => k.atk);
export const K_DEF = KINDS.map((k) => k.def);
export const K_RNG = KINDS.map((k) => k.rng);
export const K_VIS = KINDS.map((k) => k.vis);
export const K_HP = KINDS.map((k) => k.hp);
export const K_AMMO = KINDS.map((k) => k.ammo);
export const K_CHAR = KINDS.map((k) => k.ch);

export class Unit {
  hp: number;
  mp: number;
  ammo: number;
  ent = 0;
  alive = true;
  moved = false;

  constructor(readonly id: number, readonly side: number, readonly kind: number,
              public q: number, public r: number) {
    this.hp = K_HP[kind]!;
    this.mp = K_MP[kind]!;
    this.ammo = K_AMMO[kind]!;
  }

  // SPEC §12.1 정규 직렬화 — 필드 순서가 해시에 그대로 들어간다.
  serialize(): string {
    return `${this.id},${this.side},${this.kind},${this.q},${this.r},` +
           `${this.hp},${this.mp},${this.ammo},${this.ent}\n`;
  }
}

export class UnitPool {
  readonly slots: Array<Unit | null>;
  readonly nextfree: Int32Array;
  freehead = -1;

  constructor(readonly cap: number = MAX_UNITS) {
    this.slots = new Array<Unit | null>(cap).fill(null);
    this.nextfree = new Int32Array(cap).fill(-1);
  }

  spawn(side: number, kind: number, q: number, r: number): number {
    let uid: number;
    if (this.freehead >= 0) {
      uid = this.freehead;
      this.freehead = this.nextfree[uid]!;
    } else {
      uid = this.slots.findIndex((s) => s === null);
      if (uid < 0) throw new Error('유닛 풀이 가득 찼다');
    }
    this.slots[uid] = new Unit(uid, side, kind, q, r);
    return uid;
  }

  kill(uid: number): void {
    const u = this.slots[uid];
    if (!u) return;
    u.alive = false;
    this.slots[uid] = null;
    this.nextfree[uid] = this.freehead;
    this.freehead = uid;
  }

  get(uid: number): Unit | null {
    if (uid < 0 || uid >= this.cap) return null;
    return this.slots[uid] ?? null;
  }

  // 아이디 오름차순. 순회 순서가 결과를 바꾸는 자리를 남기지 않기 위해서다.
  aliveIds(side?: number): number[] {
    const out: number[] = [];
    for (let i = 0; i < this.cap; i++) {
      const u = this.slots[i];
      if (u && (side === undefined || u.side === side)) out.push(i);
    }
    return out;
  }

  count(side?: number): number {
    return this.aliveIds(side).length;
  }

  serialize(): string {
    let s = '';
    for (let i = 0; i < this.cap; i++) {
      const u = this.slots[i];
      if (u) s += u.serialize();
    }
    return s;
  }
}
