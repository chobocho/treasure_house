# -*- coding: utf-8 -*-
"""elf.py — 실행 파일이 누구를 부르는지 읽는다 (작은 readelf).

    python3 py/elf.py FILE …

5부의 질문은 하나다: 같은 `bash` 인데 Termux 의 것과 우분투의 것은
무엇이 다른가. 답은 ELF 머리의 몇 칸에 있다.
  interp  — PT_INTERP. 커널이 이 파일을 싣기 전에 먼저 부르는 링커.
            bionic 이면 /system/bin/linker64, glibc 면 ld-linux-*.so.
  needed  — DT_NEEDED. 링커가 찾아 붙일 공유 라이브러리 이름.
  runpath — DT_RUNPATH(옛것은 DT_RPATH). 라이브러리를 먼저 찾을 곳.
Termux 패키지는 $PREFIX/lib 을 여기 박아 둔다(6부).

readelf 가 없는 곳(Termux 기본 설치)에서도 돌도록 표준 라이브러리만
쓴다. 섹션 표는 보지 않고 프로그램 머리(program header)만 본다 —
링커가 보는 것도 그것이기 때문이다. 문자열 표의 가상 주소는
PT_LOAD 로 파일 위치로 바꾼다.

시간 O(프로그램 머리 수 + 동적 항목 수). 파일 전체를 한 번 읽는다.
"""
import struct
import sys

MACHINES = {3: 'x86', 8: 'MIPS', 20: 'PowerPC', 21: 'PowerPC64',
            40: 'ARM', 62: 'x86-64', 183: 'AArch64', 243: 'RISC-V'}
TYPES = {1: 'REL', 2: 'EXEC', 3: 'DYN', 4: 'CORE'}
PT_LOAD, PT_DYNAMIC, PT_INTERP = 1, 2, 3
DT_NULL, DT_NEEDED, DT_STRTAB = 0, 1, 5
DT_SONAME, DT_RPATH, DT_RUNPATH = 14, 15, 29


def _unpack(fmt, data, off):
    size = struct.calcsize(fmt)
    if off < 0 or off + size > len(data):
        raise ValueError('ELF 가 잘렸다 (%d 바이트째)' % off)
    return struct.unpack_from(fmt, data, off)


def _cstr(data, off):
    if off < 0 or off >= len(data):
        raise ValueError('문자열 위치가 파일 밖이다')
    end = data.find(b'\0', off)
    if end < 0:
        raise ValueError('문자열이 끝나지 않는다')
    return data[off:end].decode('utf-8', 'replace')


def read(path):
    """{class, endian, machine, type, interp, needed, runpath, rpath,
    soname}. ELF 가 아니거나 잘렸으면 ValueError."""
    with open(path, 'rb') as f:
        data = f.read()
    if len(data) < 16 or data[:4] != b'\x7fELF':
        raise ValueError('ELF 가 아니다: %s' % path)
    bits = {1: 32, 2: 64}.get(data[4])
    e = {1: '<', 2: '>'}.get(data[5])
    if not bits or not e:
        raise ValueError('ELF 머리의 클래스·엔디언을 모른다')
    if bits == 64:
        (etype, mach, _v, _entry, phoff, _sh, _fl, _eh, phentsize,
         phnum) = _unpack(e + 'HHIQQQIHHH', data, 16)
        phfmt = e + 'IIQQQQQQ'
    else:
        (etype, mach, _v, _entry, phoff, _sh, _fl, _eh, phentsize,
         phnum) = _unpack(e + 'HHIIIIIHHH', data, 16)
        phfmt = e + 'IIIIIIII'
    loads, interp, dyn = [], None, None
    for i in range(phnum):
        p = _unpack(phfmt, data, phoff + i * phentsize)
        if bits == 64:
            typ, _flags, off, vaddr, _pa, filesz = p[:6]
        else:
            typ, off, vaddr, _pa, filesz = p[:5]
        if typ == PT_LOAD:
            loads.append((vaddr, off, filesz))
        elif typ == PT_INTERP:
            interp = _cstr(data, off)
        elif typ == PT_DYNAMIC:
            dyn = (off, filesz)
    info = {'class': 'ELF%d' % bits,
            'endian': 'LSB' if e == '<' else 'MSB',
            'machine': MACHINES.get(mach, str(mach)),
            'type': TYPES.get(etype, str(etype)),
            'interp': interp, 'needed': [], 'runpath': None,
            'rpath': None, 'soname': None}
    if not dyn:
        return info
    word = e + ('qQ' if bits == 64 else 'iI')
    step = struct.calcsize(word)
    entries, strtab = [], None
    for k in range(dyn[1] // step):
        tag, val = _unpack(word, data, dyn[0] + k * step)
        if tag == DT_NULL:
            break
        if tag == DT_STRTAB:
            strtab = val
        entries.append((tag, val))
    if strtab is None:
        raise ValueError('동적 항목에 DT_STRTAB 가 없다')
    # 문자열 표는 가상 주소로 적혀 있다 — 싣는 구간(PT_LOAD)으로
    # 파일 위치를 찾는다
    base = None
    for vaddr, off, size in loads:
        if vaddr <= strtab < vaddr + size:
            base = off + (strtab - vaddr)
            break
    if base is None:
        raise ValueError('DT_STRTAB 주소가 어느 PT_LOAD 에도 없다')
    for tag, val in entries:
        if tag == DT_NEEDED:
            info['needed'].append(_cstr(data, base + val))
        elif tag == DT_RUNPATH:
            info['runpath'] = _cstr(data, base + val)
        elif tag == DT_RPATH:
            info['rpath'] = _cstr(data, base + val)
        elif tag == DT_SONAME:
            info['soname'] = _cstr(data, base + val)
    return info


def report(path, info):
    """덱에 싣는 모양. 한 줄 72칸 안에서 needed 를 접는다."""
    out = [path,
           '  %s %s · %s · %s' % (info['class'], info['endian'],
                                  info['machine'], info['type']),
           '  interp: %s' % (info['interp'] or '(없음 — 정적 또는 공유 '
                                               '라이브러리)')]
    line = '  needed:'
    for n in info['needed'] or ['(없음)']:
        if len(line) + 1 + len(n) > 72:
            out.append(line)
            line = '         '
        line += ' ' + n
    out.append(line)
    for k in ('runpath', 'rpath', 'soname'):
        if info[k]:
            out.append('  %s: %s' % (k, info[k]))
    return '\n'.join(out)


def main(argv):
    if not argv:
        print('사용법: elf.py FILE …')
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
