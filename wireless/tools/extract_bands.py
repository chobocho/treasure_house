#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""규격 원문의 대역 표를 뽑아 data/bands.tsv 로 만든다.

    python3 tools/extract_bands.py            # specs/zips 의 규격에서
    python3 tools/extract_bands.py --check    # 지금 것과 같은지만 본다

왜 손으로 안 적는가: 대역의 위·아래 끝은 한 자리만 틀려도 티가 안 나고,
틀린 채로 실리면 독자가 그것을 옮겨 적는다. 그래서 TS 36.101 표 5.5-1
(E-UTRA)과 TS 38.101-1 표 5.2-1(NR FR1)·38.101-2 표 5.2-1(NR FR2)을
직접 열어 읽는다.

**각주 번호를 본문으로 읽지 않는 것** 이 이 도구의 요점이다. Word 에서
각주 표시는 위첨자 run 이라, 그냥 글자만 이어 붙이면 '대역 24, 각주 17'
이 '2417' 이 되어 버린다. 실제로 그렇게 나왔다가 잡았다.

시간 O(문서 크기). 문서 하나가 70 MB 쯤 되니 메모리를 확인하고 돌릴 것.
"""
import io
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
ZIPS = os.path.join(BASE, 'specs', 'zips')
OUT = os.path.join(BASE, 'data', 'bands.tsv')

RUN = re.compile(rb'<w:r[ >].*?</w:r>', re.S)
T_RE = re.compile(rb'<w:t(?:\s[^>]*)?>(.*?)</w:t>', re.S)
SUP = re.compile(rb'<w:vertAlign w:val="superscript"/>')
TBL = re.compile(rb'<w:tbl>.*?</w:tbl>', re.S)
TR = re.compile(rb'<w:tr[ >].*?</w:tr>', re.S)
TC = re.compile(rb'<w:tc>.*?</w:tc>', re.S)
MHZ = re.compile(r'([\d.]+)\s*MHz')

# 어느 규격의 어느 조각에서 어떤 표를 찾을지.
# 판본 글자(k00 등)는 규격이 고쳐질 때마다 바뀌므로 이름 전체를 적지
# 않고 앞머리만 적는다 — 새 판을 받아도 그대로 돈다. 조각 이름도
# 규격마다 다르다(38.101-2 는 한 덩어리다). 그래서 '들어 있으면 된다'
# 로 찾고, 못 찾으면 zip 안의 가장 큰 .docx 를 본다.
SOURCES = [
    ('36101-', 's00-07', 'E-UTRA', '4G(LTE)',
     '3GPP TS 36.101 표 5.5-1'),
    ('38101-1-', 's00-05', 'NR', '5G(NR FR1)',
     '3GPP TS 38.101-1 표 5.2-1'),
    ('38101-2-', 's00-05', 'NR', '5G(NR FR2)',
     '3GPP TS 38.101-2 표 5.2-1'),
]

# 널리 쓰이는 이름. 규격에 없는 칸이라 사람이 붙인 것임을
# 표 머리말에 적어 둔다.
NOTE = {
    ('4G(LTE)', 1): 'IMT 2100 — 3G·4G 의 주력 대역',
    ('4G(LTE)', 2): 'PCS 1900 (북미)',
    ('4G(LTE)', 3): 'DCS 1800 — GSM 1800 이 쓰던 대역',
    ('4G(LTE)', 4): 'AWS-1 (북미)',
    ('4G(LTE)', 5): '셀룰러 850 — AMPS·IS-95 가 쓰던 대역',
    ('4G(LTE)', 7): 'IMT-E 2600',
    ('4G(LTE)', 8): 'GSM 900',
    ('4G(LTE)', 12): '700 하위 (북미)',
    ('4G(LTE)', 13): '700 상위 C 블록 (북미)',
    ('4G(LTE)', 17): '700 B·C 블록 (북미)',
    ('4G(LTE)', 20): '800 디지털 배당 (유럽)',
    ('4G(LTE)', 25): '확장 PCS (북미)',
    ('4G(LTE)', 26): '확장 셀룰러 850 (북미)',
    ('4G(LTE)', 28): 'APT 700 — 한국 700 MHz 가 여기다',
    ('4G(LTE)', 34): '2000 TDD (중국)',
    ('4G(LTE)', 38): '2600 TDD',
    ('4G(LTE)', 39): '1900 TDD (중국)',
    ('4G(LTE)', 40): '2300 TDD — 한국 와이브로가 쓰던 대역',
    ('4G(LTE)', 41): '2500 TDD',
    ('4G(LTE)', 42): '3500 TDD',
    ('4G(LTE)', 46): '5 GHz 비면허 (LAA)',
    ('4G(LTE)', 48): 'CBRS 3550 (미국)',
    ('4G(LTE)', 66): 'AWS-3 확장 (북미)',
    ('4G(LTE)', 71): '600 (북미)',
    ('5G(NR FR1)', 1): 'IMT 2100',
    ('5G(NR FR1)', 3): 'DCS 1800',
    ('5G(NR FR1)', 5): '셀룰러 850',
    ('5G(NR FR1)', 7): 'IMT-E 2600',
    ('5G(NR FR1)', 8): 'GSM 900',
    ('5G(NR FR1)', 28): 'APT 700 — 한국 700 MHz',
    ('5G(NR FR1)', 41): '2500 TDD',
    ('5G(NR FR1)', 77): '3.3–4.2 GHz TDD — 한국 5G 의 주력',
    ('5G(NR FR1)', 78): '3.3–3.8 GHz TDD — 유럽·한국의 주력',
    ('5G(NR FR1)', 79): '4.4–5.0 GHz TDD (중국·일본)',
    ('5G(NR FR2)', 257): '28 GHz — 한국·미국·일본',
    ('5G(NR FR2)', 258): '26 GHz — 유럽',
    ('5G(NR FR2)', 260): '39 GHz (미국)',
    ('5G(NR FR2)', 261): '28 GHz 일부 (미국)',
}


def celltext(blob):
    """칸의 글.

    **위첨자 run 은 뺀다** — 그것은 각주 번호이지 값이 아니다.
    """
    parts = []
    for rm in RUN.finditer(blob):
        run = rm.group(0)
        if SUP.search(run):
            continue
        parts.append(b''.join(T_RE.findall(run)))
    s = b''.join(parts).decode('utf-8', 'replace')
    for a, c in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'),
                 ('&quot;', '"')):
        s = s.replace(a, c)
    return re.sub(r'\s+', ' ', s).strip()


def find_band_table(xml, kind):
    """동작 대역 본 표 하나를 고른다.

    "가장 긴 표" 로는 못 고른다 — 규격에는 'E-UTRA' 와 'operating band'
    가 함께 든 표가 수십 개 있고(반송파 집성 조합·V2X 짝 등), 그 가운데
    더 긴 것이 많다. 그래서 머리글이 네 칸을 모두 갖춘 표만 본다:
    UL 대역 · DL 대역 · 듀플렉스 모드, 그리고 첫 칸이 대역 번호.
    """
    best = None
    for m in TBL.finditer(xml):
        rows = []
        for rm in TR.finditer(m.group(0)):
            rows.append([celltext(c.group(0))
                         for c in TC.finditer(rm.group(0))])
        if not rows or len(rows[0]) != 4:
            continue
        head = ' '.join(rows[0]).lower()
        if ('uplink (ul) operating band' in head
                and 'downlink (dl) operating band' in head
                and 'duplex mode' in head
                and head.startswith(('eutra', 'e-utra', 'nr ',
                                     'operating band'))):
            if best is None or len(rows) > len(best):
                best = rows
    return best


def parse(rows, gen, source):
    out = []
    for r in rows[2:]:
        cells = [x.strip() for x in r]
        if not cells or not cells[0]:
            continue
        num = cells[0][1:] if cells[0][0] in 'nN' else cells[0]
        if not num.isdigit():
            continue
        nums = MHZ.findall(' | '.join(cells[1:]))
        if len(nums) == 4:
            ul = '%s-%s' % (nums[0], nums[1])
            dl = '%s-%s' % (nums[2], nums[3])
        elif len(nums) == 2:
            ul = dl = '%s-%s' % (nums[0], nums[1])
        else:
            continue
        band = int(num)
        out.append((str(band), ul, dl, cells[-1], gen,
                    NOTE.get((gen, band), ''), source))
    return out


def build():
    rows = []
    for prefix, part, kind, gen, source in SOURCES:
        names = sorted(n for n in os.listdir(ZIPS)
                       if n.startswith(prefix) and n.endswith('.zip')
                       and os.path.getsize(
                           os.path.join(ZIPS, n)) > 1024)
        if not names:
            sys.stderr.write('  건너뜀(파일 없음): %s*\n' % prefix)
            continue
        z = zipfile.ZipFile(os.path.join(ZIPS, names[-1]))
        docs = [n for n in z.namelist() if n.endswith('.docx')]
        inner = [n for n in docs if part in n]
        if not inner:
            inner = sorted(docs, key=lambda n: -z.getinfo(n).file_size)
        if not inner:
            sys.stderr.write('  조각을 못 찾음: %s\n' % names[-1])
            continue
        zz = zipfile.ZipFile(io.BytesIO(z.read(inner[0])))
        table = find_band_table(zz.read('word/document.xml'), kind)
        if not table:
            sys.stderr.write('  대역 표를 못 찾음: %s\n' % names[-1])
            continue
        got = parse(table, gen, source)
        sys.stderr.write('  %s → %d개\n' % (gen, len(got)))
        rows += got
    head = ('band\tul_mhz\tdl_mhz\tduplex\tgeneration\tnote\tsource\n')
    note = (
        '# 주파수 대역 색인 — tools/extract_bands.py 가 만든다.\n'
        '# 손으로 고치지 말 것.\n'
        '# band·ul_mhz·dl_mhz·duplex 는 규격 원문의 표에서 뽑았다\n'
        '# (TS 36.101 표 5.5-1 · TS 38.101-1/2 표 5.2-1, 단위 MHz).\n'
        '# note 칸만 사람이 붙인 흔한 이름이다 — 규격에 없는 칸이다.\n'
        '# 지시서의 region 칸 대신 duplex·note 를 두었다.\n'
        '# 규격에 없는 칸을 지어내지 않으려는 것이다.\n')
    return head + note + ''.join('\t'.join(r) + '\n' for r in rows)


def main(argv):
    text = build()
    if '--check' in argv:
        cur = ''
        if os.path.exists(OUT):
            cur = io.open(OUT, encoding='utf-8').read()
        if cur != text:
            print('  ✗ data/bands.tsv 가 규격 원문과 어긋난다')
            return 1
        print('대역 표 — 규격 원문과 같다')
        return 0
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(text)
    print('data/bands.tsv 를 다시 만들었다')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
