# -*- coding: utf-8 -*-
"""PPM — 부분 일치 예측 — SPEC §17.

앞 두 바이트로 다음 바이트를 찍는다. 틀리면 "틀렸다" 고 말하고 앞 한
바이트로, 또 틀리면 맨손으로 찍는다. 그 "틀렸다" 가 **탈출(escape)**
이고, 탈출에 값을 얼마나 매기느냐가 PPM 의 전부다.

탈출값은 방법 C 로 매긴다 — 문맥에서 본 **서로 다른 기호의 수** 를
탈출의 빈도로 쓴다. 손댈 상수가 없는 방법이라 적어 두기에 가장 좋다.

배제(exclusion)가 나머지 절반이다. 2차에서 탈출했다면 2차가 알던
기호들은 1차에서 **불가능** 하다 — 알았으면 이미 적었을 테니까.
그 기호들을 빼고 확률을 만든다. 네 줄이고 몇 퍼센트가 남는다.

**모든 기호가 배제된 문맥은 건너뛴다.** 탈출이 확실한 사건이라 비트가
0이기 때문이다. 이걸 잊으면 복호기는 아무것도 안 읽고 부호기는 탈출을
적어서, 그런 입력이 처음 나오는 자리에서 둘이 어긋난다 — 고전 버그다.

시간은 기호당 O(문맥 크기), 공간은 본 문맥의 수에 비례한다.
"""
from compresslib import rangecoder, varint

MAX_ORDER = 2
ALPHABET = 256
# 문맥의 합계가 이 값에 닿으면 모든 셈을 반으로 줄인다. 레인지 코더가
# tot < 2^16 을 요구하기도 하고, 오래된 통계를 잊는 효과도 있다.
MAX_TOTAL = 8192


class Model:
    """문맥 → {기호: 셈}. 문맥은 바이트 0~2개짜리 튜플이다."""

    def __init__(self):
        self.ctx = {}

    def counts(self, key):
        return self.ctx.get(key)

    def update(self, key, sym):
        table = self.ctx.get(key)
        if table is None:
            table = {}
            self.ctx[key] = table
        table[sym] = table.get(sym, 0) + 1
        if sum(table.values()) >= MAX_TOTAL:
            for s in list(table):
                table[s] = max(1, table[s] >> 1)


def _context_keys(history):
    """2차 → 1차 → 0차 순의 문맥 열쇠. 역사가 짧으면 그만큼 짧다."""
    keys = []
    for order in range(MAX_ORDER, -1, -1):
        if order <= len(history):
            keys.append(tuple(history[len(history) - order:]))
    return keys


def _visible(table, excluded):
    """배제 안 된 기호를 번호 오름차순으로. 누적합의 순서가 이것이다."""
    return sorted(s for s in table if s not in excluded)


def encode(src):
    if not src:
        return varint.put(0)
    enc = rangecoder.Encoder()
    model = Model()
    history = []
    for b in src:
        excluded = set()
        coded = False
        for key in _context_keys(history):
            table = model.counts(key)
            if table is None:
                continue
            syms = _visible(table, excluded)
            if not syms:
                # 모두 배제됐다 — 탈출이 확실하므로 아무것도 안 적는다
                continue
            esc = len(syms)
            tot = sum(table[s] for s in syms) + esc
            if b in table and b not in excluded:
                cum = 0
                for s in syms:
                    if s == b:
                        break
                    cum += table[s]
                enc.encode_freq(cum, table[b], tot)
                coded = True
                break
            enc.encode_freq(tot - esc, esc, tot)
            excluded.update(syms)
        if not coded:
            # -1차 — 남은 기호에 균등하게 (§17.4)
            rest = [s for s in range(ALPHABET) if s not in excluded]
            enc.encode_freq(rest.index(b), 1, len(rest))
        for key in _context_keys(history):
            model.update(key, b)
        history.append(b)
        if len(history) > MAX_ORDER:
            del history[0]
    enc.flush()
    return varint.put(len(src)) + enc.bytes()


def decode(src):
    n, pos = varint.get_length(src)
    if n == 0:
        if pos != len(src):
            raise ValueError('빈 입력인데 뒤에 바이트가 있다')
        return b''
    dec = rangecoder.Decoder(src, pos)
    model = Model()
    history = []
    out = bytearray()
    for _ in range(n):
        excluded = set()
        found = None
        for key in _context_keys(history):
            table = model.counts(key)
            if table is None:
                continue
            syms = _visible(table, excluded)
            if not syms:
                continue
            esc = len(syms)
            tot = sum(table[s] for s in syms) + esc
            v = dec.decode_freq(tot)
            cum = 0
            hit = None
            for s in syms:
                if cum <= v < cum + table[s]:
                    hit = s
                    break
                cum += table[s]
            if hit is not None:
                dec.decode_update(cum, table[hit], tot)
                found = hit
                break
            dec.decode_update(tot - esc, esc, tot)
            excluded.update(syms)
        if found is None:
            rest = [s for s in range(ALPHABET) if s not in excluded]
            v = dec.decode_freq(len(rest))
            found = rest[v]
            dec.decode_update(v, 1, len(rest))
        out.append(found)
        for key in _context_keys(history):
            model.update(key, found)
        history.append(found)
        if len(history) > MAX_ORDER:
            del history[0]
    return bytes(out)
