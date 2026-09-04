# -*- coding: utf-8 -*-
"""유닛 풀 — SPEC §3.

   도스 시절 유닛은 malloc 으로 잡지 않았다. 고정 크기 배열 하나를 잡고
   빈 칸을 프리 리스트로 이어 두는 것이 관례였다. 이유가 두 가지 있다.

     1. 세이브 파일이 배열 덤프 한 번으로 끝난다. 포인터를 쓰면 직렬화할 때
        전부 인덱스로 바꿔야 하는데, 그럴 바에는 처음부터 인덱스를 쓴다.
     2. 640KB 안에서 조각화가 나면 복구할 방법이 없다. 고정 풀은 조각이 안 난다.

   그래서 유닛을 가리키는 것은 언제나 '아이디(=배열 첨자)'이고, 죽은 유닛의
   아이디는 프리 리스트를 통해 재사용된다.
"""

MAX_UNITS = 64
NO_UNIT = -1

INF, TANK, ARTY, RECON = range(4)

#          key      이름     mp  atk def rng vis hpmax ammo  글자
KINDS = (
    ('INF',   '보병',   6,  4, 5, 1, 2, 10, 6, 'I'),
    ('TANK',  '전차',  12,  8, 6, 1, 2, 10, 6, 'T'),
    ('ARTY',  '포병',   6, 10, 2, 3, 2,  8, 5, 'A'),
    ('RECON', '정찰',  16,  3, 3, 1, 4, 10, 4, 'R'),
)
K_MP = tuple(k[2] for k in KINDS)
K_ATK = tuple(k[3] for k in KINDS)
K_DEF = tuple(k[4] for k in KINDS)
K_RNG = tuple(k[5] for k in KINDS)
K_VIS = tuple(k[6] for k in KINDS)
K_HP = tuple(k[7] for k in KINDS)
K_AMMO = tuple(k[8] for k in KINDS)
K_CHAR = tuple(k[9] for k in KINDS)


class Unit(object):
    """한 유닛의 전체 상태. __slots__ 로 dict 를 없앤다 — 파이썬판에서
       유일하게 '도스식 레코드'에 가까운 표현이다."""

    __slots__ = ('id', 'side', 'kind', 'q', 'r', 'hp', 'mp', 'ammo', 'ent', 'alive', 'moved')

    def __init__(self, uid, side, kind, q, r):
        self.id = uid
        self.side = side
        self.kind = kind
        self.q = q
        self.r = r
        self.hp = K_HP[kind]
        self.mp = K_MP[kind]
        self.ammo = K_AMMO[kind]
        self.ent = 0
        self.alive = True
        self.moved = False

    def serialize(self):
        """SPEC §12.1 의 정규 직렬화 — 골든 해시가 이 문자열을 먹는다."""
        return '%d,%d,%d,%d,%d,%d,%d,%d,%d\n' % (
            self.id, self.side, self.kind, self.q, self.r,
            self.hp, self.mp, self.ammo, self.ent)


class UnitPool(object):
    """고정 배열 + 프리 리스트. 살아 있는 유닛만 순회하는 iter_alive 를 쓴다."""

    __slots__ = ('slots', 'nextfree', 'freehead')

    def __init__(self, cap=MAX_UNITS):
        self.slots = [None] * cap
        self.nextfree = [-1] * cap
        self.freehead = -1

    def spawn(self, side, kind, q, r):
        """빈 칸을 프리 리스트에서 먼저 꺼내고, 없으면 뒤에서 늘린다."""
        if self.freehead >= 0:
            uid = self.freehead
            self.freehead = self.nextfree[uid]
        else:
            uid = -1
            for i, s in enumerate(self.slots):
                if s is None:
                    uid = i
                    break
            if uid < 0:
                raise RuntimeError('유닛 풀이 가득 찼다')
        self.slots[uid] = Unit(uid, side, kind, q, r)
        return uid

    def kill(self, uid):
        """죽은 자리는 즉시 프리 리스트에 넣는다. 아이디가 재사용되므로
           바깥에서 아이디를 오래 들고 있으면 안 된다 — 유령 참조의 고전."""
        u = self.slots[uid]
        if u is None:
            return
        u.alive = False
        self.slots[uid] = None
        self.nextfree[uid] = self.freehead
        self.freehead = uid

    def get(self, uid):
        return self.slots[uid] if 0 <= uid < len(self.slots) else None

    def iter_alive(self, side=None):
        for u in self.slots:
            if u is not None and (side is None or u.side == side):
                yield u

    def count(self, side=None):
        return sum(1 for _ in self.iter_alive(side))

    def serialize(self):
        return ''.join(u.serialize() for u in self.slots if u is not None)
