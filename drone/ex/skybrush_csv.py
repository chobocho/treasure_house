# -*- coding: utf-8 -*-
"""12부 — 우리 쇼 파일을 드론별 CSV 묶음(zip)으로.

    python3 ex/skybrush_csv.py out/show_p16_60.json scratch/show.zip

Skybrush Studio 문서는 드론마다 CSV 하나를 zip 에 담아 가져오는
형식을 "Time_msec, x_m, y_m, z_m, Red, Green, Blue" 줄로 적고, 색은
선형 색 공간이라고 가정한다고 적는다. 우리 쇼 파일의 색은 감마로
부호화된 8비트 값이다(L22) — 그대로 넣으면 중간 밝기가 밝게 해석된다.
그래서 여기서 빛의 양으로 바꿔(0–255 로 다시 늘려) 적는다.

문서가 말하지 않는 것 — 머리줄이 있어야 하는지, 색 값의 범위가
0–255 인지 0–1 인지 — 은 확인하지 못했다. 이 파일은 머리줄을 쓰고
0–255 를 쓴다. 실제 가져오기 전에 도구에서 한 번 확인할 것.
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import render as R  # noqa: E402
from droneshow import show as SH  # noqa: E402

HEADER = 'Time_msec,x_m,y_m,z_m,Red,Green,Blue'
# zip 안 파일의 시각 — 고정해 두어야 같은 쇼가 같은 바이트가 된다
STAMP = (1980, 1, 1, 0, 0, 0)


def linear(v):
    """감마 부호 값 v(0–255) → 선형 빛의 양을 0–255 로. v 이하다."""
    return SH.rnd(255.0 * R.decode(v))


def rows(show, d):
    """드론 한 대의 줄들 — fps 마다 한 줄, 첫 줄은 머리줄."""
    out = [HEADER]
    for f in range(round(show['duration'] * show['fps']) + 1):
        t = f / show['fps']
        x = SH.position(show, d, t)
        c = SH.colour(show, d, t)
        out.append('%d,%.3f,%.3f,%.3f,%d,%d,%d'
                   % (SH.rnd(t * 1000), x[0], x[1], x[2],
                      linear(c[0]), linear(c[1]), linear(c[2])))
    return out


def write_zip(show, path):
    """드론마다 drone_NNN.csv — 번호는 쇼 파일의 id."""
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for d in show['drones']:
            info = zipfile.ZipInfo('drone_%03d.csv' % d['id'], STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, '\n'.join(rows(show, d)) + '\n')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    with open(argv[0], encoding='utf-8') as f:
        show = SH.loads(f.read())
    write_zip(show, argv[1])
    print('%s — CSV %d개' % (argv[1], len(show['drones'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
