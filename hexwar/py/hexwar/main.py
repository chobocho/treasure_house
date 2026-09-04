# -*- coding: utf-8 -*-
"""명령줄 진입점 — 세 언어 구현이 모두 같은 하위 명령을 가진다.

    python3 -m hexwar.main trace            골든 트레이스를 표준출력으로
    python3 -m hexwar.main render out.ppm   한 프레임을 PPM 으로
    python3 -m hexwar.main bench            간단한 성능 측정
"""

import io
import json
import os
import sys
import time

from . import ai
from . import scenario
from .game import Game
from .render import Renderer
from .rng import fnv1a
from .ui import Ui

GOLDEN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'golden')


def load_script(path=None):
    path = path or os.path.join(GOLDEN, 'script.txt')
    evs = []
    for raw in io.open(path, encoding='utf-8'):
        line = raw.strip()
        if line and not line.startswith(';'):
            evs.append(line)
    return evs


def digest_state(g, ui, r=None, with_frame=False):
    d = {
        'state': ui.state_name(),
        'sel': ui.sel_unit,
        'turn': g.turn,
        'side': g.side,
        'rng': g.rng.save(),
        'unitHash': '%08x' % fnv1a(g.serialize_units().encode('utf-8')),
        'fogHash': '%08x' % fnv1a(g.map.fog_text().encode('utf-8')),
        'ui': ui.digest(),
    }
    if with_frame and r is not None:
        r.draw(g, ui)
        d['fbHash'] = '%08x' % fnv1a(r.fb.to_ppm(r.pal))
    return d


def run_trace(out=sys.stdout, render_frames=True):
    m, pool, obj = scenario.load()
    g = Game(m, pool, obj)
    ui = Ui(g)
    r = Renderer() if render_frames else None
    lines = []
    for n, ev in enumerate(load_script()):
        if ev == 'ai':
            ai.take_turn(g)
            g.end_turn()
            ui.after_turn()
        else:
            ui.handle(ev)
        d = digest_state(g, ui, r, with_frame=(ev == 'render'))
        d['step'] = n
        d['ev'] = ev
        lines.append(json.dumps(d, sort_keys=True, separators=(',', ':')))
    text = '\n'.join(lines) + '\n'
    out.write(text)
    return text


def run_render(path, step=None):
    """스크립트를 step 번째까지 재생한 뒤 한 프레임을 PPM 으로 굽는다."""
    m, pool, obj = scenario.load()
    g = Game(m, pool, obj)
    ui = Ui(g)
    r = Renderer()
    evs = load_script()
    limit = len(evs) if step is None else min(step, len(evs))
    for ev in evs[:limit]:
        if ev == 'ai':
            ai.take_turn(g)
            g.end_turn()
            ui.after_turn()
        else:
            ui.handle(ev)
    r.draw(g, ui)
    data = r.fb.to_ppm(r.pal)
    io.open(path, 'wb').write(data)
    sys.stderr.write('%s · %d바이트 · FNV %08x\n' % (path, len(data), fnv1a(data)))
    return fnv1a(data)


def run_bench():
    from . import path as P
    m, pool, obj = scenario.load()
    g = Game(m, pool, obj)
    u = next(iter(g.pool.iter_alive(0)))
    t0 = time.time()
    n = 2000
    for _ in range(n):
        P.reachable(g.map, g.pool, u)
    t1 = time.time()
    r = Renderer()
    ui = Ui(g)
    t2 = time.time()
    for _ in range(20):
        r.draw(g, ui)
    t3 = time.time()
    print('reachable %d회 %.3f초 (%.1f us/회)' % (n, t1 - t0, (t1 - t0) * 1e6 / n))
    print('draw 20프레임 %.3f초 (%.1f ms/프레임)' % (t3 - t2, (t3 - t2) * 1000 / 20))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else 'trace'
    if cmd == 'trace':
        run_trace()
    elif cmd == 'render':
        run_render(argv[2] if len(argv) > 2 else 'frame.ppm',
                   int(argv[3]) if len(argv) > 3 else None)
    elif cmd == 'bench':
        run_bench()
    else:
        sys.stderr.write('사용법: trace | render <파일> [스텝] | bench\n')
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
