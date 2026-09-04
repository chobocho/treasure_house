# -*- coding: utf-8 -*-
"""게임 상태와 명령 — SPEC §8, §11.3.

   모든 상태 변화가 '명령 레코드' 하나를 거친다. 도스 워게임이 언두를 지원한
   방식이 정확히 이것이었다. 스냅샷을 통째로 뜨기에는 640KB 가 너무 좁았고,
   그래서 '되돌리는 데 꼭 필요한 필드만' 명령에 적어 두었다.

   되돌릴 때 난수 상태도 같이 되돌린다는 점이 중요하다. 그러지 않으면 공격을
   무르고 다시 하면 주사위가 달라져, 플레이어가 언두로 주사위를 굴릴 수 있다.
"""

from . import hexcoord as H
from . import los
from . import path as P
from .combat import can_attack, resolve
from .hexmap import FOG_VISIBLE
from .rng import Rng
from .units import K_MP, K_HP, NO_UNIT

MOVE, ATTACK, ENDTURN = 0, 1, 2
MAX_TURN = 20


class Command(object):
    """되돌리기에 필요한 최소 정보만 담는다. path 는 화면 재생용."""

    __slots__ = ('kind', 'unit', 'frm', 'to', 'path', 'mp', 'ent', 'moved',
                 'target', 'thp', 'tammo', 'ahp', 'aammo', 'amp', 'rng_state',
                 'killed', 'log', 'alog')

    def __init__(self, kind):
        self.kind = kind
        self.unit = -1
        self.frm = self.to = -1
        self.path = []
        self.mp = self.ent = 0
        self.moved = False
        self.target = -1
        self.thp = self.tammo = 0
        self.ahp = self.aammo = self.amp = 0
        self.rng_state = 0
        self.killed = []
        self.log = ''          # 사람이 읽는 한국어 기록
        self.alog = ''         # 화면 메시지 줄용 ASCII (5x7 글꼴이 한글을 못 찍는다)


