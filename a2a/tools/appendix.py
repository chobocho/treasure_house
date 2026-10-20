#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""appendix — 부록(18부)의 필드 사전과 찾아보기 자료를 만든다.

   손으로 옮긴 필드 표는 proto 와 어긋나고, 손으로 적은 찾아보기는 조각이 바뀔 때마다
   낡는다. 그래서 make deck 이 조립 전에 이것을 돌려 둘을 다시 만든다.

     deck/fields.tsv   docs/spec/specification/a2a.proto → 블록(서비스·메시지·enum)마다
                       머리 행 하나 + 항목(rpc·필드·값) 행. <!--FIELDS--> 가 읽는다.
                       docs/ 는 커밋하지 않으므로 proto 가 없으면 있던 파일을 그대로 둔다.
     deck/index.tsv    fields.tsv 의 이름 + deck/index_extra.tsv(오류·머리글 이름)를
                       deck/order.txt 의 조각에서 찾아, 이름마다 처음 나온 슬라이드 셋.
                       deck/proto_where.tsv(이름 → 가르치는 슬라이드)가 있으면 그것이 먼저.
                       <!--INDEX--> 가 읽는다.

     python3 tools/appendix.py           두 파일을 쓴다
     python3 tools/appendix.py --check   다시 만들면 달라지는가 — 낡았으면 종료 코드 1

   찾는 단위는 산문의 <code>이름</code> 하나 통째다(Task.id 처럼 붙은 것은 세지 않는다).
   O(조각 글자 수 + proto 줄 수) — 한 번씩 훑는다.
