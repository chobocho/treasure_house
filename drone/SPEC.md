# droneshow — the simulator specification both languages implement

> Audience: whoever writes or tests `py/droneshow/` and `js/droneshow.js`. English, like
> PLAN.md. Every number here that has a reason lives in `data/params.tsv` (the reference
> quadrotor) and is quoted, never retyped, by the deck. Test suites cite the section numbers
> of this file (`SPEC §4.2`). When this file and a test disagree, the test is wrong or this
> file is — fix one of them in the same commit; never loosen an assertion.

---

## 1. Conventions

1. **Units** — SI throughout: m, s, kg, N, N·m, rad, rad/s. Angles on slides may be printed
   in degrees; code never stores degrees.
2. **World frame ENU** — `x` east, `y` north, `z` up; gravity is `−g·e3` with `g = 9.81`.
   Shows are designed in this frame because "up" is where the audience looks. PX4 uses NED
   (`x` north, `y` east, `z` down); the conversion is `x_ned = y_enu, y_ned = x_enu,
   z_ned = −z_enu` (a proper rotation composed with a reflection is *not* allowed — this map
   is a rotation by π about the axis `(1,1,0)/√2`, det +1). The deck proves that in 8부.
3. **Body frame FLU** — `x` forward, `y` left, `z` up (thrust direction). PX4's FRD differs
   by a rotation of π about `x`.
4. **Vectors** are 3-element sequences (`list`/`tuple` in Python, `Array` in JS). No classes
   for vectors: functions `add, sub, scale, dot, cross, norm, normalize` in `vec3`.
5. **Quaternions** are `[w, x, y, z]`, scalar first, Hamilton product, representing the
   rotation from body to world: `v_world = q ⊗ (0, v_body) ⊗ q*`. The rotation matrix
   `R(q)` has columns = body axes expressed in the world frame.
6. **Canonical form** — `canonical(q)` returns `q` if `w ≥ 0` else `−q` (`q` and `−q` are
   the same rotation; T6).
7. **Rounding for output** — every float that leaves the simulator (golden JSON, show JSON,
   capture text) goes through `r9(x) = round(x, 9)` in Python and
   `Math.round(x * 1e9) / 1e9` in JS, and `-0.0` is printed as `0.0`. Capture text uses
   `%.6f` unless a module states otherwise.
8. **Determinism** — no wall clock, no `random` module, no `Math.random()`, no dict/set
   iteration order in output (sort by id). Everything random draws from §2.

## 2. Random numbers — xorshift128 (32-bit)

Both languages implement Marsaglia's xorshift128 on four 32-bit words (deviation from
PLAN.md §5 step 3, which said xorshift128+: the "+" variant needs 64-bit integers, which JS
only has as BigInt — too slow for per-step noise; the 32-bit generator uses only operations
JS does natively). Reference: G. Marsaglia, "Xorshift RNGs", J. Stat. Softw. 8(14), 2003.

```
state (x, y, z, w) = (123456789, 362436069, 521288629, 88675123)
seed(s):  x ^= s & 0xffffffff;  discard 16 outputs   (y, z, w stay non-zero,
          so the all-zero state that would stick at 0 cannot occur)
next():   t = x ^ ((x << 11) & 0xffffffff)
          x, y, z = y, z, w
          w = w ^ (w >> 19) ^ t ^ (t >> 8)       (all unsigned 32-bit)
          return w
uniform() = next() / 2^32                        in [0, 1)
normal()  = Box–Muller: u1 = 1 − uniform(), u2 = uniform(),
            return sqrt(−2 ln u1) · cos(2π u2)   (one value per two draws; no caching)
```

Golden vector `rng.json`: the first 20 `next()` outputs for seeds 0, 1, 7, 2026 must match
exactly (integers). `normal()` matches to 1e-9 (log/cos may differ in the last ulp).

## 3. The reference quadrotor (`data/params.tsv`)

