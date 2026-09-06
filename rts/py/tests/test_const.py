# -*- coding: utf-8 -*-
"""상수표와 유닛·건물표 (SPEC §0, §25).

   이 시험만 SPEC.md 를 **직접 읽어** 표와 코드를 대조한다. 손으로 옮겨 적은
   숫자는 반드시 언젠가 한 자리가 틀리고, 그 한 자리는 1200틱 뒤 해시 불일치로만
   드러난다. 루아·타입스크립트 쪽은 마크다운을 파싱하는 대신 `make parity` 의
   prim/trace/hashes 비교로 같은 숫자를 쓰는지 확인한다.
"""
from __future__ import print_function

import io
import os

import harness as H
from rts import const as C

H.title('const')

SPEC = io.open(os.path.join(os.path.dirname(H.GOLDEN), 'SPEC.md'),
               encoding='utf-8').read().split('\n')


def table_rows(header_line):
    """지정한 절 제목 뒤 첫 마크다운 표의 데이터 행을 셀 목록으로 돌려준다."""
    i = SPEC.index(header_line)
    while not SPEC[i].startswith('|'):
        i += 1
    i += 2                                  # 머리글과 구분선을 건너뛴다
    out = []
    while i < len(SPEC) and SPEC[i].startswith('|'):
        out.append([c.strip() for c in SPEC[i].strip('|').split('|')])
        i += 1
    return out


def num(s):
    s = s.split('(')[0].strip().replace('`', '')
    if s in ('—', '-', ''):
        return 0
    return int(s, 0)


# ── §0 상수표 ───────────────────────────────────────────────────────────────
bad = 0
n = 0
for cells in table_rows('## 0. 상수'):
    name = cells[0].replace('`', '').replace('\\', '')
    if not hasattr(C, name):
        H.note('%s 가 const 에 없다', name)
        bad += 1
        continue
    n += 1
    if getattr(C, name) != num(cells[1]):
        H.note('%s 기대 %s 실제 %r', name, cells[1], getattr(C, name))
        bad += 1
H.check('§0 상수 %d개가 표와 같다' % n, bad, 0)

# ── §25.1 유닛표 ────────────────────────────────────────────────────────────
COLS = ('HP', 'BASIC', 'PIERCE', 'ARMOUR', 'RANGE', 'RELOAD',
        'SPEED', 'SIGHT', 'COST', 'BUILD_TICKS', 'POP')
bad = 0
kinds = []
for cells in table_rows('### 25.1 유닛'):
    k = int(cells[0])
    kinds.append(k)
    short = cells[1].split('`')[1]
    if getattr(C, short, None) != k:
        H.note('%s 번호 기대 %d 실제 %r', short, k, getattr(C, short, None))
        bad += 1
    for j, col in enumerate(COLS):
        got = getattr(C, col)[k]
        if got != num(cells[2 + j]):
            H.note('%s.%s 기대 %s 실제 %r', short, col, cells[2 + j], got)
            bad += 1
    if C.NAME[k] != cells[1].split('`')[0].strip():
        bad += 1
    if C.FOOT[k] != 1 or C.IS_BUILDING[k] != 0:
        bad += 1
H.check('§25.1 유닛 %d종 × %d칸' % (len(kinds), len(COLS) + 3), bad, 0)
H.check('유닛 번호는 0..4', kinds, [0, 1, 2, 3, 4])

# ── §25.2 건물표 ────────────────────────────────────────────────────────────
BCOLS = ('HP', 'ARMOUR', 'SIGHT', 'COST', 'BUILD_TICKS', 'POP')
bad = 0
bkinds = []
for cells in table_rows('### 25.2 건물'):
    k = int(cells[0])
    bkinds.append(k)
    short = cells[1].split('`')[1]
    if getattr(C, short, None) != k:
        bad += 1
    if C.FOOT[k] != int(cells[2].split('×')[0]):
        H.note('%s 발자국 기대 %s 실제 %d', short, cells[2], C.FOOT[k])
        bad += 1
    for j, col in enumerate(BCOLS):
        if getattr(C, col)[k] != num(cells[3 + j]):
            H.note('%s.%s 기대 %s 실제 %r', short, col, cells[3 + j],
                   getattr(C, col)[k])
            bad += 1
    if C.IS_BUILDING[k] != 1:
        bad += 1
