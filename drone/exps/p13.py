# -*- coding: utf-8 -*-
"""13부 — 드론쇼 트릭 모음. 트릭마다 약속 하나를 수로 잰다."""
import math
import os
import sys

from droneshow import collide
from droneshow import formation as F
from droneshow import params, rng
from droneshow import show as SH
from droneshow import tricks as TR
from droneshow.font5x7 import GLYPHS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ex'))
import shape_pgm as S  # noqa: E402

P = params.load()
DM = P['dmin']
D = DM * math.sqrt(2)                   # 모양 간격 — T31(16부)
WHITE, RED, BLUE = (255, 255, 255), (255, 40, 90), (80, 200, 255)


def one(name, pts, rgb=WHITE, hold=2.0):
    """장면 하나짜리 쇼 — 스냅숏(SHOW)용."""
    return SH.plan([{'name': name, 'points': pts, 'hold': hold,
                     'rgb': rgb}], P)


def extent(pts, k):
    return max(q[k] for q in pts) - min(q[k] for q in pts)


def nn_cv(pts):
    """가장 가까운 이웃 거리의 (평균, 변동 계수) — 고르기의 잣대."""
    nn = [min(math.dist(a, b) for b in pts if b is not a) for a in pts]
    m = sum(nn) / len(nn)
    sd = math.sqrt(sum((x - m) ** 2 for x in nn) / len(nn))
    return m, sd / m


def image(ctx):
    """이미지 → 점: 채운 하트는 폭이 √n 에 비례한다(16부의 윤곽선과)."""
    rows = []
    for n, grid in ((60, 40), (300, 60)):
        text = S.pgm(S.inside_heart, grid)
        for lloyd in (0, 10):
            pts = F.image(text, n, D, rng.Rng(3), lloyd=lloyd)
            m, cv = nn_cv(pts)
            dmin = collide.min_distance(pts)[0]
            rows.append(['%d' % n, '%d×%d' % (grid, grid), '%d' % lloyd,
                         '%.1f' % extent(pts, 0),
                         '%.1f' % extent(pts, 2),
                         '%.2f' % m, '%.3f' % cv, '%.3f' % dmin])
            if lloyd == 10:
                ctx.show('p13_img%d' % n, one('heart', pts, RED))
    head = ['대수', '그림 칸', '로이드', '폭[m]', '높이[m]',
            '이웃 평균[m]', '이웃 변동계수', '최소 간격[m]']
    ctx.table('p13_image', head, rows, num=(0, 2, 3, 4, 5, 6, 7))
    star = F.image(S.pgm(S.inside_star, 50), 100, D, rng.Rng(5))
    ctx.show('p13_star', one('star', star, (255, 220, 120)))
    ctx.text('p13_pgm_head', '$ python3 ex/shape_pgm.py heart 12\n'
             + S.pgm(S.inside_heart, 12))


def glyphs(ctx):
    """5×7 글꼴의 글자마다 점 수 — 글자는 점 예산을 먹는다."""
    rows = []
    for group in ('ABCDEFGHI', 'JKLMNOPQR', 'STUVWXYZ', '0123456789'):
        rows.append([group, ' '.join('%d' % F.glyph_count(c)
                                     for c in group)])
    words = ['SHOW', 'DRONE', 'TREASURE', 'KOREA', '2026']
    for w in words:
        rows.append([w, '%d' % len(F.text(w, D))])
    ctx.table('p13_glyphs', ['글자·낱말', '점 수'], rows)
    ctx.text('p13_glyph_a', 'A 의 5×7 칸 (# = 드론)\n'
             + '\n'.join(GLYPHS['A'].split()))


def dark(ctx):
    """불 끄고 이동 — 전환 한가운데의 모습만 달라진다."""
    s = SH.plan([{'name': 'heart', 'points': F.heart(60, D, 20.0),
                  'hold': 3.0, 'rgb': RED},
                 {'name': 'globe', 'points': F.globe(60, D, z0=20.0),
                  'hold': 3.0, 'rgb': BLUE}], P)
    ctx.show('p13_move', s)
    ctx.show('p13_dark', TR.dark_move(s, fade=0.3))
    sc = s['scenes']
    ctx.text('p13_dark_times', '하트 %.2f–%.2f초 · 지구본 '
             '%.2f–%.2f초 · 전환 한가운데 %.2f초'
             % (sc[0]['t0'], sc[0]['t1'], sc[1]['t0'], sc[1]['t1'],
                (sc[0]['t1'] + sc[1]['t0']) / 2))