"""
import html
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTO = os.path.join('docs', 'spec', 'specification', 'a2a.proto')
FIELDS = os.path.join('deck', 'fields.tsv')
INDEX = os.path.join('deck', 'index.tsv')
EXTRA = os.path.join('deck', 'index_extra.tsv')
WHERE = os.path.join('deck', 'proto_where.tsv')

HEAD = ['block', 'kind', 'name', 'json', 'type', 'num', 'rule', 'oneof', 'comment']
# 표 한 칸에 두 줄 남짓 — 접힌 폴드에서 행 하나가 화면을 다 먹지 않을 길이.
MAX_COMMENT = 110
KEEP = 3                    # 찾아보기 한 줄에 싣는 슬라이드 수
APPENDIX_PART = 18          # 부록 자신은 찾아보기에 넣지 않는다(제 표가 모든 이름을 가진다)

BLOCK = re.compile(r'^(service|message|enum)\s+(\w+)\s*\{')
RPC = re.compile(r'^rpc\s+(\w+)\s*\(\s*(\w+)\s*\)\s*returns\s*\(\s*(stream\s+)?([\w.]+)\s*\)')
FIELD = re.compile(r'^(repeated\s+|optional\s+)?(map<[^>]+>|[\w.]+)\s+(\w+)\s*=\s*(\d+)\s*(\[[^\]]*\])?\s*;')
VALUE = re.compile(r'^([A-Z][A-Z0-9_]*)\s*=\s*(\d+)\s*;')
ONEOF = re.compile(r'^oneof\s+(\w+)\s*\{')
MDLINK = re.compile(r'\[([^\]]+)\]\([^)]*\)')
ARTICLE = re.compile(r'<article\b([^>]*)>(.*?)</article>', re.S)
CODE = re.compile(r'<code>(.*?)</code>', re.S)
KIND = {'message': '메시지', 'enum': 'enum', 'rpc': '메서드', 'field': '필드', 'value': 'enum 값'}


def read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def json_name(name):
    """proto 필드 이름 → ProtoJSON 이름(lowerCamel). context_id → contextId."""
    head, *rest = name.split('_')
    return head + ''.join(w[:1].upper() + w[1:] for w in rest)


def one_line(lines):
    """주석 줄들 → 첫 문장 하나. 'Optional.'·'Required.' 머리말은 규칙 칸이 말하므로 뺀다."""
    text = ' '.join(ln.strip() for ln in lines if ln.strip())
    text = MDLINK.sub(r'\1', text)
    text = re.sub(r'^(Optional|Required)\.\s*', '', text)
    # "e.g." 의 마침표는 문장의 끝이 아니다.
    m = re.search(r'(?<!e\.g)(?<!i\.e)\.(\s|$)', text)
    if m:
        text = text[:m.start() + 1]
    if len(text) > MAX_COMMENT:
        text = text[:MAX_COMMENT - 1].rstrip() + '…'
    return text


def parse_proto(text):
    """proto 본문 → [{kind, name, comment, items:[{name, json, type, num, rule, oneof, comment}]}].

       a2a.proto 의 모양만 다룬다: 맨 위 블록 안에 한 줄짜리 필드·값·rpc, oneof 한 겹.
       (-- … --) 은 린터 지시라 주석이 아니고, protolint: 줄도 버린다.
    """
    blocks, cur, comment = [], None, []
    depth, oneof, in_linter = 0, '', False
    for raw in text.split('\n'):
        line = raw.strip()
        if line.startswith('//'):
            body = line[2:].strip()
            if in_linter or body.startswith('(--'):
                in_linter = not body.endswith('--)')
                continue
            if not body.startswith('protolint:'):
                comment.append(body)
            continue
        if not line:
            if cur is None:
                comment = []
            continue
        if cur is None:
            m = BLOCK.match(line)
            if m:
                cur = {'kind': m.group(1), 'name': m.group(2), 'comment': one_line(comment), 'items': []}
                blocks.append(cur)
                depth = 1
            comment = []
            continue
        if depth == 1:
            m = RPC.match(line)
            if m and cur['kind'] == 'service':
                cur['items'].append(item(m.group(1), '%s → %s%s' % (m.group(2), m.group(3) or '', m.group(4)),
                                         '', '', '', comment))
            m2 = ONEOF.match(line)
            if m2:
                oneof = m2.group(1)
                comment = []
                depth += 1
                continue
        if depth <= 2 and cur['kind'] != 'service':
            m = FIELD.match(line) if cur['kind'] == 'message' else VALUE.match(line)
            if m and cur['kind'] == 'message':
                label, typ, name, num, opts = m.groups()
                typ = typ.replace('google.protobuf.', '')
                rule = ('REQUIRED' if 'REQUIRED' in (opts or '') else
                        'DEPRECATED' if 'deprecated = true' in (opts or '') else '')
                cur['items'].append(item(name, (label or '') + typ, num, rule, oneof if depth == 2 else '', comment))
            elif m:
                cur['items'].append(item(m.group(1), '', m.group(2), '', '', comment))
        depth += line.count('{') - line.count('}')
        if depth == 1:
            oneof = ''
        if depth == 0:
            cur = None
        comment = []
    return blocks


def item(name, typ, num, rule, oneof, comment):
    return {'name': name, 'json': json_name(name),
            'type': re.sub(r'\s+', ' ', typ).strip(), 'num': num, 'rule': rule, 'oneof': oneof,
            'comment': one_line(comment)}


def field_rows(blocks):
    """블록들 → TSV 행(첫 행은 HEAD). 블록마다 머리 행 하나, 그 아래 항목 행."""
    rows = [list(HEAD)]
    sub = {'service': 'rpc', 'message': 'field', 'enum': 'value'}
    for b in blocks:
        rows.append([b['name'], b['kind'], '', '', '', '', '', '', b['comment']])
        for it in b['items']:
            rows.append([b['name'], sub[b['kind']], it['name'],
                         it['json'] if b['kind'] == 'message' else it['name'],
                         it['type'], it['num'], it['rule'], it['oneof'], it['comment']])
    return rows


def tsv_text(rows):
    return ''.join('\t'.join(re.sub(r'[\t\n]', ' ', c) for c in r) + '\n' for r in rows)


def tsv_rows(path):
    """머리 행을 뺀 TSV 행들. # 줄·빈 줄은 건너뛴다. 파일이 없으면 []."""
    if not os.path.isfile(path):
        return []
    lines = [ln for ln in read(path).split('\n') if ln and not ln.startswith('#')]
    return [ln.split('\t') for ln in lines[1:]]


