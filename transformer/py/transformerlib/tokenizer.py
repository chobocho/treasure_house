# -*- coding: utf-8 -*-
"""바이트 BPE 토크나이저 — SPEC.md §5 를 그대로 옮겼다.

글자를 수로 바꾸는 방법은 셋이다. 글자마다 번호(어휘가 끝없이 커진다),
바이트마다 번호(어휘 256 이지만 한글 한 음절이 토큰 셋), 그리고 그
사이의 BPE — 자주 붙어 나오는 바이트 짝을 새 토큰으로 합친다.

  · 사전 토크나이저가 글을 조각으로 자른다(공백+낱말, 숫자, 기호…).
    병합은 조각 안에서만 일어난다 — "의 " 와 "다." 가 붙은 토큰이
    생기지 않게.
  · 학습: 가장 많이 나온 짝을 합치고, 다시 센다. 동률이면 id 짝이
    사전순으로 작은 쪽. 이 규칙이 없으면 파이썬 dict 차례에 따라
    병합이 달라져 C 와 어긋난다.
  · 인코드: 조각마다 순위가 가장 낮은(먼저 배운) 병합부터 적용.

학습은 짝 → 그 짝이 든 조각 목록을 들고 다녀, 병합 한 번에 그 짝이
든 조각만 다시 센다(다시 세기는 영향받은 조각의 길이 합). 다만 가장
많은 짝을 고르는 max 는 매번 짝 전체를 훑는다. 인코드는 조각 결과를
기억해 같은 조각을 다시 계산하지 않는다.
"""
import io
import struct


def char_class(c):
    """SPEC §5.2 부류표. S 공백·W 줄바꿈류·D 숫자·P 기호·L 글자."""
    o = ord(c)
    if c == ' ':
        return 'S'
    if 0x09 <= o <= 0x0D:
        return 'W'
    if '0' <= c <= '9':
        return 'D'
    if o < 0x80:
        return 'L' if c.isalpha() else 'P'
    if (0x2000 <= o <= 0x206F or 0x3000 <= o <= 0x303F
            or 0xFF00 <= o <= 0xFF65):
        return 'P'
    return 'L'


def pretokenize(text):
    """SPEC §5.2 결정표. 조각을 이으면 원문이 나온다. O(글자 수)."""
    cls = [char_class(c) for c in text]
    n, i, out = len(text), 0, []
    while i < n:
        c = cls[i]
        if c == 'S' and i + 1 < n and cls[i + 1] in 'LDP':
            k, j = cls[i + 1], i + 2
            while j < n and cls[j] == k:
                j += 1
        elif c in 'SW':
            j = i + 1
            while j < n and cls[j] in 'SW':
                j += 1
            # 공백 연속의 마지막 공백은 다음 낱말에게 양보한다
            if (j < n and cls[j] in 'LDP' and text[j - 1] == ' '
                    and j - i >= 2):
                j -= 1
        else:
            j = i + 1
            while j < n and cls[j] == c:
                j += 1
        out.append(text[i:j])
        i = j
    return out


def byte_vocab():
    return [bytes([b]) for b in range(256)]


def char_vocab(text):
    """과제용 문자 어휘 — 쓰인 바이트만 오름차순 (SPEC §5.1)."""
    return [bytes([b]) for b in sorted(set(text.encode('utf-8')))]


def _pairs(ids):
    return zip(ids, ids[1:])


def train_bpe(text, vocab_size):
    """(어휘, 병합). 기본 토큰은 0‥255, 순위 r 의 병합은 256 + r."""
    counts = {}
    for chunk in pretokenize(text):
        b = chunk.encode('utf-8')
        counts[b] = counts.get(b, 0) + 1
    words = [list(b) for b in counts]
    freq = list(counts.values())
    vocab = byte_vocab()
    merges = []

    pc, where = {}, {}              # 짝 → 개수, 짝 → 조각 번호들
    for w, ids in enumerate(words):
        for p in _pairs(ids):
            pc[p] = pc.get(p, 0) + freq[w]
            where.setdefault(p, set()).add(w)

    while len(vocab) < vocab_size and pc:
        # 개수가 가장 많고, 같으면 (왼쪽, 오른쪽) 이 작은 짝
        best = max(pc.items(), key=lambda kv: (kv[1], -kv[0][0],
                                               -kv[0][1]))
        (l, r), cnt = best
        if cnt < 2:
            break
        new = len(vocab)
        merges.append((l, r))
        vocab.append(vocab[l] + vocab[r])
        for w in sorted(where.pop((l, r), ())):
            ids = words[w]
            for p in _pairs(ids):             # 옛 짝을 빼고
                pc[p] -= freq[w]
                if pc[p] == 0:
                    del pc[p]
            words[w] = ids = _merge(ids, l, r, new)
            for p in _pairs(ids):             # 새 짝을 더한다
                pc[p] = pc.get(p, 0) + freq[w]
                where.setdefault(p, set()).add(w)
    return vocab, merges


