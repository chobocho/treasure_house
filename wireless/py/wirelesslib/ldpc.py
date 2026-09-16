# -*- coding: utf-8 -*-
"""ldpc — 저밀도 패리티 검사 부호와 믿음 전파.

   갤러거가 1962년에 낸 부호다. 당시 기계로는 복호가 불가능해 삼십 년
   넘게 잊혔다가, 터보 부호가 반복 복호의 값어치를 보인 뒤에야
   되살아났다. 지금은 5G NR 의 데이터 채널이 이것을 쓴다.

   **이 파일의 부호는 NR 의 BG1·BG2 가 아니다.** NR 의 기저 행렬은
   42×52 · 46×68 짜리 표라 여기에 옮겨 적을 수 없고, 옮겨 적으면
   "검증하지 않은 숫자" 가 된다. 대신 NR 과 **같은 꼴** 의 작은
   부호를 짜서 원리를 보인다.

     · 준순환(QC) 구조 — 기저 행렬의 칸마다 z×z 순환 이동 행렬
     · 계단(누산) 패리티 — 앞먹임 한 번으로 부호화가 끝난다(O(n))
     · 4-순환 없음 — 있으면 믿음 전파가 제 말을 되돌려 듣는다

   NR 의 실제 기저 행렬과 리프팅 집합은 덱 본문에서 TS 38.212 §5.3.2 를
   인용해 다룬다. 여기서 돌아가는 것은 그 구조를 축소한 모형이다.
"""
import math
import random


class Base(object):
    """기저 행렬. rows[r] 는 [(열, 이동량), …] 다."""

    def __init__(self, rows, nb, kb):
        self.rows = rows
        self.nb = nb
        self.kb = kb
        self.mb = len(rows)


def _build_base(kb=10, mb=14, ninfo=4, zmax=16, seed=20260916):
    """기저 행렬을 규칙으로 짓는다 — 마법의 표를 손으로 적지 않는다.

    패리티 쪽은 계단(이중 대각선)이라 부호화가 앞먹임 한 번이면 끝나고,
    정보 쪽은 씨앗을 고정한 난수로 고르되 4-순환이 생기는 선택을
    물리치며 넣는다. 같은 씨앗이면 언제나 같은 행렬이 나온다.
    """
    rnd = random.Random(seed)
    rows = [[] for _ in range(mb)]
    pairs = set()          # (열a, 열b, 이동차) — 4-순환을 막는 열쇠

    def key_of(c0, s0, col, shift):
        if c0 < col:
            return (c0, col, (shift - s0) % zmax)
        return (col, c0, (s0 - shift) % zmax)

    def ok(r, col, shift):
        for c0, s0 in rows[r]:
            if key_of(c0, s0, col, shift) in pairs:
                return False
        return True

    def commit(r, col, shift):
        for c0, s0 in rows[r]:
            pairs.add(key_of(c0, s0, col, shift))
        rows[r].append((col, shift))

    for r in range(mb):
        # 정보 열 ninfo 개
        cols = rnd.sample(range(kb), ninfo)
        for c in sorted(cols):
            for _try in range(200):
                sh = rnd.randrange(zmax)
                if ok(r, c, sh):
                    commit(r, c, sh)
                    break
            else:
                raise RuntimeError('이동량을 못 골랐다')
        # 패리티 계단: 이 행의 새 패리티 열과 바로 앞 패리티 열
        if r > 0:
            commit(r, kb + r - 1, 0)
        commit(r, kb + r, 0)
    return Base(rows, kb + mb, kb)


NR_LIKE = _build_base()


class Graph(object):
    """리프팅이 끝난 탄너 그래프.

    rows[c] 는 c번 검사가 보는 변수들의 번호다.
    """

    def __init__(self, rows, n, m, z, base):
        self.rows = rows
        self.n = n
        self.m = m
        self.k = n - m
        self.z = z
        self.base = base
        self.cols = [[] for _ in range(n)]
        for ci, vs in enumerate(rows):
            for v in vs:
                self.cols[v].append(ci)


def lift(base, z):
    """기저 행렬을 z 배로 부풀린다. 칸 (r,c,s) → z×z 순환 이동 행렬."""
    rows = []
    for r in range(base.mb):
        for i in range(z):
            vs = [c * z + ((i + s) % z) for c, s in base.rows[r]]
            rows.append(vs)
    return Graph(rows, base.nb * z, base.mb * z, z, base)


def count_four_cycles(h):
    """두 검사가 변수 둘을 함께 보는 자리의 수.

    4-순환이 있으면 믿음 전파가 두 걸음 만에 자기가 보낸 말을 되돌려
    듣는다. 그러면 '독립인 소식' 이라는 전제가 깨져 복호가 일찍 멈춘다.
    시간 O(Σ d_c²).
    """
    seen = {}
    cnt = 0
    for ci, vs in enumerate(h.rows):
        vs = sorted(vs)
        for a in range(len(vs)):
            for b in range(a + 1, len(vs)):
                key = (vs[a], vs[b])
                if key in seen and seen[key] != ci:
                    cnt += 1
                else:
                    seen[key] = ci
    return cnt


def syndrome_is_zero(h, bits):
    """모든 검사식이 만족되는가 — H·c = 0."""
    for vs in h.rows:
        s = 0
        for v in vs:
            s ^= bits[v]
        if s:
            return False
    return True


