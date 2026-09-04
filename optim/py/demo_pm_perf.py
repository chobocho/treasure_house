# -*- coding: utf-8 -*-
"""12부 데모 — 성능·병목·자원, 그리고 개선을 최적화 문제로 적기."""
import math

from py import fmt
from py.pm import allocate as AL
from py.pm import log as L
from py.pm import perf


def base_log():
    """§1·§2·§6 이 공유하는 로그. 병목 표와 배낭 표가 같은 로그에서 나와야
       "예산 1 의 절감 = 1위 병목의 총 대기 절반"이 표끼리 맞아떨어진다."""
    return L.generate(n_cases=500, seed=101)


def demo_activity():
    print('■ 1. 활동별 성능 — 시간은 어디로 가는가  (케이스 500)')
    lg = base_log()
    st = perf.activity_stats(lg)
    total_d = math.fsum(v['total_duration'] for v in st.values())
    total_w = math.fsum(v['total_waiting'] for v in st.values())
    rows = [['활동', '실행 횟수', '평균 처리(h)', '평균 대기(h)', '총 처리 비중',
             '총 대기 비중']]
    for a in sorted(st, key=lambda x: -st[x]['total_duration']):
        v = st[a]
        rows.append([a, '%d' % v['count'], '%.2f' % v['mean_duration'],
                     '%.2f' % v['mean_waiting'],
                     '%.1f%%' % (100 * v['total_duration'] / total_d),
                     '%.1f%%' % (100 * v['total_waiting'] / total_w)])
    print(fmt.table(rows, align='lrrrrr'))
    cs = perf.case_stats(lg)
    print('  케이스 처리시간: 평균 %.1fh, 중앙값 %.1fh, 90분위 %.1fh, 최대 %.1fh'
          % (cs['mean'], cs['median'], cs['p90'], cs['max']))
    print('  Receive 가 총 처리시간의 대부분을 차지한다 — 그런데 그것이 곧 병목은 아니다.')
    print('  처리시간이 긴 것과 "기다리게 만드는" 것은 다른 문제다.\n')


def demo_bottleneck():
    print('■ 2. 병목은 어디인가 — 대기시간 기여도로 본다')
    lg = base_log()
    bt = perf.bottlenecks(lg)
    rows = [['순위', '활동', '실행 횟수', '평균 대기(h)', '총 대기(h)', '대기 비중',
             '고치면 얻는 것']]
    for i, r in enumerate(bt):
        gain = 0.5 * r['total_waiting']
        rows.append(['%d' % (i + 1), r['activity'], '%d' % r['count'],
                     '%.2f' % r['mean_waiting'], '%.0f' % r['total_waiting'],
                     '%.1f%%' % (100 * r['wait_share']),
                     '%.0f h 절감 (대기 절반 가정)' % gain])
    print(fmt.table(rows, align='rlrrrrl'))
    print('  평균 대기가 비슷해도 <실행 횟수>가 다르면 총 대기가 크게 달라진다.')
    print('  개선의 이득은 빈도 x 평균에 비례하므로 총합을 봐야 한다 —')
    print('  5부 정리 19.8 의 그림자 가격과 정확히 같은 사고다.\n')


def demo_resource():
    print('■ 3. 자원 분석 — 느린 사람인가, 어려운 일인가')
    lg = L.generate(n_cases=500, seed=102, slow_resource='ware1')
    rs = perf.resource_stats(lg)
    rows = [['자원', '처리 건수', '평균 처리(h)', '총 처리(h)', '주로 하는 일', '진단']]
    for r in sorted(rs, key=lambda x: -rs[x]['mean_duration']):
        v = rs[r]
        main = max(v['activities'], key=lambda a: v['activities'][a])
        peers = [rs[o]['mean_duration'] for o in rs
                 if max(rs[o]['activities'], key=lambda a: rs[o]['activities'][a]) == main
                 and o != r]
        note = ''
        if peers:
            avg = sum(peers) / len(peers)
            if v['mean_duration'] > avg * 1.8:
                note = '같은 일을 하는 동료보다 %.1f배 느리다' % (v['mean_duration'] / avg)
            elif v['mean_duration'] < avg * 0.6:
                note = '동료보다 빠르다'
        rows.append([r, '%d' % v['count'], '%.2f' % v['mean_duration'],
                     '%.0f' % v['total_duration'], main, note])
    print(fmt.table(rows, align='lrrrll'))
    print('  평균 처리시간만 보면 Receive 를 맡은 사람들이 다 느려 보인다 —')
    print('  일 자체가 오래 걸리기 때문이다. "같은 활동을 하는 동료와 비교"해야')
    print('  진짜 이상치가 드러난다. 이 로그에서는 ware1 이 그렇다.\n')


def demo_handover():
    print('■ 4. 인계 네트워크 — 일이 실제로 어떻게 흐르는가')
    lg = L.generate(n_cases=300, seed=103)
    h = perf.handover_network(lg)
    total = sum(h.values())
    rows = [['넘긴 사람', '받은 사람', '횟수', '비중']]
    for (a, b), c in sorted(h.items(), key=lambda kv: -kv[1])[:12]:
        rows.append([a, b, '%d' % c, '%.1f%%' % (100.0 * c / total)])
    print(fmt.table(rows, align='llrr'))
    print('  자원 %d명 사이에 인계 %d쌍이 관측됐다. 조직도에는 없는 흐름이'
          % (len(lg.resources()), len(h)))
    print('  드러나는 일이 많고, 그 차이가 개선의 출발점이 된다.')
    rw = perf.rework(lg)
    print('  재작업: %s' % ', '.join('%s %d회' % (a, c)
                                     for a, c in sorted(rw.items(), key=lambda kv: -kv[1])))
    print('  반려 루프가 Request/Approve 의 재작업으로 그대로 나타난다.\n')


