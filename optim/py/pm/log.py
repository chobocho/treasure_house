# -*- coding: utf-8 -*-
"""이벤트 로그 — 프로세스 마이닝의 원재료.

   프로세스 마이닝이 다루는 자료는 단 세 열이면 시작할 수 있다.

       케이스 ID | 활동 이름 | 타임스탬프   (+ 있으면 자원, 비용, 속성)

   같은 케이스 ID 를 시간순으로 모은 것이 <자취(trace)>이고, 자취들의 다중집합이
   <이벤트 로그>다. 여기서부터 모든 것이 시작된다.

   왜 최적화 교재에 이것이 있는가: 로그에서 모델을 뽑는 일, 로그가 모델에 얼마나
   맞는지 재는 일, 병목을 찾는 일이 전부 최적화 문제이기 때문이다. 10~12부에서
   그 셋을 각각 다룬다.
"""
import math
import random


class Event(object):
    __slots__ = ('case', 'activity', 'time', 'resource', 'attrs')

    def __init__(self, case, activity, time, resource=None, **attrs):
        self.case = case
        self.activity = activity
        self.time = float(time)
        self.resource = resource
        self.attrs = attrs

    def __repr__(self):
        return 'Event(%s, %s, %.2f)' % (self.case, self.activity, self.time)


class Trace(object):
    """한 케이스의 사건들 — 시간순으로 정렬되어 있다."""

    __slots__ = ('case', 'events')

    def __init__(self, case, events=None):
        self.case = case
        self.events = list(events or [])

    def add(self, ev):
        self.events.append(ev)

    def sort(self):
        self.events.sort(key=lambda e: e.time)

    @property
    def activities(self):
        return tuple(e.activity for e in self.events)

    @property
    def duration(self):
        if not self.events:
            return 0.0
        return self.events[-1].time - self.events[0].time

    def __len__(self):
        return len(self.events)

    def __iter__(self):
        return iter(self.events)

    def __repr__(self):
        return 'Trace(%s, %s)' % (self.case, ','.join(self.activities))


class EventLog(object):
    """자취들의 다중집합. 통계와 그래프를 뽑는 최소한의 도구를 함께 둔다."""

    def __init__(self, traces=None):
        self.traces = list(traces or [])

    @classmethod
    def from_events(cls, events):
        """평평한 사건 목록을 케이스별로 묶는다 — 실제 자료는 대개 이 꼴로 온다."""
        by_case = {}
        for e in events:
            by_case.setdefault(e.case, Trace(e.case)).add(e)
        traces = []
        for case in sorted(by_case, key=lambda c: (by_case[c].events[0].time, str(c))):
            t = by_case[case]
            t.sort()
            traces.append(t)
        return cls(traces)

    @classmethod
    def from_variants(cls, variants):
        """{('A','B','C'): 5, …} 형태에서 로그를 만든다 — 교재 예제용."""
        traces = []
        cid = 0
        for seq, cnt in variants.items():
            for _ in range(cnt):
                cid += 1
                evs = [Event(cid, a, float(i)) for i, a in enumerate(seq)]
                traces.append(Trace(cid, evs))
        return cls(traces)

    def __len__(self):
        return len(self.traces)

    def __iter__(self):
        return iter(self.traces)

    # ── 기본 통계 ────────────────────────────────────────────
    def activities(self):
        """등장하는 활동 이름의 집합."""
        out = set()
        for t in self.traces:
            out.update(t.activities)
        return out

    def variants(self):
        """서로 다른 활동 순서와 그 빈도. 로그 압축의 첫걸음이다.

           실제 로그에서 케이스는 수만 개라도 변형(variant)은 수백 개인 일이 흔하다.
           대부분의 알고리즘이 변형 단위로 돌면 훨씬 싸진다.
        """
        cnt = {}
        for t in self.traces:
            cnt[t.activities] = cnt.get(t.activities, 0) + 1
        return cnt

    def start_activities(self):
        cnt = {}
        for t in self.traces:
            if len(t):
                a = t.activities[0]
                cnt[a] = cnt.get(a, 0) + 1
        return cnt

    def end_activities(self):
        cnt = {}
        for t in self.traces:
            if len(t):
                a = t.activities[-1]
                cnt[a] = cnt.get(a, 0) + 1
        return cnt

    def dfg(self):
        """직접후행 그래프(directly-follows graph): {(a, b): 횟수}.

           거의 모든 프로세스 발견 알고리즘이 이 그래프에서 출발한다.
           로그 전체를 한 번 훑으면 되므로 O(사건 수) 다.
        """
        out = {}
        for t in self.traces:
            acts = t.activities
            for i in range(len(acts) - 1):
                k = (acts[i], acts[i + 1])
                out[k] = out.get(k, 0) + 1
        return out

    def resources(self):
        out = set()
        for t in self.traces:
            for e in t:
                if e.resource is not None:
                    out.add(e.resource)
        return out

    def summary(self):
        n_ev = sum(len(t) for t in self.traces)
        durs = [t.duration for t in self.traces if len(t) > 1]
        return {
            'cases': len(self.traces),
            'events': n_ev,
            'activities': len(self.activities()),
            'variants': len(self.variants()),
            'avg_len': n_ev / float(len(self.traces)) if self.traces else 0.0,
            'avg_duration': (math.fsum(durs) / len(durs)) if durs else 0.0,
            'resources': len(self.resources()),
        }

    def filter_variants(self, min_count):
        """빈도가 낮은 변형을 걸러낸다 — 잡음 제거의 가장 단순한 형태."""
        keep = {v for v, c in self.variants().items() if c >= min_count}
        return EventLog([t for t in self.traces if t.activities in keep])


