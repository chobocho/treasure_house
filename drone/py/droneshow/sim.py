# -*- coding: utf-8 -*-
"""sim — 제어기와 물리를 묶어 한 대를 날린다 (SPEC §4–§5).

기록은 매 10걸음(50 Hz)마다 한 줄 — 걸음마다 남기면 메모리를 먹고,
그래프·표에는 50 Hz 면 충분하다.
"""
from . import cascade
from . import quadrotor as QR

DT = 1.0 / cascade.PHYS_HZ


def fly(p, ref, secs, start=(0.0, 0.0, 0.0), cfg=None, wind=None,
        every=10, state=None):
    """ref(t) → {'p', 'v'?, 'a'?, 'yaw'?} 를 secs 초 동안 따라 난다.

    반환: [{'t', 's', 'cmd'}] (every 걸음마다). wind(t) 는 바람이 미는
    힘[N]. state 를 주면 그 상태에서 시작한다."""
    ctl = cascade.Controller(p, cfg)
    s = list(state) if state else QR.hover_state(p, start)
    rows = []
    zero = (0.0, 0.0, 0.0)
    for k in range(round(secs / DT)):
        t = k * DT
        cmd = ctl.update(k, s, ref(t))
        s = QR.step(ctl.p, s, cmd, DT, wind(t) if wind else zero)
        if (k + 1) % every == 0:
            rows.append({'t': (k + 1) * DT, 's': s, 'cmd': list(cmd)})
    return rows
