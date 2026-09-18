# -*- coding: utf-8 -*-
"""deb.py — .deb 한 개를 dpkg 없이 연다.

    python3 py/deb.py FILE.deb …

.deb 는 특별한 형식이 아니다. `ar` 묶음 안에 멤버가 셋 있다.
  debian-binary   형식 판 "2.0"
  control.tar.*   control(이름·판·의존·설명)과 설치 전후 스크립트
  data.tar.*      설치될 파일들 — 경로 그대로. Termux 패키지면
                  ./data/data/com.termux/files/usr/… 로 시작한다.
6부는 이 사실을 손으로 확인한다. 이 도구가 그 손이다.

압축은 없음·gz·xz·bz2 를 연다(파이썬 tarfile 이 아는 것). zst 는
표준 라이브러리에 없어 이름만 알려 주고 멈춘다 — 조용히 틀린 답을
내는 것보다 낫다.

시간 O(파일 크기). 한 번 읽어 메모리에서 푼다.
"""
import io
import sys
import tarfile
import unicodedata

COMP = {'': '', '.gz': 'gz', '.xz': 'xz', '.bz2': 'bz2'}


def ar_members(data):
    """[(이름, 바이트)]. ar 머리는 60바이트, 몸통은 짝수로 맞춘다."""
    if not data.startswith(b'!<arch>\n'):
        raise ValueError('ar 묶음이 아니다(.deb 가 아니다)')
    out, at = [], 8
    while at < len(data):
        head = data[at:at + 60]
        if len(head) < 60 or head[58:60] != b'`\n':
            raise ValueError('ar 머리가 망가졌다 (%d 바이트째)' % at)
        name = head[:16].decode('ascii').strip().rstrip('/')
        size = int(head[48:58].decode('ascii').strip())
        body = data[at + 60:at + 60 + size]
        if len(body) < size:
            raise ValueError('ar 멤버 %s 가 잘렸다' % name)
        out.append((name, body))
        at += 60 + size + (size % 2)
    return out


def _tar(name, body):
    ext = name[name.index('.tar') + 4:]
    if ext not in COMP:
        raise ValueError('%s: %s 압축은 표준 라이브러리로 못 연다'
                         % (name, ext.lstrip('.') or '?'))
    return tarfile.open(fileobj=io.BytesIO(body),
                        mode='r:' + COMP[ext])


def parse_control(text):
    """control 필드 → dict. 이어지는 줄은 들여쓰기, 빈 줄은 ' .'."""
    out, key = {}, None
    for line in text.split('\n'):
        if not line.strip():
            continue
        if line[0] in ' \t' and key:
            part = line.strip()
            out[key] += '\n' + ('' if part == '.' else part)
        elif ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            out[key] = val.strip()
    return out


def read(path):
    """{format, members[(이름, 크기)], control{}, files[]}."""
    with open(path, 'rb') as f:
        members = ar_members(f.read())
    info = {'format': None,
            'members': [(n, len(b)) for n, b in members],
            'control': None, 'files': []}
    for name, body in members:
        if name == 'debian-binary':
            info['format'] = body.decode('ascii').strip()
        elif name.startswith('control.tar'):
            with _tar(name, body) as t:
                for m in t.getmembers():
                    if m.name.lstrip('./') == 'control':
                        text = t.extractfile(m).read().decode('utf-8')
                        info['control'] = parse_control(text)
        elif name.startswith('data.tar'):
            with _tar(name, body) as t:
                info['files'] = sorted(
                    '/' + m.name.lstrip('./') for m in t.getmembers()
                    if not m.isdir())
    if info['control'] is None:
        raise ValueError('control 이 없다 — .deb 가 아니다')
    return info


def clip(s, width=72):
    """칸 수로 자른다 — 한글은 두 칸이라 글자 수로 자르면 넘친다."""
    out, n = '', 0
    for ch in s:
        w = 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
        if n + w > width:
            break
        out += ch
        n += w
    return out


def report(path, info):
    """덱에 싣는 모양. 한 줄 72칸 안."""
    out = [path, '  멤버:']
    for n, size in info['members']:
        out.append('    %-18s %8d 바이트' % (n, size))
    out.append('  control:')
    for k, v in info['control'].items():
        first = v.split('\n')[0]
        out.append(clip('    %s: %s' % (k, first)))
    out.append('  파일 %d개:' % len(info['files']))
    for f in info['files'][:8]:
        out.append(clip('    ' + f))
    return '\n'.join(out)


def main(argv):
    if not argv:
        print('사용법: deb.py FILE.deb …')
        return 2
    rc = 0
    for p in argv:
        try:
            print(report(p, read(p)))
        except (OSError, ValueError) as err:
            print('%s: %s' % (p, err))
            rc = 1
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