H.check('§25.2 건물 %d종 × %d칸' % (len(bkinds), len(BCOLS) + 2), bad, 0)
H.check('건물 번호는 10..15', bkinds, [10, 11, 12, 13, 14, 15])

# 방어탑의 공격 수치는 비고 칸에만 있다 — 거기서도 읽어 온다
tower = [c for c in table_rows('### 25.2 건물') if c[0] == '15'][0][9]
vals = [int(''.join(ch for ch in part if ch.isdigit()))
        for part in tower.split('·')]
H.check('방어탑 기본·관통·사거리·재장전',
        [C.BASIC[C.TOWER], C.PIERCE[C.TOWER],
         C.RANGE[C.TOWER], C.RELOAD[C.TOWER]], vals)

# ── 표의 내부 정합성 ────────────────────────────────────────────────────────
H.check('빈 번호 5..9 는 전부 0', [C.HP[k] for k in range(5, 10)], [0] * 5)
H.check('표 길이는 16', [len(getattr(C, c)) for c in COLS + ('FOOT', 'NAME')],
        [16] * (len(COLS) + 2))
H.check('공격하지 않는 것은 채집기뿐', [k for k in range(16)
                                        if C.IS_BUILDING[k] == 0 and C.HP[k]
                                        and C.BASIC[k] == 0], [C.HARV])
H.check_true('사거리가 0 인 유닛은 공격력도 0',
             all(C.BASIC[k] == 0 for k in range(16) if C.RANGE[k] == 0 and C.HP[k]))
H.check_true('모든 유닛의 시야는 SIGHT_MAX 이하',
             all(C.SIGHT[k] <= C.SIGHT_MAX for k in range(16)))

# 이동 종류는 §25.1 아래 문단에만 있다 — 표가 아니라 산문이라 여기에 옮겨 적는다
H.check('차량은 전차와 채집기뿐 (SPEC §25.1)',
        [k for k in range(16) if C.MOVE_KIND[k] == 1], [C.TANK, C.HARV])
H.check('건물의 이동 종류는 0', [C.MOVE_KIND[k] for k in range(10, 16)], [0] * 6)

# ── §25.3 기술 트리 ─────────────────────────────────────────────────────────
H.check('HQ 는 선행 조건이 없다', C.PREREQ[C.HQ], [])
H.check('공장만 선행 조건이 둘', [k for k in range(16) if len(C.PREREQ[k]) > 1],
        [C.FACT])
H.check('공장의 선행은 발전소와 병영 (번호 오름차순)',
        C.PREREQ[C.FACT], [C.BARR, C.POW])
H.check('전차·박격포는 공장에서', [C.PREREQ[C.TANK], C.PREREQ[C.MORTAR]],
        [[C.FACT], [C.FACT]])
bad = 0
for k in range(16):
    for p in C.PREREQ[k]:
        if C.IS_BUILDING[p] != 1:
            bad += 1
H.check('선행 조건은 전부 건물', bad, 0)


def has_cycle():
    """DAG 확인 — 순환이 있으면 위상 정렬이 멈춘다 (§16.6)."""
    seen = [0] * 16

    def visit(k):
        if seen[k] == 1:
            return True
        if seen[k] == 2:
            return False
        seen[k] = 1
        for p in C.PREREQ[k]:
            if visit(p):
                return True
        seen[k] = 2
        return False

    return any(visit(k) for k in range(16))


H.check('기술 트리는 순환이 없다', has_cycle(), False)

# ── §25.4 시작 조건 ─────────────────────────────────────────────────────────
H.check('시작 크레딧 1000', C.START_CREDITS, 1000)
H.check('시작 채집기 2기', C.START_HARV, 2)
H.check('시나리오 길이 1200틱', C.SCENARIO_TICKS, 1200)

H.done()
