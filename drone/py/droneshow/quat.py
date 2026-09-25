# -*- coding: utf-8 -*-
"""quat — 단위 쿼터니언과 회전 (SPEC §1.5–1.6, 정리 T4–T7).

쿼터니언은 [w, x, y, z] (스칼라가 앞), 해밀턴 곱이다. q 는 몸체 좌표를
세계 좌표로 돌린다: v_세계 = q ⊗ (0, v_몸체) ⊗ q*. 회전행렬 R(q) 의
열은 세계 좌표로 적은 몸체의 세 축이다.
"""
import math

from . import vec3 as V


def mul(a, b):
    """해밀턴 곱 a ⊗ b. 교환법칙이 없다."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return [aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw]


def conj(q):
    return [q[0], -q[1], -q[2], -q[3]]


def norm(q):
    return math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2]
                     + q[3] * q[3])


def normalize(q):
    n = norm(q)
    return [q[0] / n, q[1] / n, q[2] / n, q[3] / n]


def inv(q):
    """단위 쿼터니언이면 켤레와 같다. 일반형은 켤레 / |q|²."""
    n2 = q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]
    return [q[0] / n2, -q[1] / n2, -q[2] / n2, -q[3] / n2]


def canonical(q):
    """q 와 −q 는 같은 회전이다(T6). w ≥ 0 인 쪽을 대표로 고른다."""
    return list(q) if q[0] >= 0 else [-q[0], -q[1], -q[2], -q[3]]


def rotate(q, v):
    """q ⊗ (0, v) ⊗ q* 의 벡터 부분."""
    return mul(mul(q, [0.0, v[0], v[1], v[2]]), conj(q))[1:]


def to_matrix(q):
    """R(q) — 단위 쿼터니언을 가정한다."""
    w, x, y, z = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z),
             2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z),
             2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x),
             1 - 2 * (x * x + y * y)]]


def from_matrix(m):
    """셰퍼드 방법 — w², x², y², z² 가운데 가장 큰 것으로 나눈다.

    대각합만 쓰는 공식은 회전각이 π 에 가까우면 0 에 가까운 수로
    나누게 되어 자릿수를 잃는다. 넷 중 가장 큰 성분을 먼저 구하면
    나누는 수가 늘 0.5 이상이다."""
    t = m[0][0] + m[1][1] + m[2][2]
    cand = [t, m[0][0], m[1][1], m[2][2]]
    k = cand.index(max(cand))
    if k == 0:
        s = 2.0 * math.sqrt(1.0 + t)
        q = [s / 4, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s,
             (m[1][0] - m[0][1]) / s]
    elif k == 1:
        s = 2.0 * math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2])
        q = [(m[2][1] - m[1][2]) / s, s / 4, (m[0][1] + m[1][0]) / s,
             (m[0][2] + m[2][0]) / s]
    elif k == 2:
        s = 2.0 * math.sqrt(1.0 - m[0][0] + m[1][1] - m[2][2])
        q = [(m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s, s / 4,
             (m[1][2] + m[2][1]) / s]
    else:
        s = 2.0 * math.sqrt(1.0 - m[0][0] - m[1][1] + m[2][2])
        q = [(m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s,
             (m[1][2] + m[2][1]) / s, s / 4]
    return normalize(q)


def from_axis_angle(axis, angle):
    a = V.normalize(axis)
    s = math.sin(angle / 2)
    return [math.cos(angle / 2), a[0] * s, a[1] * s, a[2] * s]


def to_axis_angle(q):
    """(단위 축, 각 ∈ [0, π]). 각이 0 이면 축은 x 로 정한다."""
    q = canonical(q)
    s = math.sqrt(q[1] * q[1] + q[2] * q[2] + q[3] * q[3])
    if s < 1e-15:
        return [1.0, 0.0, 0.0], 0.0
    return [q[1] / s, q[2] / s, q[3] / s], 2 * math.atan2(s, q[0])


def from_two_vectors(a, b):
    """단위 벡터 a 를 b 로 보내는 가장 짧은 회전.

    (1 + a·b, a × b) 를 정규화하면 반각 공식이 된다. a 와 b 가
    정반대면 그 식이 0 이 되므로 a 에 수직인 아무 축으로 π 돈다."""
    d = V.dot(a, b)
    if d < -1.0 + 1e-12:
        axis = V.cross(a, [1.0, 0.0, 0.0])
        if V.norm(axis) < 1e-6:
            axis = V.cross(a, [0.0, 1.0, 0.0])
        return from_axis_angle(axis, math.pi)
    c = V.cross(a, b)
    return normalize([1.0 + d, c[0], c[1], c[2]])


# ------------------------------------ 오일러각 (ZYX: 요·피치·롤)
def from_euler(roll, pitch, yaw):
    """R = Rz(요) · Ry(피치) · Rx(롤) 에 해당하는 쿼터니언."""
    qx = from_axis_angle([1.0, 0.0, 0.0], roll)
    qy = from_axis_angle([0.0, 1.0, 0.0], pitch)
    qz = from_axis_angle([0.0, 0.0, 1.0], yaw)
    return mul(qz, mul(qy, qx))


def to_euler(q):
    """[롤, 피치, 요]. 피치 ±90° 에서는 롤과 요가 갈리지 않는다(T5)."""
    w, x, y, z = q
    sp = max(-1.0, min(1.0, 2 * (w * y - z * x)))
    return [math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)),
            math.asin(sp),
            math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))]


def euler_rate_matrix(roll, pitch):
    """E — 오일러각의 변화율을 몸체 각속도로: ω = E · (φ̇, θ̇, ψ̇).

    행렬식이 cos(피치) 라서 피치 ±90° 에서 E 는 거꾸로 풀 수 없다.
    그것이 짐벌 락이다(T5)."""
    sr, cr = math.sin(roll), math.cos(roll)
    sp, cp = math.sin(pitch), math.cos(pitch)
    return [[1.0, 0.0, -sp], [0.0, cr, sr * cp], [0.0, -sr, cr * cp]]


# ------------------------------------------------------- 운동학 (T7)
def qdot(q, w):
    """q̇ = ½ q ⊗ (0, ω) — ω 는 몸체 좌표의 각속도."""
    p = mul(q, [0.0, w[0], w[1], w[2]])
    return [0.5 * c for c in p]


def step_euler(q, w, dt):
    """오일러 한 걸음. 노름이 √(1 + (dt|ω|/2)²) 로 커진다 — T7."""
    d = qdot(q, w)
    return [q[i] + dt * d[i] for i in range(4)]
