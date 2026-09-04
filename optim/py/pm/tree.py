# -*- coding: utf-8 -*-
"""프로세스 트리 — 구조가 보장된 프로세스 모델.

   연산자 네 개와 잎(활동)만으로 프로세스를 적는다.

       →(A, B, …)   차례로 실행         seq
       ×(A, B, …)   하나만 선택         xor
       ∧(A, B, …)   병렬(순서 무관)     and
       ↺(A, B, …)   A 를 하고, 필요하면 B 를 거쳐 A 로 되돌아온다   loop

   왜 이 표현인가: 이렇게 만든 모델은 <반드시 건전(sound)하다> — 교착이 없고,
   시작하면 반드시 끝낼 수 있으며, 쓸모없는 부분이 없다. 알파 알고리즘이 만든
   페트리넷은 그 보장이 없어 실무에서 곤란을 겪는다.
"""
from py.pm import petri

SEQ, XOR, AND, LOOP, ACT, TAU = 'seq', 'xor', 'and', 'loop', 'act', 'tau'


class Node(object):
    __slots__ = ('op', 'label', 'children')

    def __init__(self, op, label=None, children=None):
        self.op = op
        self.label = label
        self.children = list(children or [])

    def __repr__(self):
        if self.op == ACT:
            return str(self.label)
        if self.op == TAU:
            return 'τ'
        sym = {SEQ: '→', XOR: '×', AND: '∧', LOOP: '↺'}[self.op]
        return '%s(%s)' % (sym, ', '.join(repr(c) for c in self.children))

    def activities(self):
        if self.op == ACT:
            return {self.label}
        out = set()
        for c in self.children:
            out |= c.activities()
        return out

    def size(self):
        return 1 + sum(c.size() for c in self.children)


def act(label):
    return Node(ACT, label)


def tau():
    return Node(TAU)


def to_petri(node):
    """프로세스 트리를 페트리넷으로 바꾼다 (표준 구성).

       각 부분트리를 '입력 장소 하나, 출력 장소 하나'를 가진 조각으로 만들고,
       연산자마다 정해진 방식으로 이어 붙인다. 필요한 곳에 보이지 않는 전이(τ)를
       넣는다 — 병렬의 분기·합류, 루프의 되돌림이 그 자리다.

       반환: (PetriNet, 초기 마킹, 최종 마킹)
    """
    net = petri.PetriNet(name='tree')
    counter = [0]

    def newp():
        counter[0] += 1
        p = 'p%d' % counter[0]
        net.add_place(p)
        return p

    def newt(label=None):
        counter[0] += 1
        t = 't%d' % counter[0]
        net.add_transition(t, label)
        return t

    def build(n, src, snk):
        if n.op == ACT:
            t = newt(n.label)
            net.add_arc(src, t)
            net.add_arc(t, snk)
        elif n.op == TAU:
            t = newt(None)
            net.add_arc(src, t)
            net.add_arc(t, snk)
        elif n.op == SEQ:
            cur = src
            for i, c in enumerate(n.children):
                nxt = snk if i == len(n.children) - 1 else newp()
                build(c, cur, nxt)
                cur = nxt
        elif n.op == XOR:
            for c in n.children:
                build(c, src, snk)          # 같은 장소에서 갈라져 같은 장소로 모인다
        elif n.op == AND:
            split = newt(None)
            join = newt(None)
            net.add_arc(src, split)
            net.add_arc(join, snk)
            for c in n.children:
                a, b = newp(), newp()
                net.add_arc(split, a)
                net.add_arc(b, join)
                build(c, a, b)
        elif n.op == LOOP:
            body = n.children[0]
            redo = n.children[1] if len(n.children) > 1 else tau()
            mid = newp()
            build(body, src, mid)
            # 나가는 길
            out = newt(None)
            net.add_arc(mid, out)
            net.add_arc(out, snk)
            # 되돌아오는 길
            back = newp()
            build(redo, mid, back)
            re = newt(None)
            net.add_arc(back, re)
            net.add_arc(re, src)
        else:
            raise ValueError('모르는 연산자: %s' % n.op)

    i = newp()
    o = newp()
    build(node, i, o)
    return net, {i: 1}, {o: 1}
