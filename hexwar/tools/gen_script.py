# -*- coding: utf-8 -*-
"""입력 스크립트 녹화 — golden/script.txt.

   도스 게임의 데모 리플레이가 정확히 이 방식이었다. 화면을 저장하는 것이
   아니라 '입력만' 저장하고, 재생할 때 같은 엔진에 같은 순서로 먹인다.
   엔진이 결정적이면 화면은 저절로 같아진다 — 그래서 리플레이 파일이
   수십 KB 도 안 됐다.

   여기서는 사람 대신 간단한 계획기가 마우스를 움직인다. 결과물은 사람이
   친 것과 구분되지 않는 순수 입력 로그다.
"""
import io, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'py'))

from hexwar import ai, hexcoord as H, picker as PK, scenario           # noqa: E402
from hexwar.game import Game                                            # noqa: E402
from hexwar.hexmap import MAP_W                                         # noqa: E402
from hexwar.ui import Ui, SELECTED                                      # noqa: E402
from hexwar.units import NO_UNIT                                        # noqa: E402


class Recorder(object):
    def __init__(self):
        m, pool, obj = scenario.load()
        self.g = Game(m, pool, obj)
        self.ui = Ui(self.g)
        self.events = []

    def emit(self, ev):
        self.events.append(ev)
        self.ui.handle(ev)

    def find(self, wid, w=None):
        w = w or self.ui.root
        if w.id == wid:
            return w
        for c in w.children:
            hit = self.find(wid, c)
            if hit is not None:
                return hit
        return None

    def on_screen(self, idx):
        row, col = divmod(idx, MAP_W)
        cx, cy = PK.hex_center(col, row)
        sx, sy = cx - self.ui.cam_x, cy - self.ui.cam_y
        return (sx, sy, 4 <= sx < 252 and 4 <= sy < 164)

    def ensure_visible(self, idx):
        """화면 밖이면 미니맵을 클릭해 카메라를 옮긴다 — 이것도 입력이므로
           반드시 이벤트로 남긴다. 여기서 상태를 몰래 바꾸면 재생이 어긋난다."""
        if self.on_screen(idx)[2]:
            return
        mm = self.find('minimap')
        row, col = divmod(idx, MAP_W)
        self.emit('click %d %d' % (mm.x + col * 2, mm.y + row * 2))

    def click_hex(self, idx):
        self.ensure_visible(idx)
        sx, sy, ok = self.on_screen(idx)
        if not ok:
            return False
        self.emit('click %d %d' % (sx, sy))
        return True

    def plan_unit(self, uid):
        """유닛 하나의 행동. 판단은 게임 상태만 읽고, 조작은 전부 이벤트로 낸다."""
        u = self.g.pool.get(uid)
        if u is None:
            return
        idx = self.g.map.axial_idx(u.q, u.r)
        if not self.click_hex(idx):
            return
        if self.ui.sel_unit != uid:
            return
        if self.ui.attack_overlay:
            self.click_hex(min(self.ui.attack_overlay))
            return
        enemy = ai.nearest_enemy(self.g, u)
        if enemy is None or not self.ui.move_overlay:
            return
        best, bs = -1, 1 << 30
        for i in self.ui.move_overlay:
            q, r = self.g.map.idx_axial(i)
            key = H.distance(q, r, enemy.q, enemy.r) * 100 + self.ui.reach.cost[i]
            if key < bs or (key == bs and i < best):
                best, bs = i, key
        if best >= 0:
            self.click_hex(best)
            # 이동 뒤 사거리에 뭔가 들어왔으면 바로 때린다
            if self.ui.state == SELECTED and self.ui.attack_overlay:
                self.click_hex(min(self.ui.attack_overlay))

    def run(self, turns=10):
        self.emit('render')
        for _t in range(turns):
            if self.g.over:
                break
            if self.g.side == 0:
                for uid in sorted(u.id for u in self.g.pool.iter_alive(0)):
                    self.plan_unit(uid)
                    if self.g.over:
                        break
                self.emit('key TAB')
                self.emit('render')
                self.emit('key E')
                self.emit('key ENTER')
            else:
                self.events.append('ai')
                ai.take_turn(self.g)
                self.g.end_turn()
                self.ui.after_turn()
            self.emit('render')
        # 마지막에 조작 경로를 몇 개 더 밟아 상태 기계의 나머지 간선을 덮는다
        for ev in ('key LEFT', 'key RIGHT', 'key UP', 'key DOWN', 'key TAB',
                   'key T', 'key ESC', 'key E', 'key ESC', 'key U', 'render'):
            self.emit(ev)


def main():
    r = Recorder()
    r.run()
    p = os.path.join(BASE, 'golden', 'script.txt')
    io.open(p, 'w', encoding='utf-8').write(
        ';; HexWar 입력 스크립트 — tools/gen_script.py 가 녹화했다\n' +
        '\n'.join(r.events) + '\n')
    print('%d 이벤트 · %d턴 · 남은 유닛 청 %d 적 %d'
          % (len(r.events), r.g.turn, r.g.pool.count(0), r.g.pool.count(1)))
    print('wrote %s' % p)


if __name__ == '__main__':
    main()
