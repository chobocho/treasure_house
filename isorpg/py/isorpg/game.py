# -*- coding: utf-8 -*-
"""게임 상태와 틱 — SPEC §12.

   한 틱은 PIT 기본 분주(18.2065 Hz) 한 번이다. 고정 타임스텝이라
   프레임을 몇 장 그리든 결과가 같다 — 세 언어의 트레이스를 바이트로 견줄 수 있는
   이유가 그것이다.
"""
import io
import os

from . import camera as CAM
from . import dice as DICE
from . import gamemap as M
from . import los as LOS
from . import path as P
from . import proj as PR
from . import raster as RA
from . import save as SV
from . import sortdag as SD
from .fixed import FP_ONE, fp_floor, fp_mul
from .rng import Rng

_HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLDEN = os.path.join(_HERE, 'golden')

SPEED = 13107                   # 한 틱에 0.2타일
MON_SPEED = 9830                # 몬스터는 조금 느리다 (0.15타일)
DIAG_FACTOR = 46341             # round(65536 / sqrt(2))
AGGRO_R = 7
ATTACK_EVERY = 12
PATH_EVERY = 8
GAME_SEED = 20260906

K_PLAYER, K_MON, K_CHEST, K_NPC = 0, 1, 2, 3

# 8방향 -> 스프라이트 4방향. 화면에서 오른쪽아래/왼쪽아래/오른쪽위/왼쪽위 넷이면 족하다.
SPRDIR = [0, 0, 1, 1, 3, 3, 2, 2]


class Entity(object):
    __slots__ = ('eid', 'kind', 'fx', 'fy', 'h', 'hp', 'maxhp', 'lv', 'xp',
                 'atk', 'dfn', 'armor', 'dirn', 'alive', 'anim', 'cool', 'path')

    def __init__(self, eid, kind, tx, ty):
        self.eid = eid
        self.kind = kind
        self.fx = tx * FP_ONE + FP_ONE // 2        # 타일 중앙
        self.fy = ty * FP_ONE + FP_ONE // 2
        self.h = 0
        self.hp = 1
        self.maxhp = 1
        self.lv = 1
        self.xp = 0
        self.atk = 0
        self.dfn = 0
        self.armor = 0
        self.dirn = 2
        self.alive = 1
        self.anim = 0
        self.cool = 0
        self.path = None

    def tile(self):
        return (fp_floor(self.fx), fp_floor(self.fy))


PLACE_MON = [(20, 20), (28, 21), (21, 28), (27, 27), (24, 14), (24, 40)]
PLACE_CHEST = [(22, 22), (26, 26), (24, 20)]
PLACE_NPC = [(23, 25), (25, 23)]


