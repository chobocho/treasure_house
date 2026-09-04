# -*- coding: utf-8 -*-
"""페트리넷 — 프로세스 모델의 표준 표현.

   장소(place)와 전이(transition)로 이루어진 이분 그래프이고, 장소에 놓인 토큰의
   분포(marking)가 상태다. 전이는 입력 장소마다 토큰이 있을 때 <발화>할 수 있고,
   발화하면 입력에서 토큰을 하나씩 빼고 출력에 하나씩 놓는다.

   왜 이 표현인가:
     · 병렬(두 전이가 동시에 활성)과 선택(한 장소에서 두 전이가 경쟁)을 모두 적는다
     · 상태가 명확해서 "이 자취를 이 모델이 낼 수 있는가"를 기계적으로 판정한다
     · 그 판정이 11부의 적합도 검사와 정렬로 이어진다
"""


_SAME = object()      # "라벨을 이름과 같게" 를 뜻하는 표지. None 은 보이지 않는 전이(τ) 다.


class PetriNet(object):
    """1-안전(1-safe)을 가정하지 않는 일반 페트리넷. 마킹은 {장소: 토큰 수} 다."""

    def __init__(self, places=None, transitions=None, name=''):
        self.places = set(places or [])
        self.transitions = {}          # 이름 -> 라벨 (None 이면 보이지 않는 전이 τ)
        for t in (transitions or []):
            self.transitions[t] = t
        self.ins = {}                  # 전이 -> {장소: 개수}
        self.outs = {}
        self.name = name

    def add_place(self, p):
        self.places.add(p)
        return p

    def add_transition(self, t, label=_SAME):
        """label 을 생략하면 이름과 같은 라벨, None 을 주면 보이지 않는 전이(τ) 다."""
        self.transitions[t] = t if label is _SAME else label
        self.ins.setdefault(t, {})
        self.outs.setdefault(t, {})
        return t

    def add_arc(self, src, dst, weight=1):
        """장소→전이 또는 전이→장소. 방향은 인자의 종류로 판별한다."""
        if src in self.places:
            self.ins.setdefault(dst, {})
            self.ins[dst][src] = self.ins[dst].get(src, 0) + weight
        else:
            self.outs.setdefault(src, {})
            self.outs[src][dst] = self.outs[src].get(dst, 0) + weight

    # ── 실행 의미론 ──────────────────────────────────────────
    def enabled(self, marking):
        """현재 마킹에서 발화 가능한 전이들."""
        out = []
        for t in self.transitions:
            need = self.ins.get(t, {})
            if all(marking.get(p, 0) >= c for p, c in need.items()):
                out.append(t)
        return out

    def fire(self, marking, t):
        """전이 t 를 발화한 뒤의 새 마킹. 발화 불가능하면 ValueError."""
        need = self.ins.get(t, {})
        if not all(marking.get(p, 0) >= c for p, c in need.items()):
            raise ValueError('전이 %s 는 지금 발화할 수 없다' % t)
        m = dict(marking)
        for p, c in need.items():
            m[p] -= c
            if m[p] == 0:
                del m[p]
        for p, c in self.outs.get(t, {}).items():
            m[p] = m.get(p, 0) + c
        return m

    def label_of(self, t):
        return self.transitions.get(t, t)

    def transitions_with_label(self, label):
        return [t for t, l in self.transitions.items() if l == label]

    def summary(self):
        arcs = sum(len(v) for v in self.ins.values()) + \
               sum(len(v) for v in self.outs.values())
        return {'places': len(self.places), 'transitions': len(self.transitions),
                'arcs': arcs,
                'silent': sum(1 for l in self.transitions.values() if l is None)}


def replay_trace(net, marking0, final, trace, allow_silent=True, max_silent=6):
    """자취를 모델 위에서 그대로 따라가 본다 (완벽 재생이 되는가).

       보이지 않는 전이(τ)가 있으면 그것들을 몇 번 발화해서라도 다음 활동을
       가능하게 만들 수 있는지 너비 우선으로 찾아 본다. 이것이 11부 정렬의
       가장 단순한 형태다 — 비용을 매기지 않고 '되는가/안 되는가'만 본다.

       반환: (성공 여부, 최종 마킹)
    """
    m = dict(marking0)
    for act in trace:
        m2 = _advance(net, m, act, allow_silent, max_silent)
        if m2 is None:
            return False, m
        m = m2
    if allow_silent:
        m = _to_final(net, m, final, max_silent) or m
    return _covers(m, final), m


def _advance(net, m, label, allow_silent, max_silent):
    """label 을 가진 전이를 발화할 수 있게 되는 마킹을 찾는다(τ 를 통과해서라도)."""
    seen = {_key(m)}
    frontier = [(m, 0)]
    while frontier:
        cur, depth = frontier.pop(0)
        for t in net.enabled(cur):
            if net.label_of(t) == label:
                return net.fire(cur, t)
        if not allow_silent or depth >= max_silent:
            continue
        for t in net.enabled(cur):
            if net.label_of(t) is None:
                nxt = net.fire(cur, t)
                k = _key(nxt)
                if k not in seen:
                    seen.add(k)
                    frontier.append((nxt, depth + 1))
    return None


def _to_final(net, m, final, max_silent):
    """τ 만 발화해서 최종 마킹에 닿을 수 있으면 그 마킹을 돌려준다."""
    seen = {_key(m)}
    frontier = [(m, 0)]
    while frontier:
        cur, depth = frontier.pop(0)
        if _covers(cur, final):
            return cur
        if depth >= max_silent:
            continue
        for t in net.enabled(cur):
            if net.label_of(t) is None:
                nxt = net.fire(cur, t)
                k = _key(nxt)
                if k not in seen:
                    seen.add(k)
                    frontier.append((nxt, depth + 1))
    return None


def _covers(m, final):
    return all(m.get(p, 0) >= c for p, c in final.items())


def _key(m):
    return tuple(sorted((p, c) for p, c in m.items() if c))