| name | value | unit | note |
|---|---|---|---|
| `m` | 0.5 | kg | mass |
| `g` | 9.81 | m/s² | |
| `L` | 0.12 | m | centre to rotor axis |
| `Jxx`,`Jyy`,`Jzz` | 2.3e-3, 2.3e-3, 4.0e-3 | kg·m² | diagonal inertia |
| `kT` | 1.2e-6 | N/(rad/s)² | thrust per rotor `T = kT·Ω²` |
| `kQ` | 1.24e-8 | N·m/(rad/s)² | reaction torque `Q = kQ·Ω²`; chosen so that 4·kQ·Ω_h³ ≈ momentum-theory power / `fm` |
| `tau_m` | 0.03 | s | motor first-order lag |
| `omega_min`,`omega_max` | 200, 2000 | rad/s | motor speed limits |
| `c_drag` | 0.08 | N/(m/s) | linear translational drag |
| `rho` | 1.225 | kg/m³ | air density (sea level) |
| `r_prop` | 0.0635 | m | propeller radius (5-inch) |
| `fm` | 0.6 | – | figure of merit (momentum theory → real rotor) |
| `eta_e` | 0.8 | – | motor + ESC efficiency |
| `batt_V`, `batt_Ah`, `batt_use` | 14.8, 1.5, 0.8 | V, Ah, – | 4S pack, usable fraction |
| `led_W` | 1.0 | W | LED module power |
| `dmin` | 1.5 | m | minimum drone spacing in a show |
| `vmax`,`amax` | 3.0, 2.0 | m/s, m/s² | show motion limits |

Derived (computed in code, printed by captures, never typed on slides): hover thrust per
rotor `m g / 4`, hover speed `Ω_h = √(m g / (4 kT))`, thrust-to-weight
`4 kT Ω_max² / (m g)`, `a = L/√2`, `c = kQ/kT`.

## 4. Dynamics (`rigidbody`, `motor`, `mixer`, `quadrotor`)

### 4.1 Rotor layout (X configuration)