def depth(ctx):
    """2.5-D — 체스판처럼 한 칸 걸러 뒤로 빼면 앞에서 본 간격을
    좁혀도 3차원 간격은 지킨다. 앞 간격 dmin·깊이 dmin 이면 3차원
    간격이 √2·dmin 이라 전환까지 안전하다(T31). 앞 간격 dmin/√2 는
    멈춘 모양만 dmin 을 지킨다."""
    rows = []
    for s in (DM, DM / math.sqrt(2)):           # 앞에서 본 간격
        base = F.text('DRONE', s, 20.0)
        for dep in (0.0, 0.5 * s, s):
            pts = TR.layered_depth(base, dep)
            flat = [[q[0], 0.0, q[2]] for q in pts]
            front = collide.min_distance(flat)[0]
            rows.append(['%.3f' % dep, '%.3f' % front,
                         '%.3f' % collide.min_distance(pts)[0],
                         '%.1f' % extent(pts, 0)])
    head = ['뒤로 뺀 깊이[m]', '앞에서 본 간격[m]',
            '3차원 최소 간격[m]', '글자 폭[m]']
    ctx.table('p13_depth', head, rows, num=(0, 1, 2, 3))
    wide = F.text('DRONE', D, 20.0)
    ctx.text('p13_depth_width', 'DRONE 폭 — 한 평면 간격 √2·dmin %.1f m'
             ' · 체스판(앞 간격 dmin) %.1f m'
             % (extent(wide, 0), extent(F.text('DRONE', DM, 20.0), 0)))
    safe = TR.layered_depth(F.text('DRONE', DM, 20.0), DM)
    ctx.show('p13_depth', one('DRONE', safe))


def rotate(ctx):
    """회전 볼륨 — 강체 회전은 모든 거리를 지킨다. 직선으로 잇는
    전환(현)은 안쪽으로 파고든다."""
    pts = F.sphere(80, D, z0=20.0)
    steps = TR.rotate_volume(pts, math.pi / 2, 6)
    rows = []
    for k, q in enumerate(steps):
        far = max(math.dist(c, TR.centroid(pts)) for c in q)
        rows.append(['%d' % (15 * k),
                     '%.4f' % collide.min_distance(q)[0], '%.4f' % far])
    head = ['회전[°]', '최소 간격[m]', '중심에서 가장 먼 점[m]']
    ctx.table('p13_rotate', head, rows, num=(0, 1, 2))
    # 같은 회전을 장면 두 개(0°, 90°)의 직선 전환으로 하면
    s = SH.plan([{'name': 'r0', 'points': steps[0], 'hold': 1.0,
                  'rgb': BLUE},
                 {'name': 'r90', 'points': steps[-1], 'hold': 1.0,
                  'rgb': BLUE}], P)
    dd, t, _i, _j = SH.min_distance(s)
    ctx.text('p13_rotate_chord', '0° → 90° 를 직선 전환 한 번으로: '
             '최소 간격 %.3f m (%.2f초) · 전환 %.2f초'
             % (dd, t, s['scenes'][1]['t0'] - s['scenes'][0]['t1']))


def wave(ctx):
    """파동 — 위아래 최고 속도 2π·A/T 가 v_max 를 넘으면 못 쓴다."""
    rows = []
    for amp, per in ((0.5, 4.0), (1.0, 6.0), (1.0, 4.0), (2.0, 6.0),
                     (2.0, 4.0)):
        v = 2 * math.pi * amp / per
        a = (2 * math.pi / per) ** 2 * amp
        rows.append(['%.1f' % amp, '%.1f' % per, '%.3f' % v, '%.3f' % a,
                     '예' if v <= P['vmax'] and a <= P['amax']
                     else '아니오'])
    ctx.table('p13_wave', ['진폭 A[m]', '주기 T[s]', '최고 속도[m/s]',
                           '최고 가속도[m/s²]', '한계 안'], rows,
              num=(0, 1, 2, 3))
    g = F.grid(60, D, z0=20.0)
    ctx.show('p13_wave0', one('w0', TR.wave(g, 1.0, 12.0, 6.0, 0.0)))
    ctx.show('p13_wave1', one('w1', TR.wave(g, 1.0, 12.0, 6.0, 1.5)))