class Game(object):
    __slots__ = ('map', 'pool', 'objectives', 'rng', 'turn', 'side',
                 'undo_stack', 'log', 'over', 'winner')

    def __init__(self, m, pool, objectives, seed=0x1BADB002):
        self.map = m
        self.pool = pool
        self.objectives = objectives
        self.rng = Rng(seed)
        self.turn = 1
        self.side = 0
        self.undo_stack = []
        self.log = []
        self.over = False
        self.winner = -1
        los.update_fog(self.map, self.pool, 0)

    # ------------------------------------------------------------------ 이동
    def move_unit(self, uid, target_idx):
        """target_idx 까지 이동. 성공하면 Command, 실패하면 None."""
        u = self.pool.get(uid)
        if u is None or u.side != self.side or self.over:
            return None
        reach = P.reachable(self.map, self.pool, u)
        if not reach.has(target_idx) or target_idx == self.map.axial_idx(u.q, u.r):
            return None

        cmd = Command(MOVE)
        cmd.unit = uid
        cmd.frm = self.map.axial_idx(u.q, u.r)
        cmd.to = target_idx
        cmd.path = P.trace_path(self.map, reach, target_idx)
        cmd.mp = u.mp
        cmd.ent = u.ent
        cmd.moved = u.moved

        cost = reach.cost[target_idx]
        self.map.occupant[cmd.frm] = NO_UNIT
        self.map.occupant[target_idx] = uid
        u.q, u.r = self.map.idx_axial(target_idx)
        u.mp = u.mp - cost
        # ZOC 안으로 들어갔으면 남은 이동력을 버린다 (SPEC §6.2)
        zoc = P.zoc_mask(self.map, self.pool, u.side)
        if zoc[target_idx]:
            u.mp = 0
        u.ent = 0                       # 움직이면 참호가 풀린다
        u.moved = True
        cmd.log = '%s 이동 %d칸' % (self._name(u), len(cmd.path) - 1)
        cmd.alog = 'MOVE U%d %d STEP' % (uid, len(cmd.path) - 1)
        self._after_command(cmd)
        return cmd

    # ------------------------------------------------------------------ 공격
    def attack(self, uid, target_uid):
        u = self.pool.get(uid)
        t = self.pool.get(target_uid)
        if u is None or t is None or u.side != self.side or self.over:
            return None
        if not can_attack(self.map, self.pool, u, t):
            return None

        cmd = Command(ATTACK)
        cmd.unit = uid
        cmd.target = target_uid
        cmd.frm = self.map.axial_idx(u.q, u.r)
        cmd.mp, cmd.ent, cmd.moved = u.mp, u.ent, u.moved
        cmd.ahp, cmd.aammo, cmd.amp = u.hp, u.ammo, u.mp
        cmd.thp, cmd.tammo = t.hp, t.ammo
        cmd.rng_state = self.rng.save()      # 언두가 주사위까지 되돌린다

        al, dl, roll, score = resolve(self.map, self.pool, self.rng, u, t)
        cmd.log = '%s → %s  2d6=%d 점수%+d  피해 %d/%d' % (
            self._name(u), self._name(t), roll, score, dl, al)
        cmd.alog = 'ATK U%d>U%d ROLL %d DMG %d/%d' % (uid, target_uid, roll, dl, al)

        for x in (t, u):
            if x.hp <= 0:
                i = self.map.axial_idx(x.q, x.r)
                if i >= 0 and self.map.occupant[i] == x.id:
                    self.map.occupant[i] = NO_UNIT
                cmd.killed.append((x.id, x.side, x.kind, x.q, x.r))
                self.pool.kill(x.id)
        self._after_command(cmd)
        return cmd

    # ------------------------------------------------------------------- 턴
    def end_turn(self):
        cmd = Command(ENDTURN)
        cmd.log = '%d턴 %s 종료' % (self.turn, '청군' if self.side == 0 else '적군')
        cmd.alog = 'END TURN %d SIDE %d' % (self.turn, self.side)
        self.undo_stack = []            # 턴이 넘어가면 언두 이력은 버린다
        self._check_victory_on_end()
        if self.over:
            self.log.append((cmd.log, cmd.alog))
            return cmd
        self.side = 1 - self.side
        if self.side == 0:
            self.turn += 1
            if self.turn > MAX_TURN:
                self.over = True
                self.winner = -1
        for u in self.pool.iter_alive(self.side):
            if not u.moved:
                u.ent = min(3, u.ent + 1)     # 가만히 있으면 참호를 판다
            u.mp = K_MP[u.kind]
            u.moved = False
        los.update_fog(self.map, self.pool, 0)
        self.log.append((cmd.log, cmd.alog))
        return cmd

    def _check_victory_on_end(self):
        if self.pool.count(1) == 0:
            self.over, self.winner = True, 0
        elif self.pool.count(0) == 0:
            self.over, self.winner = True, 1
        elif self.side == 0:
            held = 0
            for q, r in self.objectives:
                i = self.map.axial_idx(q, r)
                uid = self.map.occupant[i] if i >= 0 else NO_UNIT
                if uid != NO_UNIT and self.pool.get(uid) and self.pool.get(uid).side == 0:
                    held += 1
            if held == len(self.objectives):
                self.over, self.winner = True, 0

    # ------------------------------------------------------------------ 언두
    def undo(self):
        """가장 최근 명령을 되돌린다. 안개는 복원하지 않고 다시 계산한다 —
           저장 비용보다 재계산이 싸고, 무엇보다 틀릴 여지가 없다."""
        if not self.undo_stack:
            return False
        cmd = self.undo_stack.pop()
        if cmd.kind == MOVE:
            u = self.pool.get(cmd.unit)
            self.map.occupant[cmd.to] = NO_UNIT
            self.map.occupant[cmd.frm] = cmd.unit
            u.q, u.r = self.map.idx_axial(cmd.frm)
            u.mp, u.ent, u.moved = cmd.mp, cmd.ent, cmd.moved
        elif cmd.kind == ATTACK:
            # 죽은 유닛을 같은 아이디로 되살린다. 프리 리스트가 방금 그 자리를
            # 내줬으므로 아이디가 재사용되기 전이면 안전하다.
            for (uid, side, kind, q, r) in cmd.killed:
                self.pool.slots[uid] = None
                self._revive(uid, side, kind, q, r)
            u = self.pool.get(cmd.unit)
            t = self.pool.get(cmd.target)
            u.hp, u.ammo, u.mp, u.ent, u.moved = cmd.ahp, cmd.aammo, cmd.amp, cmd.ent, cmd.moved
            t.hp, t.ammo = cmd.thp, cmd.tammo
            self.rng.restore(cmd.rng_state)
        else:
            return False
        los.update_fog(self.map, self.pool, 0)
        if self.log:
            self.log.pop()
        return True

    def _revive(self, uid, side, kind, q, r):
        from .units import Unit
        u = Unit(uid, side, kind, q, r)
        self.pool.slots[uid] = u
        # 프리 리스트에서 이 아이디를 빼낸다
        if self.pool.freehead == uid:
            self.pool.freehead = self.pool.nextfree[uid]
        else:
            prev = self.pool.freehead
            while prev >= 0 and self.pool.nextfree[prev] != uid:
                prev = self.pool.nextfree[prev]
            if prev >= 0:
                self.pool.nextfree[prev] = self.pool.nextfree[uid]
        i = self.map.axial_idx(q, r)
        if i >= 0:
            self.map.occupant[i] = uid

    # ---------------------------------------------------------------- 공통
    def _after_command(self, cmd):
        self.undo_stack.append(cmd)
        self.log.append((cmd.log, cmd.alog))
        los.update_fog(self.map, self.pool, 0)
        self.assert_consistent()

    def _name(self, u):
        from .units import KINDS
        return '%s%d' % (KINDS[u.kind][1], u.id)

    def assert_consistent(self):
        """occupant 배열과 유닛 좌표가 어긋나면 즉시 잡는다. 도스 시절의
           고전적 버그가 '유닛은 옮겼는데 맵의 점유 표시를 안 지운 것' 이다."""
        seen = {}
        for u in self.pool.iter_alive():
            i = self.map.axial_idx(u.q, u.r)
            assert i >= 0, '유닛 %d 가 맵 밖에 있다' % u.id
            assert self.map.occupant[i] == u.id, \
                'occupant[%d]=%d 인데 유닛 %d 가 거기 있다' % (i, self.map.occupant[i], u.id)
            assert i not in seen, '%d 칸에 유닛 둘' % i
            seen[i] = u.id
        for i, uid in enumerate(self.map.occupant):
            if uid != NO_UNIT:
                assert self.pool.get(uid) is not None, 'occupant[%d] 가 죽은 유닛' % i

    def serialize_units(self):
        return self.pool.serialize()
