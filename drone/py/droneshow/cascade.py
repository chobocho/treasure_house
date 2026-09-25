# -*- coding: utf-8 -*-
"""cascade — 위치 P → 속도 PID → 추력 방향 → 자세 P → 각속도 PID → 믹서.

SPEC §5. 루프마다 도는 빠르기가 다르다: 각속도·자세 250 Hz, 위치
50 Hz, 물리 500 Hz. 안쪽 루프가 충분히 빨라야 바깥 루프가 안쪽을
'명령대로 곧장 되는 것' 으로 볼 수 있다(T17). 빠르기는 설정 한 칸이라
실패 실험(안쪽을 느리게)이 플래그 하나다.
"""
import math

from . import attitude as A
from . import mixer
from . import params as P
from . import pid
from . import vec3 as V

PHYS_HZ = 500


class Controller:
    def __init__(self, p, cfg=None):
        self.p = p = dict(p, **(cfg or {}))
        self.d = P.derived(p)
        self.div = {k: round(PHYS_HZ / p[k])
                    for k in ('rate_hz', 'att_hz', 'pos_hz')}
        for k, n in self.div.items():
            if n * p[k] != PHYS_HZ:
                raise ValueError('%s 는 500 의 약수여야 한다' % k)
        kv = [p['kp_vel']] * 3, [p['ki_vel']] * 3, [p['kd_vel']] * 3
        self.vel = pid.VecPID(*kv, i_max=p['i_max_vel'],
                              tau_d=p['tau_d_vel'])
        kr = [p['kp_rate']] * 3, [p['ki_rate']] * 3, [p['kd_rate']] * 3
        self.rate = pid.VecPID(*kr, i_max=p['i_max_rate'],
                               tau_d=p['tau_d_rate'])
        self.k_att = [p['k_att_xy'], p['k_att_xy'], p['k_att_z']]
        self.f_des = [0.0, 0.0, p['m'] * p['g']]
        self.q_d = [1.0, 0.0, 0.0, 0.0]
        self.w_sp = [0.0, 0.0, 0.0]
        self.w_ff = [0.0, 0.0, 0.0]
        self.cmd = [self.d['omega_hover']] * 4
        self.log = {}

    def position(self, s, ref):
        """위치·속도 루프 → 원하는 추력 벡터와 자세 (SPEC §5.2–5.3)."""
        p, dt = self.p, self.div['pos_hz'] / PHYS_HZ
        e = V.sub(ref['p'], s[0:3])
        vsp = V.add(V.scale(e, p['kp_pos']), ref.get('v', [0.0] * 3))
        n = V.norm(vsp)
        if n > p['vmax_ctrl']:
            vsp = V.scale(vsp, p['vmax_ctrl'] / n)
        asp = V.add(self.vel.update(vsp, s[3:6], dt),
                    ref.get('a', [0.0] * 3))
        f = V.scale([asp[0], asp[1], asp[2] + p['g']], p['m'])
        f[2] = max(f[2], 0.1 * p['m'] * p['g'])     # 뒤집혀 밀지 않는다
        lim = math.tan(math.radians(p['tilt_max_deg'])) * f[2]
        h = math.sqrt(f[0] * f[0] + f[1] * f[1])
        if h > lim:
            f[0], f[1] = f[0] * lim / h, f[1] * lim / h
        self.f_des = f
        self.q_d = A.desired_attitude(f, ref.get('yaw', 0.0))
        # 가가속도(jerk)가 주어지면 평탄성으로 몸체 각속도를 앞먹임(T12)
        if 'j' in ref:
            self.w_ff = A.flat_rates(ref.get('a', [0.0] * 3), ref['j'],
                                     ref.get('yaw', 0.0),
                                     ref.get('yaw_rate', 0.0), p['g'])
        else:
            self.w_ff = [0.0, 0.0, 0.0]
        self.log.update(v_sp=vsp, a_sp=asp)

    def attitude(self, s):
        w = A.att_law(s[6:10], self.q_d, self.k_att, self.p['yaw_w'])
        w = V.add(w, self.w_ff)
        lim = self.p['rate_max']
        self.w_sp = [max(-lim, min(lim, x)) for x in w]

    def rates(self, s):
        """각속도 PID → 토크, 총추력은 f_des 를 지금의 몸체 z 에
        투영."""
        p, dt = self.p, self.div['rate_hz'] / PHYS_HZ
        alpha = self.rate.update(self.w_sp, s[10:13], dt)
        tau = [p['Jxx'] * alpha[0], p['Jyy'] * alpha[1],
               p['Jzz'] * alpha[2]]
        from .quat import rotate
        zb = rotate(s[6:10], [0.0, 0.0, 1.0])
        u = [max(0.0, V.dot(self.f_des, zb))] + tau
        t, flags = mixer.allocate(p, u, self.d['T_min'],
                                  self.d['T_max'])
        self.cmd = [min(p['omega_max'], max(p['omega_min'],
                                            math.sqrt(x / p['kT'])))
                    for x in t]
        self.log.update(u=u, flags=flags)

    def update(self, k, s, ref):
        """물리 걸음 번호 k 에서 부른다. 모터 명령 넷을 돌려준다."""
        if k % self.div['pos_hz'] == 0:
            self.position(s, ref)
        if k % self.div['att_hz'] == 0:
            self.attitude(s)
        if k % self.div['rate_hz'] == 0:
            self.rates(s)
        return self.cmd