Rotor `i = 1..4` sits at angle `45° + 90°(i−1)` counter-clockwise from body `x`:
`r1 = (a, a, 0)` front-left, `r2 = (−a, a, 0)` rear-left, `r3 = (−a, −a, 0)` rear-right,
`r4 = (a, −a, 0)` front-right, `a = L/√2`. Spin `s = (+1, −1, +1, −1)` where `+1` means the
rotor spins counter-clockwise seen from above (angular velocity `+z`). The body receives the
reaction torque `−s_i·kQ·Ω_i²·e3`. (This numbering is ours; the deck shows PX4's.)

### 4.2 Mixer

`u = (F, τx, τy, τz)ᵀ = M·(T1, T2, T3, T4)ᵀ` with

```
M = [  1    1    1    1 ]
    [  a    a   −a   −a ]        τ = Σ r_i × (0, 0, T_i)
    [ −a    a    a   −a ]
    [ −c    c   −c    c ]        c = kQ / kT
```

Rows are mutually orthogonal, so `M·Mᵀ = diag(4, 4a², 4a², 4c²)`, `det M = 16 a² c` and
`M⁻¹ = Mᵀ·diag(1/4, 1/(4a²), 1/(4a²), 1/(4c²))` (T9).

**Desaturation** (`mixer.allocate(u, Tmin, Tmax)`): (1) `T = M⁻¹u`; if every
`Tmin ≤ T_i ≤ Tmax`, done. (2) Scale `τz` by the largest `k ∈ [0, 1]` (bisection, 30
iterations) that keeps `T` inside the limits, or 0 if none does. (3) If still outside, shift
all four by the same `δ` (collective) so that the spread fits: `δ = Tmin − min T` if
`min T < Tmin`, else `δ = Tmax − max T`. (4) Clamp each `T_i`. Priority is therefore roll/
pitch > collective > yaw, the order PX4 and ArduPilot document (CITE in 9부). Returns `T`
and a flag set `{yaw_scaled, shifted, clamped}`.

### 4.3 Equations of motion

State `X = (p, v, q, ω, Ω1..Ω4)` (17 numbers).

```
ṗ = v
v̇ = (1/m)·(R(q)·(0, 0, ΣT_i) − c_drag·v + f_wind) − g·e3
q̇ = ½ · q ⊗ (0, ω)
ω̇ = J⁻¹·(τ − ω × (J ω))            τ from §4.2 with T_i = kT Ω_i²
Ω̇_i = (Ω_cmd,i − Ω_i) / tau_m       Ω_cmd clamped to [omega_min, omega_max]
```

### 4.4 Integration

Fixed-step RK4 with `dt = 0.002 s` on all 17 numbers; inputs (`Ω_cmd`, wind) are held
constant over a step. After each step `q ← q / |q|` (T7). `rigidbody.rk4(f, x, dt)` is
generic (a list of floats in, a list out) so the tests can use it on `x' = a x` and on the
torque-free tumble (T8 witness).

### 4.5 Wind (optional, off by default)

Ornstein–Uhlenbeck per axis: `w ← w + (−w/T_w)·dt_c + σ_w·√(2 dt_c/T_w)·normal()` at the
controller rate, `f_wind = k_w·w`. Parameters in the run config, not params.tsv.

## 5. Control (`pid`, `attitude`, `cascade`)

Rates: position loop 50 Hz, attitude 250 Hz, rate loop 250 Hz (physics 500 Hz). Every rate
is a run-config field (`rate_hz`, `att_hz`, `pos_hz`) so a failure experiment is one flag.
Loops run when `step % (500 / hz) == 0`; `500 / hz` must be an integer.

### 5.1 PID (`pid.PID`)

`u = kp·e + ki·I + kd·D`, with `I += e·dt` clamped to `±i_max`, and the derivative taken on
the measurement (`D = −(y − y_prev)/dt`, low-passed by a first-order filter with time
constant `tau_d`: `D_f += (D − D_f)·dt/(tau_d + dt)`). First call: `D = 0`. Vector PIDs
apply the scalar PID per axis. `reset()` zeroes `I`, `D_f` and forgets `y_prev`.

### 5.2 Position → thrust vector

```
v_sp = kp_pos·(p_ref − p) + v_ff              |v_sp| clamped to vmax_ctrl
a_sp = PID_vel(v_sp − v; measurement v) + a_ff
f_des = m·(a_sp + g·e3)
tilt: if angle(f_des, e3) > tilt_max, keep f_des·e3 and scale the horizontal part down
F = f_des · (R(q)·e3)                           collective thrust along current body z
```

### 5.3 Desired attitude from thrust vector and yaw (differential flatness, T12)

```
z_d = f_des / |f_des|
x_c = (cos ψ_d, sin ψ_d, 0)
y_d = normalize(z_d × x_c);  x_d = y_d × z_d
R_d = [x_d y_d z_d] → q_d  (Shepperd's method: branch on the largest of w², x², y², z²)
```

### 5.4 Attitude P law (T18, T19) — PX4 structure

```
e_z = R(q)·e3;  e_z_d = R(q_d)·e3
q_red = shortest-arc quaternion taking e_z to e_z_d  (world frame), then q_red ⊗ q
        (if e_z and e_z_d are antiparallel within 1e-5: q_red = q_d)
q_mix = canonical(q_red⁻¹ ⊗ q_d);  clamp q_mix.w, q_mix.z to [−1, 1]
q_d'  = q_red ⊗ (cos(yaw_w·acos(q_mix.w)), 0, 0, sin(yaw_w·asin(q_mix.z)))
q_e   = q⁻¹ ⊗ q_d'
ω_sp  = k_att ∘ (2 · canonical(q_e).xyz)       per-axis gains, clamped to rate_max
```

With `yaw_w = 1` this is exactly `ω_sp = 2k·sign(q_e,w)·q_e,xyz`, the law proved in T18.

### 5.5 Rate loop

`τ_cmd = J·PID_rate(ω_sp − ω; measurement ω)` per axis (the `J` factor makes the gains
dimensionless in angular acceleration; the gyroscopic term is not fed forward).

### 5.6 Gains (`data/params.tsv`, rows `k_*`)

| loop | gains |
|---|---|
| position P | `kp_pos = 1.2` |
| velocity PID | `kp_vel = 3.0, ki_vel = 0.6, kd_vel = 0.05, i_max_vel = 2.0, tau_d_vel = 0.02` |
| attitude P | `k_att = (8, 8, 4)`, `yaw_w = 0.4`, `rate_max = 6` rad/s |
| rate PID | `kp_rate = 18, ki_rate = 4, kd_rate = 0.4, i_max_rate = 1.0, tau_d_rate = 0.005` |
| limits | `tilt_max = 35°`, `vmax_ctrl = 5 m/s` |

The rate loop's bandwidth (`kp_rate`) is ~2× the attitude gain and the attitude gain ~7×
the position gain (time-scale separation, T17). Experiment `p09_timescale` breaks it on
purpose by lowering `kp_rate` to a quarter of `k_att_xy`; lowering only the *sample rate* of
the rate and attitude loops to 50 Hz does **not** break it (measured in
`test_cascade.TimeScale` — PLAN.md §3.3 expected otherwise; the slide follows the
measurement).

A jerk feed-forward (`ref['j']` → body rates by T12's `flat_rates`) is available but does
not reduce the circle-tracking error of `test_cascade.FeedForward` while drag is unmodelled
by the controller; the 9부 table shows the four feed-forward levels as measured.

## 6. Sensors and estimation (`sensors`, `estimator`) — optional path `--sensors`

Sensor models at 250 Hz (gyro, accelerometer), 50 Hz (barometer), 10 Hz (GNSS):

```
gyro  = ω + b_g + σ_g·n        b_g constant per run (drawn once, σ_bg)
accel = Rᵀ·(v̇ + g·e3) + σ_a·n   (specific force in body frame)
baro  = p_z + σ_b·n
gnss  = p + σ_p·n               (each axis)
```

Estimators: (1) `complementary_1d(theta, gyro_rate, acc_angle, alpha, dt)` — the T23
one-axis filter; (2) `Complementary` — attitude quaternion: integrate gyro, correct tilt
toward the accelerometer's gravity direction with gain `k_c`; (3) `kalman_1d_gain(P, R)` =
`P/(P+R)` (T24) and `Kalman1D` (constant-velocity model, scalar measurement); (4) `KalmanCV`
— per-axis position/velocity filter with accelerometer input and GNSS/baro updates.
Noise parameters are run-config fields; defaults in `data/params.tsv` (`sigma_*`).

## 7. Trajectories (`poly`, `profile`)

1. `poly.rest_to_rest(n)` — the normalised rest-to-rest polynomial `β(u)`, `u ∈ [0,1]`,
   degree `2n−1` with `β(0)=0, β(1)=1` and derivatives 1..n−1 zero at both ends:
   `n=3` min-jerk `10u³ − 15u⁴ + 6u⁵`; `n=4` min-snap `35u⁴ − 84u⁵ + 70u⁶ − 20u⁷`.
2. `poly.min_snap(waypoints, times)` — per axis, `N` segments of degree 7; unknowns 8N;
   constraints: start and end position + zero velocity/acceleration/jerk (8), interior
   waypoint positions from both sides (2 each) and continuity of derivatives 1..6 (6 each);
   solved by Gaussian elimination with partial pivoting on the 8N×8N system (N ≤ 12).
   Segment time scaled to local `t ∈ [0, T_k]`. Returns coefficients `c[k][0..7]`
   (ascending powers). T27: this is the unique minimiser of `∫ (x⁗)² dt`.
3. `profile.trapezoid(d, vmax, amax)` — minimum-time rest-to-rest profile over distance
   `d`: triangular if `d < vmax²/amax`, else trapezoidal (T28). Returns `(T, t_acc, v_peak)`
   and `sample(t) → (s, v, a)`.
4. `profile.beta_trap(u, r)` — normalised trapezoid with ramp fraction `r ∈ (0, ½]`,
   `v̂ = 1/(1−r)`: `v̂u²/(2r)` for `u ≤ r`, `v̂(u − r/2)` in the middle,
   `1 − v̂(1−u)²/(2r)` for `u ≥ 1−r`.

## 8. Formations, assignment, collision (`formation`, `assign`, `collide`)

- Formation generators return a list of `n` points `[x, y, z]` (ENU, metres), centred at
  the origin in `x`, bottom at `z = z0` unless stated, and must respect `dmin` (tests):
  `grid(n, spacing, plane)`, `circle(n, radius)`, `rings(n, radius, layers, dz)`,
  `sphere(n, radius)` (Fibonacci lattice), `heart(n, size)` (parametric
  `x = 16 sin³t, z = 13 cos t − 5 cos 2t − 2 cos 3t − cos 4t`, resampled to equal arc
  length), `globe(n, radius, meridians, parallels)`, `text(s, pitch)` (built-in 5×7 font,
  `#` = drone), `image(pgm_text, n, dmin, seed)` (threshold → Poisson-disk thinning with
  seeded dart throwing → Lloyd relaxation, 10 iterations, on the bright pixels),
  `digit(d, pitch)` (countdown). The plane of 2-D formations is `x–z` (facing the audience
  on the `−y` side) unless `plane='xy'`.
- `assign.hungarian(cost)` — O(n³) Kuhn–Munkres with potentials; returns
  `(perm, total, ops)` where `ops` counts inner-loop relaxations (operation count, not time).
  `assign.brute(cost)` for `n ≤ 7`. `assign.cost_matrix(A, B, squared=True)`.
- `collide.min_distance(points)` — spatial hash with cell `dmin`, O(n) expected; returns
  `(dmin_found, i, j)`. `collide.check_transition(A, B, perm, beta, samples)` samples the
  synchronised straight-line motion `x_i(u) = (1−β(u))·a_i + β(u)·b_perm(i)` and returns the
  global minimum distance and where. `collide.crossings(A, B, perm)` counts pairs whose
  straight segments pass within `dmin` of each other in the formation plane (T30 witness).

## 9. Shows (`show`, `render`, `cli`)

### 9.1 Show file (JSON)

```
{ "format": "droneshow/1", "fps": 25, "dmin": 1.5, "seed": 7,
  "profile": {"kind": "trapezoid", "ramp": 0.25},     or {"kind": "minsnap"}
  "scenes": [{"name": "heart", "t0": 0.0, "t1": 8.0}, …],
  "drones": [ {"id": 0, "keyframes": [[t, x, y, z, r, g, b], …]}, … ] }
```

Keyframes are sorted by `t`; positions in metres (ENU), colours 0..255 integers. Between
keyframes `k` and `k+1` the position is `p_k + β(u)·(p_{k+1} − p_k)`, `u = (t−t_k)/(t_{k+1}−t_k)`,
with `β` from `profile` — **the same β for every drone**, so a transition is synchronised
straight-line motion and CAPT's guarantee applies (T31). A keyframe may carry an optional
8th element, the kind of the segment that *starts* there: `"T"` trapezoid (with the show's
`ramp`), `"S"` min-snap, `"J"` min-jerk, `"L"` linear (used by the rotation and wave
tricks, sampled densely). A drone may carry `"lights": [[t, r, g, b], …]`; if present, its
colour comes from the lights track (linear in time) instead of the keyframes — tricks that
change light without changing motion (dark moves, LED-only motion) edit only this track. Colours interpolate linearly in
the stored (gamma-encoded) values unless `"color": "linear-light"` is given, in which case
they are decoded with γ = 2.2, interpolated, and re-encoded (T34).

### 9.2 CSV export

One file per drone `drone_<id>.csv`, header `Time [msec],x [m],y [m],z [m],Red,Green,Blue`
(verify against Skybrush Studio docs before the deck claims compatibility — PLAN.md §3.3),
sampled at `fps`.

### 9.3 Planner (`show.plan`)

Input: a list of scenes `(formation_points, hold_seconds, rgb or per-drone rgb)`. For each
transition: Hungarian assignment on squared distances, duration
`T = max(d_max·β'_max/vmax, √(d_max·β''_max/amax))` rounded up to 1/fps, keyframes at the
start and end. Tricks are functions that transform a plan: `dark_move`,
`stagger_takeoff`, `layered_depth`, `rotate_volume`, `wave`, `led_only_motion`,
`dither_gradient`.

### 9.4 Run modes

- `kinematic` — positions are the show file's interpolated positions (≤ 500 drones).
- `physics` — each drone is a §4 quadrotor with the §5 controller tracking the show
  trajectory with feed-forward `v_ff`, `a_ff` from the analytic β derivatives (≤ 20 drones).
  Output: tracking table (max/mean position error per drone) and minimum distance.

### 9.5 Renderer

`render.snapshot_svg(show, frame, view)` → `<svg class="show" viewBox="0 0 340 H">` with a
dark background, each drone a small circle in its LED colour with a larger translucent halo
(additive look), views `front` (x–z), `top` (x–y), `audience` (perspective from
`(0, −D, h)` looking at the formation centre, T33). Deterministic text (fixed `%.2f`
coordinates, drones drawn in id order). `render.png(show, frame, w, h, view)` → PNG bytes
(RGB, zlib level 9, additive splats) for scratch viewing.

### 9.6 CLI (`python3 -m droneshow …`)

`plan SPEC.json -o show.json` · `info show.json` · `csv show.json DIR` ·
`svg show.json FRAME [--view V]` · `fly show.json --mode physics|kinematic --seed 7`.

## 10. Golden vectors (`golden/*.json`, written by `py/tests/write_golden.py`)

| file | content | tolerance |
|---|---|---|
| `rng.json` | first 20 `next()` for seeds 0,1,7,2026; 10 `normal()` for seed 7 | exact / 1e-9 |
| `quat.json` | 20 cases: `q1⊗q2`, `rotate(q, v)`, `to_matrix`, `from_matrix`, `from_axis_angle` | 1e-9 |
| `mixer.json` | `M`, `M⁻¹` for params; 10 allocate cases incl. saturation flags | 1e-9 |
| `hover.json` | hover Ω, thrust per rotor, thrust-to-weight | 1e-9 |
| `pid.json` | 3 PID step sequences (50 steps) incl. clamp and filter | 1e-9 |
| `physics.json` | 3-drone physics run: states at t = 0.5, 1, 2, 5 s | 1e-9 |
| `poly.json` | min-snap coefficients for 3 waypoint sets; β samples | 1e-9 |
| `assign.json` | Hungarian assignments for 6 point sets (n = 5…50), totals | exact perm / 1e-9 |
| `profile.json` | trapezoid samples | 1e-9 |
| `formation.json` | formation point sets for fixed seeds | 1e-9 |
| `show12.json` | a full 12-drone show (heart → circle → text) | 1e-9 |

Both sides round with `r9` before comparing, then compare with `|a − b| ≤ 1e-9`.

## 11. Size budget

`py/droneshow/` ≤ 3,000 lines total, no module > 300 lines; `js/droneshow.js` ≤ 2,500
lines; comments in Korean, every line ≤ 72 columns (`tools/width.py`).