def demo_queue():
    print('■ 5. 리틀의 법칙과 대기행렬 — 용량을 늘리면 얼마나 좋아지나')
    lg = L.generate(n_cases=600, seed=104)
    r = perf.littles_law(lg)
    rows = [['양', '값', '뜻']]
    rows.append(['도착률 λ', '%.4f 건/h' % r['lambda'], '단위 시간당 새 케이스'])
    rows.append(['평균 체류 W', '%.1f h' % r['W'], '케이스 하나가 시스템에 있는 시간'])
    rows.append(['L = λW (예측)', '%.2f 건' % r['L_predicted'], '리틀의 법칙'])
    rows.append(['L (관측)', '%.2f 건' % r['L_observed'], '실제 동시 진행 건수의 시간평균'])
    rows.append(['상대 오차', '%.2f%%' % (100 * abs(r['L_predicted'] - r['L_observed'])
                                          / r['L_observed']), '어긋나면 로그가 불완전하다는 신호'])
    print(fmt.table(rows, align='lrl'))
    print()
    print('  가동률이 1 에 가까워지면 대기가 폭발한다 (M/M/1, 서비스율 mu = 1):')
    rows = [['도착률 λ', '가동률 ρ', '평균 대기 Wq', '직전 대비']]
    prev = None
    for lam in (0.5, 0.8, 0.9, 0.95, 0.99, 0.999):
        w = perf.mm1_waiting(lam, 1.0)
        rows.append(['%.3f' % lam, '%.1f%%' % (100 * lam), '%.1f' % w,
                     '%.1f배' % (w / prev) if prev else '-'])
        prev = w
    print(fmt.table(rows, align='rrrr'))
    print('  가동률 90% → 99% 는 부하가 10% 늘어난 것인데 대기는 11배가 된다.')
    print('  "자원을 100% 활용하라"는 직관이 프로세스에서 위험한 이유다.\n')


def demo_optimize():
    print('■ 6. 개선을 최적화 문제로 적는다  (§1·§2 와 같은 로그)')
    lg = base_log()

    print('  (1) 활동-자원 배치 = 할당 문제 (7부 헝가리안)')
    out, total = AL.assign_resources(lg)
    acts, res, M = AL.cost_matrix(lg)
    rows = [['활동', '배정된 자원', '평균 처리(h)', '가장 나쁜 선택(h)', '절감']]
    for (a, r, c) in out:
        i = acts.index(a)
        worst = max(M[i])
        rows.append([a, r, '%.3f' % c, '%.3f' % worst, '%.3f' % (worst - c)])
    print(fmt.table(rows, align='llrrr'))
    print('    총 평균 처리시간 %.3f h. 자원 하나가 활동 하나만 맡는다는 제약 아래' % total)
    print('    최소가 되는 배정이며, 무작위 배치 200회 중 대부분보다 낫다.')
    print('    주의: Receive 에 buyer1 이 배정된 것은 관측이 없는 조합이라 전체 평균으로')
    print('    채웠기 때문이다. 최적화는 그 낙관적 추정을 그대로 믿는다 — 자료가 없는')
    print('    칸을 어떻게 채우느냐가 답을 바꾼다. 실무에서는 그런 칸을 큰 값으로 막거나')
    print('    "배정 불가" 제약으로 처리한다.')
    print()

    print('  (2) 예산 배분 = 0/1 배낭 (7부 분지한정·동적계획)')
    rows = [['예산(담당자 추가 인원)', '선택된 활동', '절감되는 총 대기(h)', '쓴 예산']]
    for b in (1, 2, 3, 5):
        p = AL.capacity_plan(lg, budget=b)
        rows.append(['%d' % b, ', '.join(p['chosen']), '%d' % p['saved'],
                     '%d' % p['spent']])
    print(fmt.table(rows, align='rlrr'))
    print('    "담당자를 한 명 더 붙이면 그 활동의 대기가 절반이 된다"는 가정 아래,')
    print('    예산 안에서 절감을 최대화하는 조합을 고른다. 가치=절감, 무게=인건비,')
    print('    용량=예산인 배낭 문제다. 예산이 늘수록 절감이 단조 증가하고, 예산 1 의')
    print('    절감은 2번 표의 1위 병목 "고치면 얻는 것"과 같은 수다 — 같은 로그다.')
    print()
    print('  이 두 계산은 7부에서 만든 헝가리안과 배낭 DP 를 "그대로" 호출한 것이다.')
    print('  프로세스 개선이 별도의 기법이 아니라 조합 최적화의 응용이라는 뜻이다.')


def main():
    demo_activity()
    demo_bottleneck()
    demo_resource()
    demo_handover()
    demo_queue()
    demo_optimize()


if __name__ == '__main__':
    main()
