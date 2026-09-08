#!/usr/bin/env python3
"""합친 매니페스트에서 한 종류만 골라 낸다.

    kubectl kustomize … | pickobj.py Deployment

kustomize 가 내놓는 것은 --- 로 이어 붙인 문서 여러 개다. 통째로는
백 줄이 넘어 한 화면에 안 들어가므로, 덱에 실을 때는 종류별로 나눈다.

주석은 사라진다. kustomize 가 YAML 을 다시 써 내면서 버리기 때문인데,
그래서 덱은 **원본 파일**을 인용해 설명하고 이쪽은 결과만 보인다.
"""
import sys


def main(kind):
    docs = sys.stdin.read().split('\n---\n')
    out = [d.rstrip('\n') for d in docs
           if any(l == 'kind: ' + kind for l in d.split('\n'))]
    if not out:
        sys.exit('%s 가 없다' % kind)
    print('\n---\n'.join(out))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