def vocabulary(rows, extra):
    """찾아볼 이름 → 종류. 필드는 와이어 이름(JSON)으로 찾는다. extra 가 이긴다."""
    v = {}
    for r in rows[1:] if rows and rows[0] == HEAD else rows:
        block, kind, name, json = r[0], r[1], r[2], r[3]
        if kind in ('message', 'enum'):
            v[block] = KIND[kind]
        elif kind in KIND:
            v[json] = KIND[kind]
    for r in extra:
        v[r[0]] = r[1]
    return v


def scan(sections, vocab, keep=KEEP, pin=None):
    """[(조각 이름, 본문)] → {이름: [슬라이드 id …]}. 처음 나온 차례로 keep 개까지.

       pin(이름 → id)은 그 이름을 가르치는 슬라이드라 맨 앞에 둔다(vocab 에 있는 이름만).
    """
    found = {}
    for name, sid in (pin or {}).items():
        if name in vocab:
            found[name] = [sid]
    for fname, text in sections:
        if int(fname[:2]) == APPENDIX_PART:
            continue
        for m in ARTICLE.finditer(text):
            idm = re.search(r'\bid="([^"]+)"', m.group(1))
            if not idm:
                continue
            sid = idm.group(1)
            for c in CODE.findall(m.group(2)):
                word = html.unescape(c).strip().strip('"')
                if word not in vocab:
                    continue
                got = found.setdefault(word, [])
                if sid not in got and len(got) < keep:
                    got.append(sid)
    return found


def build(root):
    """→ {상대 경로: 새 내용}. proto 가 없으면 fields.tsv 는 있던 내용 그대로."""
    out = {}
    proto = os.path.join(root, PROTO)
    if os.path.isfile(proto):
        rows = field_rows(parse_proto(read(proto)))
        out[FIELDS] = tsv_text(rows)
    else:
        old = os.path.join(root, FIELDS)
        rows = [list(HEAD)] + tsv_rows(old)
        if os.path.isfile(old):
            out[FIELDS] = read(old)
    vocab = vocabulary(rows, tsv_rows(os.path.join(root, EXTRA)))
    pin = {r[0]: r[1] for r in tsv_rows(os.path.join(root, WHERE)) if len(r) > 1 and r[1]}
    order = [ln.strip() for ln in read(os.path.join(root, 'deck', 'order.txt')).split('\n')
             if ln.strip() and not ln.startswith('#')]
    secs = [(f, read(os.path.join(root, 'deck', 'sections', f))) for f in order
            if os.path.isfile(os.path.join(root, 'deck', 'sections', f))]
    found = scan(secs, vocab, KEEP, pin)
    # 대소문자를 가리지 않는 abc 차례, 같으면 대문자 먼저 — 책의 찾아보기 차례.
    names = sorted(found, key=lambda s: (s.lower(), s))
    out[INDEX] = tsv_text([['ident', 'kind', 'where']] +
                          [[n, vocab[n], ','.join(found[n])] for n in names])
    return out


def main(argv=None, root=None):
    argv = sys.argv[1:] if argv is None else argv
    root = root or ROOT
    out = build(root)
    stale = [rel for rel, text in sorted(out.items())
             if not os.path.isfile(os.path.join(root, rel)) or read(os.path.join(root, rel)) != text]
    if '--check' in argv:
        for rel in stale:
            print('  ✗ 낡았다: %s (python3 tools/appendix.py)' % rel)
        return 1 if stale else 0
    for rel in stale:
        with io.open(os.path.join(root, rel), 'w', encoding='utf-8', newline='') as f:
            f.write(out[rel])
    if not os.path.isfile(os.path.join(root, PROTO)):
        print('  ! %s 가 없다 — %s 는 있던 그대로 (make docs)' % (PROTO, FIELDS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
