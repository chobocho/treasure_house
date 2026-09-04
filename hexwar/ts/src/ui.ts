// GUI 셸 — SPEC §11

import { Game } from './game';
import * as H from './hexcoord';
import { FOG_VISIBLE, MAP_H, MAP_W } from './hexmap';
import * as P from './path';
import * as PK from './picker';
import { CAM_MAX_X, CAM_MAX_Y, MSG, PANEL_RECT, VIEW } from './layout';
import { K_RNG, NO_UNIT, Unit } from './units';

export const enum Kind { PANEL, BUTTON, LABEL, MINIMAP, MAPVIEW, LOG, DIALOG }
export const enum State { IDLE, SELECTED, TARGETING, DIALOG, GAMEOVER }

export const STATE_NAMES = ['IDLE', 'SELECTED', 'TARGETING', 'DIALOG', 'GAMEOVER'] as const;

export interface Widget {
  id: string;
  x: number; y: number; w: number; h: number;
  kind: Kind;
  label: string;
  enabled: boolean;
  visible: boolean;
  children: Widget[];
}

function widget(id: string, x: number, y: number, w: number, h: number,
                kind: Kind, label = '', children: Widget[] = []): Widget {
  return { id, x, y, w, h, kind, label, enabled: true, visible: true, children };
}

export function buildUi(): Widget {
  const minimap = widget('minimap', PANEL_RECT[0] + 6, 24, 48, 36, Kind.MINIMAP);
  const btnEnd = widget('end', PANEL_RECT[0] + 4, 150, 56, 12, Kind.BUTTON, 'END TURN');
  const btnUndo = widget('undo', PANEL_RECT[0] + 4, 164, 56, 12, Kind.BUTTON, 'UNDO');
  const btnNext = widget('next', PANEL_RECT[0] + 4, 178, 56, 12, Kind.BUTTON, 'NEXT UNIT');
  const panel = widget('panel', PANEL_RECT[0], PANEL_RECT[1], PANEL_RECT[2], PANEL_RECT[3],
                       Kind.PANEL, '', [minimap, btnEnd, btnUndo, btnNext]);
  const mapview = widget('map', VIEW[0], VIEW[1], VIEW[2], VIEW[3], Kind.MAPVIEW);
  const logw = widget('log', MSG[0], MSG[1], MSG[2], MSG[3], Kind.LOG);
  const yes = widget('yes', 100, 112, 40, 14, Kind.BUTTON, 'YES');
  const no = widget('no', 180, 112, 40, 14, Kind.BUTTON, 'NO');
  const dlg = widget('dialog', 80, 74, 160, 56, Kind.DIALOG, 'END TURN?', [yes, no]);
  dlg.visible = false;
  return widget('root', 0, 0, 320, 200, Kind.PANEL, '', [mapview, logw, panel, dlg]);
}

function contains(w: Widget, px: number, py: number): boolean {
  return px >= w.x && px < w.x + w.w && py >= w.y && py < w.y + w.h;
}

// 뒤에서 앞으로 훑어 가장 위의 위젯을 찾는다 — 그리기 순서의 정확한 역순.
export function hitTest(w: Widget, px: number, py: number): Widget | null {
  if (!w.visible || !contains(w, px, py)) return null;
  for (let i = w.children.length - 1; i >= 0; i--) {
    const hit = hitTest(w.children[i]!, px, py);
    if (hit) return hit;
  }
  return w.enabled ? w : null;
}

export class Ui {
  readonly root: Widget = buildUi();
  state: State = State.IDLE;
  prevState: State = State.IDLE;
  camX = 0;
  camY = 0;
  cursorIdx = -1;
  selIdx = -1;
  selUnit = -1;
  moveOverlay = new Set<number>();
  attackOverlay = new Set<number>();
  reach: P.Reach | null = null;
  readonly objectiveIdx = new Set<number>();

  constructor(readonly g: Game) {
    for (const [q, r] of g.objectives) this.objectiveIdx.add(g.map.axialIdx(q, r));
  }