class Game(object):
    def __init__(self):
        self.map = M.gen_map()
        self.rng = Rng(GAME_SEED)
        self.fog = LOS.Fog(M.MAP_W, M.MAP_H)
        self.tick_n = 0
        self.cycle_breaks = 0
        self.pal_phase = 0
        self.slot = None
        self.in_dir = -1
        self.in_act = 0
        self.in_atk = 0
        self.ents = []
        self.log = []
        self._build_entities()
        px, py = PR.world_to_screen(self.ents[0].fx, self.ents[0].fy, self.ents[0].h)
        self.cam_x, self.cam_y = CAM.clamp_cam(px - PR.SCR_W // 2, py - PR.SCR_H // 2)
        self.fog.update(self.map, *self.ents[0].tile())
        self._frame = None
        self._sprites = None

    # ------------------------------------------------------------ 초기 배치
    def _build_entities(self):
        p = Entity(0, K_PLAYER, 24, 34)
        p.hp = p.maxhp = 60
        p.atk, p.dfn, p.armor = 4, 3, 2
        self.ents.append(p)
        for k, (tx, ty) in enumerate(PLACE_MON):
            e = Entity(k + 1, K_MON, tx, ty)
            e.hp = e.maxhp = 8 + k
            e.atk, e.dfn, e.armor = 1, 0, 0
            self.ents.append(e)
        for k, (tx, ty) in enumerate(PLACE_CHEST):
            e = Entity(len(self.ents), K_CHEST, tx, ty)
            self.ents.append(e)
        for k, (tx, ty) in enumerate(PLACE_NPC):
            e = Entity(len(self.ents), K_NPC, tx, ty)
            self.ents.append(e)
        for e in self.ents:
            tx, ty = e.tile()
            e.h = self.map.height(tx, ty)

    # ------------------------------------------------------------ 이동
    def can_stand(self, e, fx, fy):
        tx, ty = fp_floor(fx), fp_floor(fy)
        if not P.passable(self.map, tx, ty):
            return False
        dh = self.map.height(tx, ty) - e.h
        return -P.CLIMB_MAX <= dh <= P.CLIMB_MAX

    def move_entity(self, e, d, speed):
        """방향 d 로 한 틱만큼. 막히면 축을 하나씩 떼어 미끄러진다.

           도스 RPG 의 조작감은 이 '미끄러짐'에서 온다. 벽에 비스듬히 부딪혔을 때
           딱 멈추면 답답하고, 벽을 타고 흐르면 자연스럽다.
        """
        s = speed
        dx = P.DIRX[d] * s
        dy = P.DIRY[d] * s
        if P.DIAG[d]:
            dx = fp_mul(dx, DIAG_FACTOR)
            dy = fp_mul(dy, DIAG_FACTOR)
        nfx = e.fx + dx
        nfy = e.fy + dy
        moved = False
        if self.can_stand(e, nfx, nfy):
            e.fx, e.fy = nfx, nfy
            moved = True
        elif dx and self.can_stand(e, nfx, e.fy):
            e.fx = nfx
            moved = True
        elif dy and self.can_stand(e, e.fx, nfy):
            e.fy = nfy
            moved = True
        e.dirn = d
        tx, ty = e.tile()
        e.h = self.map.height(tx, ty)
        if moved:
            e.anim += 1
        return moved

    # ------------------------------------------------------------ 전투
    def adjacent(self, a, b):
        ax, ay = a.tile()
        bx, by = b.tile()
        dx = ax - bx
        dy = ay - by
        return -1 <= dx <= 1 and -1 <= dy <= 1

    def do_attack(self, a, b):
        hit, dmg, _d20 = DICE.attack(self.rng, a.atk, b.dfn, 1, 6, a.atk, b.armor)
        if not hit:
            return False
        b.hp -= dmg
        if b.hp <= 0:
            b.hp = 0
            b.alive = 0
            if a.kind == K_PLAYER:
                a.xp += 20 + 5 * b.maxhp
                while a.xp >= DICE.xp_to_next(a.lv):
                    a.xp -= DICE.xp_to_next(a.lv)
                    a.lv += 1
                    a.maxhp += 4 + self.rng.next() % 5
                    a.hp = a.maxhp
                    a.atk += 1
                    if a.lv % 2 == 0:
                        a.dfn += 1
        return True

    # ------------------------------------------------------------ 한 틱
    def tick(self):
        """SPEC §12.2 의 순서를 그대로. 순서가 곧 명세다."""
        p = self.ents[0]
        # 1~2. 입력과 플레이어 이동
        if self.in_dir >= 0:
            self.move_entity(p, self.in_dir, SPEED)
        # 3. 몬스터
        ptx, pty = p.tile()
        for e in self.ents:
            if e.kind != K_MON or not e.alive:
                continue
            etx, ety = e.tile()
            dx = etx - ptx
            dy = ety - pty
            near = (-AGGRO_R <= dx <= AGGRO_R and -AGGRO_R <= dy <= AGGRO_R)
            if not (near and LOS.visible(self.map, etx, ety, ptx, pty)):
                e.path = None
                continue
            if self.adjacent(e, p):
                if e.cool <= 0:
                    self.do_attack(e, p)
                    e.cool = ATTACK_EVERY
                else:
                    e.cool -= 1
                continue
            if e.cool > 0:
                e.cool -= 1
            if e.path is None or self.tick_n % PATH_EVERY == 0:
                got = P.astar(self.map, etx, ety, ptx, pty)
                e.path = got[0]
            if e.path and len(e.path) > 1:
                nx, ny = e.path[1]
                d = -1
                for k in range(8):
                    if P.DIRX[k] == nx - etx and P.DIRY[k] == ny - ety:
                        d = k
                        break
                if d >= 0:
                    self.move_entity(e, d, MON_SPEED)
                    if e.tile() == (nx, ny):
                        e.path = e.path[1:]
        # 4. 플레이어 명령
        if self.in_atk:
            for e in self.ents:
                if e.kind == K_MON and e.alive and self.adjacent(p, e):
                    self.do_attack(p, e)
                    break
        if self.in_act:
            for e in self.ents:
                if e.kind == K_CHEST and e.alive and self.adjacent(p, e):
                    e.alive = 0
                    p.xp += 30
                    while p.xp >= DICE.xp_to_next(p.lv):
                        p.xp -= DICE.xp_to_next(p.lv)
                        p.lv += 1
                        p.maxhp += 4 + self.rng.next() % 5
                        p.hp = p.maxhp
                        p.atk += 1
                        if p.lv % 2 == 0:
                            p.dfn += 1
                    break
        # 5. 안개와 조명
        self.fog.update(self.map, ptx, pty)
        # 6. 카메라
        sx, sy = PR.world_to_screen(p.fx, p.fy, p.h)
        self.cam_x, self.cam_y = CAM.follow(self.cam_x, self.cam_y, sx, sy)
        # 7. 틱
        self.tick_n += 1
        self.pal_phase = self.tick_n // 4

    # ------------------------------------------------------------ 트레이스
    def trace_line(self):
        p = self.ents[0]
        mon = sum(1 for e in self.ents if e.kind == K_MON and e.alive)
        # 세이브 끝에 붙은 CRC 를 그대로 읽는다. 세이브 전체를 다시 crc16 하면
        # 언제나 0이 나온다 — CCITT-FALSE 의 성질이라 값으로는 쓸모가 없다.
        blob = SV.pack_state(self)
        crc = blob[-2] * 256 + blob[-1]
        return ('{"t":%d,"px":%d,"py":%d,"ph":%d,"hp":%d,"lv":%d,"xp":%d,'
                '"rng":%d,"cam":[%d,%d],"seen":%d,"vis":%d,"mon":%d,"crc":%d}'
                % (self.tick_n, p.fx, p.fy, p.h, p.hp, p.lv, p.xp, self.rng.s,
                   self.cam_x, self.cam_y, self.fog.count_seen(),
                   self.fog.count_visible(), mon, crc))

    def run_script(self, path=None, emit=None, limit=None):
        """골든 시나리오를 돌린다. emit 이 있으면 매 틱 한 줄씩 넘긴다.

           limit 을 주면 그만큼 '진행한 틱' 뒤에 멈춘다. tick_n 이 아니라
           실제로 돌린 횟수다 — load 가 시계를 되돌리기 때문이다.
        """
        done = 0
        text = io.open(path or os.path.join(GOLDEN, 'script.txt'),
                       encoding='utf-8').read()
        for raw in text.split('\n'):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            p = line.split()
            cmd = p[0]
            if cmd == 'mark':
                if emit:
                    emit('{"mark":"%s","t":%d}' % (p[1], self.tick_n))
                continue
            if cmd == 'save':
                self.slot = SV.pack_state(self)
                continue
            if cmd == 'load':
                if self.slot is not None:
                    SV.unpack_state(self.slot, self)
                continue
            if cmd == 'hold':
                d = P.DIR_NAME.index(p[1])
                n = int(p[2])
                self.in_dir, self.in_act, self.in_atk = d, 0, 0
            elif cmd == 'wait':
                n = int(p[1])
                self.in_dir, self.in_act, self.in_atk = -1, 0, 0
            elif cmd == 'act':
                n = 1
                self.in_dir, self.in_act, self.in_atk = -1, 1, 0
            elif cmd == 'atk':
                n = 1
                self.in_dir, self.in_act, self.in_atk = -1, 0, 1
            else:
                raise ValueError('모르는 명령: %r' % cmd)
            for _ in range(n):
                self.tick()
                done += 1
                if emit:
                    emit(self.trace_line())
                if limit is not None and done >= limit:
                    self.in_dir, self.in_act, self.in_atk = -1, 0, 0
                    return self
        self.in_dir, self.in_act, self.in_atk = -1, 0, 0
        return self

    # ------------------------------------------------------------ 렌더
    def sprites(self):
        if self._sprites is None:
            self._sprites = RA.load_sprites()
        return self._sprites

    def _boxes(self):
        """정렬에 넣을 상자들. 지형 기둥과 물체를 한 통에 넣는다.

           지형을 빼고 물체끼리만 정렬하면 절벽 뒤에 선 캐릭터가 절벽 위로 뜬다.
           도스 시절 게임들이 실제로 겪던 문제고, 여기서는 같이 정렬해 없앤다.
        """
        m = self.map
        tx0, ty0, tx1, ty1 = PR.visible_range(
            self.cam_x, self.cam_y, self.cam_x + PR.SCR_W, self.cam_y + PR.SCR_H)
        boxes = []
        kinds = []
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                h = m.height(tx, ty)
                boxes.append((len(boxes), tx, ty, 0, tx + 1, ty + 1, h + 1))
                kinds.append(('tile', tx, ty))
        for e in self.ents:
            if not e.alive and e.kind == K_MON:
                continue
            tx, ty = e.tile()
            if not (tx0 <= tx <= tx1 and ty0 <= ty <= ty1):
                continue
            boxes.append((len(boxes), tx, ty, e.h, tx + 1, ty + 1, e.h + 3))
            kinds.append(('ent', e, 0))
        # 장식: 숲에는 나무, 바위 지형에는 바위. 배치는 좌표만으로 정해 결정적이다.
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                t = m.terrain(tx, ty)
                h = m.height(tx, ty)
                if t == M.T_FOREST and (tx * 7 + ty * 13) % 5 == 0:
                    boxes.append((len(boxes), tx, ty, h, tx + 1, ty + 1, h + 4))
                    kinds.append(('spr', 46, (tx, ty, h)))
                elif t == M.T_ROCK and (tx * 11 + ty * 5) % 7 == 0:
                    boxes.append((len(boxes), tx, ty, h, tx + 1, ty + 1, h + 2))
                    kinds.append(('spr', 47, (tx, ty, h)))
        return boxes, kinds

    def render(self):
        """한 프레임. 정렬 결과대로 지형 기둥과 물체를 차례로 올린다."""
        spr = self.sprites()
        f = self._frame
        if f is None:
            f = self._frame = RA.Frame()
        f.clear(0)
        m = self.map
        boxes, kinds = self._boxes()
        order, breaks = SD.topo_sort(boxes)
        self.cycle_breaks += breaks
        ptx, pty = self.ents[0].tile()
        for bid in order:
            kind = kinds[bid]
            if kind[0] == 'tile':
                tx, ty = kind[1], kind[2]
                lv = self.fog.light_of(tx, ty, ptx, pty)
                if lv == 0:
                    continue
                t = m.terrain(tx, ty)
                h = m.height(tx, ty)
                if h == 0:
                    sx, sy = PR.tile_to_screen(tx, ty, 0)
                    f.blit_rle(spr[t], sx - self.cam_x, sy - self.cam_y, lv)
                else:
                    for k in range(1, h + 1):
                        sx, sy = PR.tile_to_screen(tx, ty, k)
                        f.blit_rle(spr[16 + t], sx - self.cam_x, sy - self.cam_y, lv)
            elif kind[0] == 'ent':
                e = kind[1]
                tx, ty = e.tile()
                lv = self.fog.light_of(tx, ty, ptx, pty)
                if lv == 0:
                    continue
                sx, sy = PR.world_to_screen(e.fx, e.fy, e.h)
                sy += PR.HH
                if e.kind == K_PLAYER:
                    sid = 32 + SPRDIR[e.dirn] * 2 + (e.anim // 4) % 2
                elif e.kind == K_MON:
                    sid = 40 + (self.tick_n // 6 + e.eid) % 2
                elif e.kind == K_CHEST:
                    sid = 42 if e.alive else 43
                else:
                    sid = 44 + e.eid % 2
                f.blit_rle(spr[sid], sx - self.cam_x, sy - self.cam_y, lv)
            else:
                sid = kind[1]
                tx, ty, h = kind[2]
                lv = self.fog.light_of(tx, ty, ptx, pty)
                if lv == 0:
                    continue
                sx, sy = PR.tile_to_screen(tx, ty, h)
                f.blit_rle(spr[sid], sx - self.cam_x, sy + PR.HH - self.cam_y, lv)
        return f.fb

    def render_ppm(self):
        pal = RA.cycle_palette(RA.load_palette(), self.pal_phase)
        return RA.to_ppm(self.render(), pal)


def run_script_trace(path=None):
    g = Game()
    out = []
    g.run_script(path, out.append)
    return '\n'.join(out) + '\n'
