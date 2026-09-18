# -*- coding: utf-8 -*-
"""commit·tag 객체와 신원 줄 (SPEC.md §4.4 · §4.5 · §1.3 · §9.1).

커밋 = 트리 하나 + 부모 목록 + 누가·언제 + 메시지. 커밋의 이름에는
작성 시각과 시간대까지 들어가므로, 같은 트리라도 1초만 달라도 다른
커밋이다 — 그래서 mygit 은 시계를 읽지 않고 환경 변수만 믿는다.
"""
import re

from mygit import GitError

DAYS = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')
MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
          'Oct', 'Nov', 'Dec')
IDENT_RE = re.compile(r'^(.*) <(.*)> (-?\d+) ([+-]\d{4})$')
DATE_RE = re.compile(r'^(\d+) ([+-]\d{4})$')


def parse_ident(line):
    """'이름 <메일> 초 ±hhmm' → (이름, 메일, 초, 시간대)."""
    m = IDENT_RE.match(line)
    if not m:
        raise GitError('fatal: mygit: bad ident line: %s' % line)
    return m.group(1), m.group(2), int(m.group(3)), m.group(4)


def ident_from_env(env, who):
    """GIT_<who>_NAME·EMAIL·DATE → 신원 줄 (SPEC.md §1.3).

    설정 파일도 시계도 보지 않는다 — 없으면 멈춘다. 캡처가 세 번
    같으려면 입력이 전부 드러나 있어야 하기 때문이다.
    """
    vals = []
    for part in ('NAME', 'EMAIL', 'DATE'):
        key = 'GIT_%s_%s' % (who, part)
        if key not in env:
            raise GitError('fatal: mygit: %s is not set' % key)
        vals.append(env[key])
    if not DATE_RE.match(vals[2]):
        raise GitError("fatal: mygit: GIT_%s_DATE is not "
                       "'<seconds> <+hhmm>'" % who)
    return '%s <%s> %s' % tuple(vals)


def civil_from_days(z):
    """1970-01-01 부터의 날 수 → (해, 달, 일). Howard Hinnant 의
    그레고리력 공식 — 로캘도 표준 달력 함수도 쓰지 않는다. O(1)."""
    z += 719468
    era = (z if z >= 0 else z - 146096) // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + 3 if mp < 10 else mp - 9
    return (y + 1 if m <= 2 else y), m, d


def format_date(seconds, tz):
    """git log 의 Date 꼴 — 'Wed Nov 15 07:13:20 2023 +0900'.

    시각을 그 시간대로 옮겨 찍는다. 일은 앞에 0 을 붙이지 않는다.
    """
    sign = -1 if tz[0] == '-' else 1
    local = seconds + sign * (int(tz[1:3]) * 3600 + int(tz[3:5]) * 60)
    days, rest = divmod(local, 86400)
    y, m, d = civil_from_days(days)
    return '%s %s %d %02d:%02d:%02d %d %s' % (
        DAYS[(days + 4) % 7], MONTHS[m - 1], d, rest // 3600,
        rest // 60 % 60, rest % 60, y, tz)


def cleanup_message(text):
    """commit -m 의 공백 정리(git 의 cleanup=whitespace).

    줄마다 끝 공백을 지우고, 이어진 빈 줄은 하나로, 앞뒤의 빈 줄은
    지운다. 줄 앞의 공백은 남긴다. 남는 것이 없으면 ''.
    """
    out = []
    for line in text.split('\n'):
        line = line.rstrip()
        if line or (out and out[-1]):
            out.append(line)
    while out and not out[-1]:
        out.pop()
    return '\n'.join(out) + '\n' if out else ''


def subject_of(message):
    """제목 = 첫 문단의 줄들을 공백 하나로 이은 것(SPEC.md §4.4).

    줄 끝의 공백은 떼지만 **앞의 공백은 남긴다** — "  lead" 라는
    메시지의 제목은 "  lead" 다(진짜 git 의 commit 요약 줄로 확인,
    golden/scen/plumbing.scn). 빈 줄을 만나면 거기서 끝난다.
    """
    lines = []
    for line in message.split('\n'):
        if not line.strip():
            break
        lines.append(line.rstrip())
    return ' '.join(lines)


def parse_commit(body):
    """커밋 몸 → {tree, parents, author, committer, message}.

    모르는 머리 줄(gpgsig·mergetag 와 그 이어진 줄)은 건너뛴다.
    메시지는 UTF-8 로 읽되 깨진 바이트도 되돌릴 수 있게 둔다.
    """
    text = body.decode('utf-8', 'surrogateescape')
    head, _, message = text.partition('\n\n')
    c = {'tree': None, 'parents': [], 'author': None,
         'committer': None, 'message': message}
    for line in head.split('\n'):
        key, _, val = line.partition(' ')
        if key == 'tree':
            c['tree'] = val
        elif key == 'parent':
            c['parents'].append(val)
        elif key in ('author', 'committer'):
            c[key] = val
    if c['tree'] is None or c['committer'] is None:
        raise GitError('fatal: mygit: corrupt commit object')
    return c


def serialize_commit(tree, parents, author, committer, message):
    lines = ['tree ' + tree] + ['parent ' + p for p in parents]
    lines += ['author ' + author, 'committer ' + committer]
    text = '\n'.join(lines) + '\n\n' + message
    return text.encode('utf-8', 'surrogateescape')


def serialize_tag(obj, type_, name, tagger, message):
    text = ('object %s\ntype %s\ntag %s\ntagger %s\n\n%s'
            % (obj, type_, name, tagger, message))
    return text.encode('utf-8', 'surrogateescape')


def parse_tag(body):
    """태그 몸 → {object, type, tag, tagger, message}."""
    text = body.decode('utf-8', 'surrogateescape')
    head, _, message = text.partition('\n\n')
    t = {'message': message}
    for line in head.split('\n'):
        key, _, val = line.partition(' ')
        t[key] = val
    return t