  stateName(): string { return STATE_NAMES[this.state]!; }

  asciiLog(g: Game, n: number): string[] {
    return g.log.slice(Math.max(0, g.log.length - n)).map((p) => p[1]).reverse();
  }

  clampCam(): void {
    this.camX = Math.max(0, Math.min(CAM_MAX_X, this.camX));
    this.camY = Math.max(0, Math.min(CAM_MAX_Y, this.camY));
  }

  scroll(dx: number, dy: number): void {
    this.camX += dx;
    this.camY += dy;
    this.clampCam();
  }

  centerOn(idx: number): void {
    const row = Math.floor(idx / MAP_W);
    const [cx, cy] = PK.hexCenter(idx - row * MAP_W, row);
    this.camX = cx - (VIEW[2] >> 1);
    this.camY = cy - (VIEW[3] >> 1);
    this.clampCam();
  }

  private attackTargets(u: Unit): Set<number> {
    const out = new Set<number>();
    if (u.ammo <= 0 || u.mp <= 0) return out;
    const m = this.g.map;
    for (const tid of this.g.pool.aliveIds()) {
      const t = this.g.pool.get(tid)!;
      if (t.side === u.side) continue;
      const i = m.axialIdx(t.q, t.r);
      if (i < 0 || m.fog[i] !== FOG_VISIBLE) continue;
      if (H.distance(u.q, u.r, t.q, t.r) <= K_RNG[u.kind]!) out.add(i);
    }
    return out;
  }

  select(uid: number): boolean {
    const u = this.g.pool.get(uid);
    if (!u || u.side !== this.g.side) return false;
    this.selUnit = uid;
    this.selIdx = this.g.map.axialIdx(u.q, u.r);
    this.reach = P.reachable(this.g.map, this.g.pool, u);
    this.moveOverlay = new Set(
      this.reach.list.filter((i) => i !== this.selIdx &&
                                    this.g.map.occupant[i] === NO_UNIT));
    this.attackOverlay = this.attackTargets(u);
    this.state = State.SELECTED;
    return true;
  }

  deselect(): void {
    this.selUnit = -1;
    this.selIdx = -1;
    this.reach = null;
    this.moveOverlay = new Set();
    this.attackOverlay = new Set();
    this.state = State.IDLE;
  }

  nextUnit(): boolean {
    const ids = this.g.pool.aliveIds(this.g.side).filter((i) => this.g.pool.get(i)!.mp > 0);
    if (ids.length === 0) return false;
    const at = ids.indexOf(this.selUnit);
    const nxt = at >= 0 ? ids[(at + 1) % ids.length]! : ids[0]!;
    if (this.select(nxt)) {
      this.centerOn(this.selIdx);
      return true;
    }
    return false;
  }

  handle(ev: string): boolean {
    const parts = ev.split(' ');
    if (parts[0] === 'click') return this.onClick(Number(parts[1]), Number(parts[2]));
    if (parts[0] === 'key') return this.onKey(parts[1]!);
    if (parts[0] === 'render') return true;
    throw new Error(`알 수 없는 이벤트: ${ev}`);
  }

  onClick(x: number, y: number): boolean {
    const w = hitTest(this.root, x, y);
    if (!w) return false;
    if (this.state === State.DIALOG) {
      // 모달: 대화상자 밖의 클릭은 통째로 버린다
      if (w.id === 'yes') {
        this.closeDialog();
        this.g.endTurn();
        this.afterTurn();
        return true;
      }
      if (w.id === 'no') { this.closeDialog(); return true; }
      return false;
    }
    if (w.kind === Kind.BUTTON) return this.onButton(w.id);
    if (w.id === 'minimap') return this.onMinimap(x, y, w);
    if (w.kind === Kind.MAPVIEW) return this.onMapClick(x, y);
    return false;
  }

  onButton(wid: string): boolean {
    if (wid === 'end') { this.openDialog(); return true; }
    if (wid === 'undo') {
      const ok = this.g.undo();
      if (ok && this.selUnit >= 0) {
        if (!this.g.pool.get(this.selUnit)) this.deselect();
        else this.select(this.selUnit);
      }
      return ok;
    }
    if (wid === 'next') return this.nextUnit();
    return false;
  }

