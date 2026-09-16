# -*- coding: utf-8 -*-
"""9부 — 행렬곱 세 차례와 스레드 (tfs bench).

**이 캡처만 시간을 잰다.** 그래서 세 번 돌리면 숫자가 달라지고,
tools/record.sh 의 md5 대조에서 빠진다. 덱은 이 표를 "이 기계에서
잰 한 번" 으로만 싣고, 산문에 속도 숫자를 옮겨 적지 않는다.
"""
from demo import crun, report


def main():
    text = crun.tfs('bench')
    sections, title, body = [], None, []
    for line in text.rstrip('\n').split('\n'):
        if line.startswith('== '):
            if title:
                sections.append((title, '\n'.join(body).strip('\n')))
            title = line.strip('= ').split('. ', 1)[1]
            body = []
        else:
            body.append(line)
    sections.append((title, '\n'.join(body).strip('\n')))
    return report.write('bench.txt', sections)


if __name__ == '__main__':
    print(main())
