# -*- coding: utf-8 -*-
"""12부 — 제작 툴. 우리 쇼를 다른 도구로 넘기는 길을 캡처한다."""
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ex'))
import skybrush_csv as K  # noqa: E402
from droneshow import show as SH  # noqa: E402

ENV = {'PYTHONPATH': 'py'}
SHOW = 'scratch/p12_show.json'


def run(ctx):
    os.makedirs('scratch', exist_ok=True)
    ctx.py('p12_plan', 'ex/lab_show.py', '12', '-o', SHOW)
    ctx.py('p12_zip', 'ex/skybrush_csv.py', SHOW, 'scratch/p12.zip')
    ctx.py('p12_list', '-m', 'zipfile', '-l', 'scratch/p12.zip')
    # 같은 드론, 같은 순간 — 우리 CSV(감마 부호)와 Skybrush 용(선형)
    with open(SHOW, encoding='utf-8') as f:
        s = SH.loads(f.read())
    d = s['drones'][0]
    heart = [m for m in s['scenes'] if m['name'] == 'heart'][0]
    f = round(heart['t0'] * s['fps'])
    ours = SH.csv_rows(s, d)
    theirs = K.rows(s, d)
    with zipfile.ZipFile('scratch/p12.zip') as z:
        inzip = z.read('drone_000.csv').decode('utf-8').split('\n')
    ctx.text('p12_compare', '\n'.join([
        '드론 0, 하트 장면 시작 %.2f초 (프레임 %d)' % (heart['t0'], f),
        '우리 CSV      ' + ours[0], '              ' + ours[f + 1],
        'Skybrush 용   ' + theirs[0], '              ' + theirs[f + 1],
        'zip 안의 같은 줄과 같다: %s'
        % (inzip[f + 1] == theirs[f + 1])]))
    ctx.text('p12_show_head', json.dumps(
        {k: s[k] for k in ('format', 'fps', 'dmin', 'profile',
                           'duration')}, ensure_ascii=False))