# ---------------------------------------------------------------- 로그 생성기

MODEL = {
    # 구매 프로세스: 요청 → 승인(반려 시 재요청) → (주문 ∥ 예산확인) → 입고 → 지급
    'start': 'Request',
    'flow': [
        ('Request', ['Approve']),
        ('Approve', ['Order', 'Reject']),
        ('Reject', ['Request']),
        ('Order', ['Receive']),
        ('Receive', ['Pay']),
        ('Pay', []),
    ],
}

DURATION = {'Request': (2.0, 0.5), 'Approve': (8.0, 4.0), 'Reject': (1.0, 0.3),
            'Order': (4.0, 1.0), 'Check': (3.0, 1.0), 'Receive': (48.0, 20.0),
            'Pay': (6.0, 2.0)}

ROLES = {'Request': ['clerk1', 'clerk2'], 'Approve': ['mgr1', 'mgr2'],
         'Reject': ['mgr1', 'mgr2'], 'Order': ['buyer1', 'buyer2', 'buyer3'],
         'Check': ['fin1'], 'Receive': ['ware1', 'ware2'], 'Pay': ['fin1', 'fin2']}


def generate(n_cases=200, seed=0, reject_prob=0.25, parallel_prob=0.5,
             noise=0.0, slow_resource=None):
    """합성 이벤트 로그를 만든다 — 정답 모델을 아는 상태에서 실험하기 위해서다.

       프로세스 마이닝 연구의 표준적인 방법이다. 실제 로그로는 "발견한 모델이
       맞는가"를 확인할 길이 없지만, 합성 로그는 <생성 모델>을 알고 있으므로
       알고리즘이 그것을 되찾는지 검사할 수 있다.

       noise: 이 확률로 사건 하나를 지우거나 순서를 뒤바꾼다(현실의 불완전한 기록).
       slow_resource: 특정 자원의 처리 시간을 3배로 — 병목 실험용(12부).
    """
    rng = random.Random(seed)
    events = []
    clock0 = 0.0
    for case in range(1, n_cases + 1):
        t = clock0 + rng.expovariate(1 / 6.0)      # 케이스 도착 간격
        clock0 = t
        seq = []
        # 요청 → 승인 (반려하면 재요청)
        while True:
            seq.append('Request')
            seq.append('Approve')
            if rng.random() < reject_prob:
                seq.append('Reject')
                continue
            break
        # 주문과 예산확인이 병렬로 일어날 수 있다
        if rng.random() < parallel_prob:
            pair = ['Order', 'Check']
            rng.shuffle(pair)
            seq.extend(pair)
        else:
            seq.append('Order')
        seq.append('Receive')
        seq.append('Pay')

        for act in seq:
            mu, sd = DURATION[act]
            who = rng.choice(ROLES[act])
            dur = max(0.1, rng.gauss(mu, sd))
            if slow_resource and who == slow_resource:
                dur *= 3.0
            wait = rng.expovariate(1 / 2.0)
            t += wait + dur
            events.append(Event(case, act, t, resource=who,
                                duration=dur, waiting=wait))

    if noise > 0:
        events = _add_noise(events, noise, rng)
    return EventLog.from_events(events)


def _add_noise(events, p, rng):
    """기록 누락과 순서 뒤바뀜을 흉내낸다."""
    by_case = {}
    for e in events:
        by_case.setdefault(e.case, []).append(e)
    out = []
    for case in sorted(by_case):
        evs = sorted(by_case[case], key=lambda e: e.time)
        if len(evs) > 2 and rng.random() < p:
            if rng.random() < 0.5:
                del evs[rng.randrange(1, len(evs) - 1)]        # 사건 하나 누락
            else:
                i = rng.randrange(len(evs) - 1)                # 이웃 두 사건 뒤바꿈
                evs[i].time, evs[i + 1].time = evs[i + 1].time, evs[i].time
                evs.sort(key=lambda e: e.time)
        out.extend(evs)
    return out