  onMinimap(x: number, y: number, w: Widget): boolean {
    const col = Math.min(MAP_W - 1, Math.max(0, Math.floor((x - w.x) / 2)));
    const row = Math.min(MAP_H - 1, Math.max(0, Math.floor((y - w.y) / 2)));
    this.centerOn(row * MAP_W + col);
    return true;
  }

  onMapClick(x: number, y: number): boolean {
    const hexpos = PK.pick(x, y, this.camX, this.camY);
    if (!hexpos) return false;
    const i = hexpos[1] * MAP_W + hexpos[0];
    this.cursorIdx = i;
    const m = this.g.map;
    const uid = m.occupant[i]!;

    if (this.state === State.TARGETING) {
      if (this.attackOverlay.has(i) && uid !== NO_UNIT) {
        this.g.attack(this.selUnit, uid);
        this.afterAction();
        return true;
      }
      this.state = State.SELECTED;
      return false;
    }

    if (this.state === State.SELECTED) {
      if (this.attackOverlay.has(i) && uid !== NO_UNIT) {
        this.g.attack(this.selUnit, uid);
        this.afterAction();
        return true;
      }
      if (this.moveOverlay.has(i)) {
        this.g.moveUnit(this.selUnit, i);
        this.afterAction();
        return true;
      }
    }

    if (uid !== NO_UNIT && m.fog[i] === FOG_VISIBLE) {
      const u = this.g.pool.get(uid);
      if (u && u.side === this.g.side) return this.select(uid);
    }
    this.deselect();
    return true;
  }

  onKey(k: string): boolean {
    if (this.state === State.DIALOG) {
      if (k === 'ESC') { this.closeDialog(); return true; }
      if (k === 'ENTER') {
        this.closeDialog();
        this.g.endTurn();
        this.afterTurn();
        return true;
      }
      return false;
    }
    if (k === 'LEFT') this.scroll(-PK.HEX_W, 0);
    else if (k === 'RIGHT') this.scroll(PK.HEX_W, 0);
    else if (k === 'UP') this.scroll(0, -PK.ROW_STEP);
    else if (k === 'DOWN') this.scroll(0, PK.ROW_STEP);
    else if (k === 'TAB') return this.nextUnit();
    else if (k === 'U') return this.onButton('undo');
    else if (k === 'E') this.openDialog();
    else if (k === 'T') {
      if (this.state === State.SELECTED && this.attackOverlay.size > 0) {
        this.state = State.TARGETING;
      } else return false;
    } else if (k === 'ESC') {
      if (this.state === State.TARGETING) this.state = State.SELECTED;
      else this.deselect();
    } else return false;
    return true;
  }

  private dlg(): Widget {
    const d = this.root.children.find((c) => c.id === 'dialog');
    if (!d) throw new Error('dialog');
    return d;
  }

  openDialog(): void {
    this.prevState = this.state;
    this.state = State.DIALOG;
    this.dlg().visible = true;
  }

  closeDialog(): void {
    this.dlg().visible = false;
    this.state = this.prevState;
  }

  afterAction(): void {
    const u = this.g.pool.get(this.selUnit);
    if (this.g.over) {
      this.state = State.GAMEOVER;
      this.moveOverlay = new Set();
      this.attackOverlay = new Set();
      return;
    }
    if (!u || (u.mp <= 0 && u.ammo <= 0)) this.deselect();
    else this.select(this.selUnit);
  }

  afterTurn(): void {
    this.deselect();
    if (this.g.over) this.state = State.GAMEOVER;
  }

  digest(): string {
    return `${this.stateName()}|sel=${this.selUnit}|cur=${this.cursorIdx}` +
           `|cam=${this.camX},${this.camY}|mov=${this.moveOverlay.size}` +
           `|atk=${this.attackOverlay.size}`;
  }
}