def _merge(ids, l, r, new):
    """왼쪽부터 겹치지 않게 (l, r) → new. O(len)."""
    out, i, n = [], 0, len(ids)
    while i < n:
        if i + 1 < n and ids[i] == l and ids[i + 1] == r:
            out.append(new)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


class Tokenizer(object):
    def __init__(self, vocab, merges):
        self.vocab = list(vocab)
        self.merges = list(merges)
        n_base = sum(1 for v in vocab if len(v) == 1)
        self.base = dict((v[0], i)
                         for i, v in enumerate(vocab[:n_base]))
        self.rank = dict(((l, r), k) for k, (l, r) in enumerate(merges))
        self.n_base = n_base
        self.cache = {}

    def encode_chunk(self, chunk):
        """SPEC §5.4 — 낮은 순위부터. 한 바퀴 O(len), 최대 len 바퀴."""
        if chunk in self.cache:
            return self.cache[chunk]
        ids = []
        for b in chunk.encode('utf-8'):
            if b not in self.base:
                raise ValueError('어휘에 없는 바이트 0x%02X (%r)'
                                 % (b, chunk))
            ids.append(self.base[b])
        while len(ids) >= 2:
            ranks = [self.rank.get(p) for p in _pairs(ids)]
            known = [k for k in ranks if k is not None]
            if not known:
                break
            k = min(known)
            l, r = self.merges[k]
            ids = _merge(ids, l, r, self.n_base + k)
        self.cache[chunk] = ids
        return ids

    def encode(self, text):
        out = []
        for chunk in pretokenize(text):
            out.extend(self.encode_chunk(chunk))
        return out

    def decode_bytes(self, ids):
        return b''.join(self.vocab[i] for i in ids)

    def decode(self, ids):
        """토큰 경계가 UTF-8 글자 가운데일 수 있다 — 깨진 곳은 �."""
        return self.decode_bytes(ids).decode('utf-8', 'replace')


def save(prefix, vocab, merges):
    """prefix.vocab (id<TAB>16진) · prefix.merges (왼<TAB>오).
    SPEC §5.1."""
    with io.open(prefix + '.vocab', 'w', encoding='utf-8',
                 newline='\n') as f:
        for i, v in enumerate(vocab):
            f.write('%d\t%s\n' % (i, v.hex()))
    with io.open(prefix + '.merges', 'w', encoding='utf-8',
                 newline='\n') as f:
        for l, r in merges:
            f.write('%d\t%d\n' % (l, r))


def load(prefix):
    vocab, merges = [], []
    for line in io.open(prefix + '.vocab', encoding='utf-8'):
        i, h = line.rstrip('\n').split('\t')
        if int(i) != len(vocab):
            raise ValueError('.vocab id 가 빈틈 없이 이어지지 않는다')
        vocab.append(bytes.fromhex(h))
    for line in io.open(prefix + '.merges', encoding='utf-8'):
        l, r = line.rstrip('\n').split('\t')
        merges.append((int(l), int(r)))
    return vocab, merges


def write_bin(path, ids):
    """uint16 리틀 엔디언, 머리말 없음 — SPEC §5.5."""
    if any(not 0 <= i < 65536 for i in ids):
        raise ValueError('uint16 에 안 들어가는 id')
    with io.open(path, 'wb') as f:
        f.write(struct.pack('<%dH' % len(ids), *ids))


def read_bin(path):
    raw = io.open(path, 'rb').read()
    return list(struct.unpack('<%dH' % (len(raw) // 2), raw))