def led(ctx):
    """빛만의 움직임 — 드론은 멈추고 밝은 띠가 흐른다."""
    s = one('grid', F.grid(60, D, z0=20.0), BLUE, hold=8.0)
    t = TR.led_only_motion(s, speed=2.0, width=2.0 * D, dim=0.25)
    ctx.show('p13_led', t)
    moved = max(math.dist(SH.position(t, d, 0.0),
                          SH.position(t, d, 8.0)) for d in t['drones'])
    ctx.text('p13_led_moved', '8초 동안 가장 많이 움직인 드론: %.3f m'
             % moved)


def dither(ctx):
    """밝기 네 단계로 16 대의 그러데이션 — 반올림 대 오차 확산."""
    vals = [k / 15 for k in range(16)]
    rq = [min(1.0, max(0.0, math.floor(v * 3 + 0.5) / 3)) for v in vals]
    dq = TR.dither(vals, 4)
    rows = [['%d' % k, '%.3f' % v, '%.3f' % a, '%.3f' % b]
            for k, (v, a, b) in enumerate(zip(vals, rq, dq))]
    head = ['드론', '원하는 값', '반올림', '오차 확산']
    ctx.table('p13_dither', head, rows, num=(0, 1, 2, 3))
    # 이웃 w 대를 묶어 본 평균이 원하는 평균에서 벗어난 정도 —
    # 창을 한 칸씩 밀며 잰 절댓값의 평균
    def err(q, w):
        k = range(len(vals) - w + 1)
        return sum(abs(sum(q[i:i + w]) - sum(vals[i:i + w])) / w
                   for i in k) / len(k)
    lines = ['묶음 크기  반올림 오차  오차 확산 오차']
    for w in (2, 3, 4, 8):
        lines.append('  %2d 대     %.4f      %.4f'
                     % (w, err(rq, w), err(dq, w)))
    ctx.text('p13_dither_mean', '\n'.join(lines))


def takeoff(ctx):
    """이륙 — 땅 격자 간격과 엇갈림(delay)에 따라 최소 간격과
    다운워시 노출(위아래로 겹친 쌍 × 초)."""
    s = one('heart', F.heart(60, D, 20.0), RED, hold=3.0)
    rows = []
    for gs, gname in ((DM, 'dmin'), (D, '√2·dmin')):
        g = F.grid(60, gs, plane='xy')
        for delay in (0.0, 0.5, 1.0):
            x = TR.takeoff(s, g, P, delay)
            t1 = x['takeoff']['t1']
            mind = min(collide.min_distance(
                [SH.position(x, d, k * 0.04) for d in x['drones']])[0]
                for k in range(int(t1 / 0.04) + 1))
            expo = 0.1 * sum(TR.under_count(
                [SH.position(x, d, k * 0.1) for d in x['drones']],
                DM, 10.0) for k in range(int(t1 / 0.1) + 1))
            rows.append([gname, '%.1f' % delay, '%.2f' % t1,
                         '%.3f' % mind, '%.1f' % expo])
            if gs == D and delay == 1.0:
                ctx.show('p13_takeoff', x)
    head = ['땅 격자 간격', '엇갈림[s]', '이륙 시간[s]', '최소 간격[m]',
            '다운워시 노출[쌍·s]']
    ctx.table('p13_takeoff', head, rows, num=(1, 2, 3, 4))


def run(ctx):
    image(ctx)
    glyphs(ctx)
    dark(ctx)
    depth(ctx)
    rotate(ctx)
    wave(ctx)
    led(ctx)
    dither(ctx)
    takeoff(ctx)
