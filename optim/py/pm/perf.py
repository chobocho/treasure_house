# -*- coding: utf-8 -*-
"""성능 분석 — 어디가 느리고, 왜 그런가.

   발견(10부)과 적합도(11부)는 "무엇이 일어났는가"를 다뤘다. 여기서는 "얼마나
   오래 걸렸는가"를 묻는다. 그리고 그 답이 나오면 곧바로 다음 질문이 온다 —
   "무엇을 고쳐야 하는가". 그 순간부터는 최적화 문제다.

   이 파일이 계산하는 것
     · 활동별 처리시간·대기시간, 케이스 처리시간
     · 병목 판정 (대기시간 기여도)
     · 자원별 작업부하와 처리 속도
     · 인계(handover) 네트워크
     · 리틀의 법칙으로 본 재공품(WIP)
   그리고 이 값들이 12부 후반의 <자원 배치 최적화>의 입력이 된다.
"""
import math


def _num(x):
    return float(x)


def activity_stats(log):
    """활동별 처리시간·대기시간 통계. 생성기가 남긴 duration·waiting 속성을 쓴다."""
    acc = {}
    for t in log:
        for e in t:
            d = acc.setdefault(e.activity, {'n': 0, 'dur': [], 'wait': []})
            acc[e.activity]['n'] += 1
            if 'duration' in e.attrs:
                d['dur'].append(_num(e.attrs['duration']))
            if 'waiting' in e.attrs:
                d['wait'].append(_num(e.attrs['waiting']))
    out = {}
    for a, d in acc.items():
        out[a] = {
            'count': d['n'],
            'mean_duration': _mean(d['dur']),
            'mean_waiting': _mean(d['wait']),
            'total_duration': math.fsum(d['dur']),
            'total_waiting': math.fsum(d['wait']),
            'p90_waiting': _quantile(d['wait'], 0.9),
        }
    return out


def _mean(xs):
    return math.fsum(xs) / len(xs) if xs else 0.0


def _quantile(xs, q):
    if not xs:
        return 0.0
    ys = sorted(xs)
    i = min(len(ys) - 1, int(q * (len(ys) - 1) + 0.5))
    return ys[i]


def case_stats(log):
    """케이스 처리시간(첫 사건 ~ 마지막 사건)의 분포."""
    ds = [t.duration for t in log if len(t) > 1]
    return {'n': len(ds), 'mean': _mean(ds), 'median': _quantile(ds, 0.5),
            'p90': _quantile(ds, 0.9), 'max': max(ds) if ds else 0.0,
            'min': min(ds) if ds else 0.0}


def bottlenecks(log):
    """병목 후보를 대기시간 기여도로 정렬한다.

       기여도 = (그 활동의 총 대기시간) / (모든 활동의 총 대기시간)

       왜 총합인가: 평균 대기가 길어도 드물게 일어나면 전체에 미치는 영향은 작다.
       고쳐서 얻는 이득은 <빈도 x 평균>에 비례하므로 총합을 본다. 5부 정리 19.8 의
       그림자 가격과 같은 사고다 — "한 단위 개선했을 때 목적값이 얼마나 좋아지나".
    """
    st = activity_stats(log)
    total_wait = math.fsum(v['total_waiting'] for v in st.values())
    total_dur = math.fsum(v['total_duration'] for v in st.values())
    rows = []
    for a, v in st.items():
        rows.append({
            'activity': a,
            'count': v['count'],
            'mean_waiting': v['mean_waiting'],
            'total_waiting': v['total_waiting'],
            'wait_share': v['total_waiting'] / total_wait if total_wait else 0.0,
            'dur_share': v['total_duration'] / total_dur if total_dur else 0.0,
        })
    rows.sort(key=lambda r: -r['total_waiting'])
    return rows


def resource_stats(log):
    """자원별 처리 건수·평균 처리시간. 느린 자원과 과부하 자원을 가려낸다."""
    acc = {}
    for t in log:
        for e in t:
            if e.resource is None:
                continue
            d = acc.setdefault(e.resource, {'n': 0, 'dur': [], 'acts': {}})
            d['n'] += 1
            if 'duration' in e.attrs:
                d['dur'].append(_num(e.attrs['duration']))
            d['acts'][e.activity] = d['acts'].get(e.activity, 0) + 1
    out = {}
    for r, d in acc.items():
        out[r] = {'count': d['n'], 'mean_duration': _mean(d['dur']),
                  'total_duration': math.fsum(d['dur']),
                  'activities': d['acts']}
    return out


def handover_network(log):
    """인계 네트워크: {(자원 a, 자원 b): 횟수} — a 가 한 일 다음에 b 가 일했다.

       조직 안에서 일이 실제로 어떻게 흘러가는지 보여 준다. 조직도와 다른 경우가
       많고, 그 차이가 개선의 출발점이 되는 일이 흔하다.
    """
    out = {}
    for t in log:
        evs = [e for e in t if e.resource is not None]
        for i in range(len(evs) - 1):
            k = (evs[i].resource, evs[i + 1].resource)
            out[k] = out.get(k, 0) + 1
    return out


def rework(log):
    """재작업: 한 케이스 안에서 같은 활동이 두 번 이상 일어난 횟수."""
    out = {}
    for t in log:
        seen = {}
        for a in t.activities:
            seen[a] = seen.get(a, 0) + 1
        for a, c in seen.items():
            if c > 1:
                out[a] = out.get(a, 0) + (c - 1)
    return out


def littles_law(log, window=None):
    """리틀의 법칙:  L = λ W  (평균 재공품 = 도착률 x 평균 체류시간).

       프로세스 마이닝에서 특히 유용한 이유: 세 값 중 둘을 로그에서 직접 재고
       나머지 하나를 검산할 수 있다. 어긋나면 로그가 불완전하다는 신호다.
    """
    ts = [(t.events[0].time, t.events[-1].time) for t in log if len(t)]
    if not ts:
        return {}
    t0 = min(a for a, _ in ts)
    t1 = max(b for _, b in ts)
    span = (t1 - t0) if window is None else window
    lam = len(ts) / span if span > 0 else 0.0
    W = _mean([b - a for a, b in ts])
    # 실제 재공품: 시간축을 훑으며 동시에 열려 있는 케이스 수의 시간평균
    points = []
    for a, b in ts:
        points.append((a, 1))
        points.append((b, -1))
    points.sort()
    cur, prev, area = 0, t0, 0.0
    for tm, d in points:
        area += cur * (tm - prev)
        cur += d
        prev = tm
    L_obs = area / span if span > 0 else 0.0
    return {'lambda': lam, 'W': W, 'L_predicted': lam * W, 'L_observed': L_obs,
            'span': span}


def mm1_waiting(lam, mu):
    """M/M/1 대기행렬의 평균 대기시간 W_q = λ / (μ(μ−λ)).

       용량 증설의 효과를 어림하는 데 쓴다. ρ = λ/μ 가 1 에 가까워지면 대기가
       <폭발>한다는 것이 요점이다 — 가동률 95% 와 99% 의 차이가 5배가 아니라 5배 이상이다.
    """
    if mu <= lam:
        return float('inf')
    return lam / (mu * (mu - lam))