class Encoder(object):
    """계단 구조를 이용한 앞먹임 부호기.

    패리티 열이 이중 대각선이라 검사식을 위에서 아래로 한 번 훑으면
    패리티가 하나씩 정해진다. 행렬을 뒤집을 필요가 없다 — 실물
    LDPC 부호기가 O(n) 인 까닭이 바로 이 구조다.
    """

    def __init__(self, h):
        self.h = h

    def encode(self, msg):
        h = self.h
        if len(msg) != h.k:
            raise ValueError('메시지는 %d 비트다: %d' % (h.k, len(msg)))
        cw = list(msg) + [0] * h.m
        z, kb = h.z, h.base.kb
        for r in range(h.base.mb):
            for i in range(z):
                ci = r * z + i
                s = 0
                for v in h.rows[ci]:
                    if v < (kb + r) * z:      # 아직 안 정한 열은 빼고
                        s ^= cw[v]
                cw[(kb + r) * z + i] = s
        return cw


# ── 믿음 전파 ─────────────────────────────────────────────────────

_CLAMP = 1.0 - 1e-12


def _check_msg(vals, minsum, alpha=0.75):
    """한 검사가 이웃들에게 보낼 말. vals 는 들어온 말들이다.

    합곱은 tanh 규칙, 최소합은 '부호는 곱, 크기는 최소' 다. 최소합은
    크기를 늘 크게 잡는 쪽으로 틀리므로 보통 0.7~0.8 을 곱해 눌러 준다.
    시간 O(d²) — d 가 6 안팎이라 이 책에서는 이 쪽이 읽기 좋다.
    """
    d = len(vals)
    out = [0.0] * d
    for i in range(d):
        if minsum:
            sgn = 1.0
            mag = float('inf')
            for j in range(d):
                if j == i:
                    continue
                v = vals[j]
                if v < 0:
                    sgn = -sgn
                mag = min(mag, abs(v))
            out[i] = alpha * sgn * mag
        else:
            prod = 1.0
            for j in range(d):
                if j == i:
                    continue
                t = math.tanh(vals[j] / 2.0)
                prod *= max(-_CLAMP, min(_CLAMP, t))
            prod = max(-_CLAMP, min(_CLAMP, prod))
            out[i] = 2.0 * math.atanh(prod)
    return out


def decode(h, llr, iters=20, minsum=False, layered=False):
    """(경판정 비트, 쓴 반복 횟수). 잡음이 없으면 0 회로 끝난다.

    양수 LLR 이 비트 0 을 뜻한다(이 책 전체의 약속).

    layered 를 켜면 검사를 하나씩 처리하며 사후값을 곧바로 고친다.
    같은 곳에 절반쯤 되는 반복으로 닿는다 — 실물 복호기는 거의
    전부 이 일정을 쓴다.
    """
    n, m = h.n, h.m
    post = list(llr)
    msg = [[0.0] * len(vs) for vs in h.rows]

    def hard():
        return [0 if v > 0 else 1 for v in post]

    if syndrome_is_zero(h, hard()):
        return hard(), 0

    for it in range(1, iters + 1):
        if layered:
            for ci in range(m):
                vs = h.rows[ci]
                inc = [post[v] - msg[ci][j] for j, v in enumerate(vs)]
                new = _check_msg(inc, minsum)
                for j, v in enumerate(vs):
                    post[v] = inc[j] + new[j]
                    msg[ci][j] = new[j]
        else:
            newmsg = []
            for ci in range(m):
                vs = h.rows[ci]
                inc = [post[v] - msg[ci][j] for j, v in enumerate(vs)]
                newmsg.append(_check_msg(inc, minsum))
            post = list(llr)
            for ci in range(m):
                for j, v in enumerate(h.rows[ci]):
                    post[v] += newmsg[ci][j]
            msg = newmsg
        if syndrome_is_zero(h, hard()):
            return hard(), it
    return hard(), iters


# ── 성능 재기 ─────────────────────────────────────────────────────


def _run(h, enc, ebn0_db, frames, iters, seed, minsum, layered):
    """(프레임 오류 수, 쓴 반복의 합) — 두 잣대를 한 번에 센다."""
    rnd = random.Random(seed)
    rate = float(h.k) / h.n
    esn0 = 10.0 ** ((ebn0_db + 10.0 * math.log10(rate)) / 10.0)
    sigma2 = 1.0 / (2.0 * esn0)
    sd = math.sqrt(sigma2)
    bad = 0
    total = 0
    for _ in range(frames):
        msg = [rnd.getrandbits(1) for _ in range(h.k)]
        cw = enc.encode(msg)
        llr = [2.0 * ((1.0 - 2.0 * b) + rnd.gauss(0.0, sd)) / sigma2
               for b in cw]
        got, used = decode(h, llr, iters, minsum, layered)
        total += used
        if got != cw:
            bad += 1
    return bad, total


def frame_errors(h, enc, ebn0_db, frames, iters=20, seed=1,
                 minsum=False, layered=False):
    """부호어 하나라도 틀린 프레임의 수."""
    return _run(h, enc, ebn0_db, frames, iters, seed, minsum,
                layered)[0]


def mean_iters(h, enc, ebn0_db, frames, iters=20, seed=1,
               minsum=False, layered=False):
    """프레임마다 쓴 반복 횟수의 평균 — 일정(schedule)을 견주는 잣대."""
    return _run(h, enc, ebn0_db, frames, iters, seed, minsum,
                layered)[1] / float(frames)
