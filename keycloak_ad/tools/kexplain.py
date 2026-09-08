#!/usr/bin/env python3
"""필드 하나가 무엇인지 규격에서 직접 읽어 온다.

    kexplain.py deployment spec.replicas
    kexplain.py service     spec.type
    kexplain.py ingress                  # 최상위 필드 목록

`kubectl explain` 이 하는 일과 같다. 다른 점은 **서버가 필요 없다**는
것이다 — kubectl 은 클러스터에 물어보는데(1.3x 부터는 오프라인으로 안
된다), 여기서는 쿠버네티스가 공개한 JSON 스키마를 그대로 읽는다.
그래서 클러스터가 없는 이 덱에서도 필드 설명이 진짜 규격에서 나온다.

스키마는 bin/schemas/ 에 있다 (tools/fetch_k8s_tools.sh 가 받아 둔다).
"""
import json
import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMAS = os.path.join(os.path.dirname(HERE), 'bin', 'schemas')

# 덱이 쓰는 종류만. 파일 이름은 kubernetes-json-schema 의 규칙 그대로다.
KINDS = {
    'namespace': 'namespace-v1.json',
    'deployment': 'deployment-apps-v1.json',
    'service': 'service-v1.json',
    'ingress': 'ingress-networking-v1.json',
    'configmap': 'configmap-v1.json',
    'secret': 'secret-v1.json',
    'pod': 'pod-v1.json',
}

WIDTH = 72


def load(kind):
    name = KINDS.get(kind.lower())
    if name is None:
        sys.exit('모르는 종류: %s (아는 것: %s)'
                 % (kind, ' '.join(sorted(KINDS))))
    path = os.path.join(SCHEMAS, name)
    if not os.path.exists(path):
        sys.exit('스키마가 없다: %s\n'
                 '  sh tools/fetch_k8s_tools.sh 를 먼저 돌릴 것' % path)
    return json.load(open(path, encoding='utf-8'))


def walk(node, path):
    """점으로 이어진 경로를 따라 내려간다. 배열은 items 를 지나친다."""
    for step in path:
        while 'items' in node and 'properties' not in node:
            node = node['items']
        props = node.get('properties')
        if not props or step not in props:
            sys.exit('그런 필드가 없다: %s' % step)
        node = props[step]
    return node


def typename(node):
    t = node.get('type', '')
    if isinstance(t, list):
        t = [x for x in t if x != 'null']
        t = t[0] if t else ''
    if t == 'array':
        inner = node.get('items', {})
        return '[]%s' % (typename(inner) or 'object')
    return t or 'object'


def show(kind, dotted):
    root = load(kind)
    path = [p for p in dotted.split('.') if p]
    node = walk(root, path)
    where = kind.upper() + ('.' + dotted if dotted else '')

    print('필드:  %s' % where)
    print('종류:  %s' % typename(node))
    desc = node.get('description', '')
    if desc:
        print('설명:')
        for line in textwrap.wrap(desc, WIDTH - 2):
            print('  ' + line)

    while 'items' in node and 'properties' not in node:
        node = node['items']
    props = node.get('properties')
    if props:
        need = set(node.get('required', []))
        print('하위 필드:')
        for name in sorted(props):
            mark = '*' if name in need else ' '
            print('  %s %-24s %s' % (mark, name, typename(props[name])))
        if need:
            print('  (* 는 반드시 적어야 하는 것)')


if __name__ == '__main__':
    if not 2 <= len(sys.argv) <= 3:
        sys.exit(__doc__)
    show(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else '')
