# -*- coding: utf-8 -*-
"""10부 데모 — 이벤트 로그를 처음 열어 보면 무엇이 보이는가."""
from py import fmt
from py.pm import log as L

SHORT = {'Request': 'Req', 'Approve': 'App', 'Reject': 'Rej', 'Order': 'Ord',
         'Check': 'Chk', 'Receive': 'Rec', 'Pay': 'Pay'}


def short(seq, maxlen=9):
    """긴 자취를 줄여 적는다 — 표가 화면을 넘지 않게."""
    xs = [SHORT.get(a, a) for a in seq]
    if len(xs) <= maxlen:
        return ' '.join(xs)
    return ' '.join(xs[:maxlen - 2]) + ' … ' + ' '.join(xs[-2:])


def demo_summary():
    print('■ 1. 로그의 첫인상  (합성 구매 프로세스, 케이스 500개)')
    lg = L.generate(n_cases=500, seed=1)
    s = lg.summary()
    rows = [['항목', '값', '뜻']]
    rows.append(['케이스 수', '%d' % s['cases'], '프로세스 인스턴스 (구매 건)'])
    rows.append(['사건 수', '%d' % s['events'], '기록된 활동 실행 횟수'])
    rows.append(['활동 종류', '%d' % s['activities'], '모델의 전이가 될 후보'])
    rows.append(['변형(variant) 수', '%d' % s['variants'], '서로 다른 활동 순서'])
    rows.append(['평균 자취 길이', '%.2f' % s['avg_len'], '케이스당 사건 수'])
    rows.append(['평균 처리시간', '%.1f 시간' % s['avg_duration'], '첫 사건 ~ 마지막 사건'])
    rows.append(['자원 수', '%d' % s['resources'], '작업을 수행한 사람/시스템'])
    print(fmt.table(rows, align='lrl'))
    print('  케이스 500개인데 변형은 %d가지뿐이다. 실제 로그도 대개 이렇다 —' % s['variants'])
    print('  그래서 대부분의 알고리즘은 케이스가 아니라 "변형" 단위로 돌면 훨씬 싸진다.\n')


def demo_variants():
    print('■ 2. 변형 — 로그를 압축해서 보는 첫 방법')
    lg = L.generate(n_cases=500, seed=1)
    var = lg.variants()
    total = sum(var.values())
    rows = [['#', '활동 순서 (약칭)', '길이', '케이스 수', '비율', '누적 비율']]
    acc = 0
    items = sorted(var.items(), key=lambda kv: -kv[1])
    for i, (seq, cnt) in enumerate(items):
        acc += cnt
        if i < 8:
            rows.append(['%d' % (i + 1), short(seq), '%d' % len(seq), '%d' % cnt,
                         '%.1f%%' % (100.0 * cnt / total),
                         '%.1f%%' % (100.0 * acc / total)])
    rest = len(items) - 8
    if rest > 0:
        rows.append(['…', '그 외 %d개 변형 (각 1~2건)' % rest, '', '%d' % (total - acc + sum(c for _, c in items[8:])), '', '100.0%'])
    print(fmt.table(rows, align='rlrrrr'))
    print('  약칭: Req=Request App=Approve Rej=Reject Ord=Order Chk=Check Rec=Receive')
    print('  상위 몇 개 변형이 대부분의 케이스를 덮는다. 이 "긴 꼬리" 구조가')
    print('  프로세스 마이닝에서 잡음 필터링이 통하는 이유다.\n')


def demo_dfg():
    print('■ 3. 직접후행 그래프 — 거의 모든 발견 알고리즘의 출발점')
    lg = L.generate(n_cases=500, seed=1)
    dfg = lg.dfg()
    acts = sorted(lg.activities())
    rows = [[''] + acts]
    for a in acts:
        rows.append([a] + ['%d' % dfg.get((a, b), 0) for b in acts])
    print(fmt.table(rows, align='l' + 'r' * len(acts)))
    print('  행 a, 열 b 의 값은 "a 바로 다음에 b 가 온 횟수"다. 로그를 한 번 훑으면')
    print('  얻어지므로 O(사건 수) 다.')
    print('  시작 활동: %s' % dict(lg.start_activities()))
    print('  종료 활동: %s' % dict(lg.end_activities()))
    print('  Order 와 Check 사이에 양방향 간선이 있는 것에 주목 — 병렬의 흔적이다.\n')


def demo_noise():
    print('■ 4. 기록이 불완전하면 무슨 일이 생기는가')
    rows = [['잡음 비율', '변형 수', '가장 흔한 변형의 비율', '1회만 나타난 변형 수']]
    for noise in (0.0, 0.05, 0.15, 0.30, 0.50):
        lg = L.generate(n_cases=500, seed=2, noise=noise)
        var = lg.variants()
        singles = sum(1 for c in var.values() if c == 1)
        top = max(var.values())
        rows.append(['%.0f%%' % (100 * noise), '%d' % len(var),
                     '%.1f%%' % (100.0 * top / 500), '%d' % singles])
    print(fmt.table(rows, align='rrrr'))
    print('  잡음이 늘면 변형 수가 폭발하고, 그중 40% 가량은 <한 번만> 나타난다.')
    print('  알파 알고리즘은 "한 번이라도 관측됐으면 참"으로 다루므로 여기서 무너진다.')
    print('  휴리스틱·인덕티브 마이너가 빈도를 보는 이유다.')


def main():
    demo_summary()
    demo_variants()
    demo_dfg()
    demo_noise()


if __name__ == '__main__':
    main()
