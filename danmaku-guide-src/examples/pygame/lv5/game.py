from array import array
from math import floor, sqrt

# region constants
WIDTH, HEIGHT = 480, 640
SEED = 0x2F6E2B1
LEFT, RIGHT, UP, DOWN = 1, 2, 4, 8
SHOOT, FOCUS, BOMB, START, PAUSE = 16, 32, 64, 128, 256
PLAYER_SPEED, FOCUS_SPEED = 4.0, 1.6
PLAYER_RADIUS, GRAZE_RADIUS = 2.5, 16.0
SHOT_PERIOD, SHOT_SPEED = 8, 8.0
FLOAT_FIELDS = ('x', 'y', 'vx', 'vy', 'radius', 'hp')
INT_FIELDS = ('kind', 'age', 'mark')
FIELDS = FLOAT_FIELDS + INT_FIELDS
# endregion




# 접는 범위와 계산 순서를 고정해 포트 간 반올림을 맞춘다. 시간 O(1), 추가 공간 O(1).
# region dsin
def dsin(turn):
    # region angle-fold
    t = turn - floor(turn)
    if t > .75:
        t -= 1
    elif t > .25:
        t = .5 - t
    # endregion
    x = t * 6.283185307179586
    z = x * x
    # region horner
    p = 1 / 6227020800
    p = -1 / 39916800 + z * p
    p = 1 / 362880 + z * p
    p = -1 / 5040 + z * p
    p = 1 / 120 + z * p
    p = -1 / 6 + z * p
    return x * (1 + z * p)
    # endregion
# endregion


# region dcos
def dcos(turn):
    return dsin(turn + .25)
# endregion


class Rng:
    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF

    # region rng
    def next(self):
        x = self.state
        x = (x ^ (x << 13)) & 0xFFFFFFFF
        x = (x ^ (x >> 17)) & 0xFFFFFFFF
        x = (x ^ (x << 5)) & 0xFFFFFFFF
        self.state = x
        return x
    # endregion


# region collision
def overlaps(ax, ay, ar, bx, by, br):
    dx, dy = ax - bx, ay - by
    radius = ar + br
    return dx * dx + dy * dy <= radius * radius
# endregion


class Pool:
    # region pool-init
    def __init__(self, capacity):
        if not isinstance(capacity, int) or capacity < 0:
            raise ValueError('풀 용량은 음이 아닌 정수여야 합니다')
        self.capacity, self.count = capacity, 0
        for name in FLOAT_FIELDS:
            setattr(self, name, array('d', [0.0]) * capacity)
        for name in INT_FIELDS:
            setattr(self, name, array('i', [0]) * capacity)
    # endregion

    # region pool-add
    def add(self, x, y, vx, vy, radius=3.0, kind=0, hp=1.0):
        if self.count == self.capacity:
            return -1
        i = self.count
        self.count += 1
        self.x[i], self.y[i] = x, y
        self.vx[i], self.vy[i] = vx, vy
        self.radius[i], self.hp[i] = radius, hp
        self.kind[i], self.age[i], self.mark[i] = kind, 0, 0
        return i
    # endregion

    # region pool-erase
    # 순서를 유지하지 않는 대신 삭제 시간 O(1), 추가 공간 O(1)을 보장한다.
    def erase(self, i):
        if not isinstance(i, int) or i < 0 or i >= self.count:
            return False
        last = self.count - 1
        for name in FIELDS:
            column = getattr(self, name)
            column[i] = column[last]
        self.count = last
        return True
    # endregion


class Game:
    # region state-init
    def __init__(self, seed=SEED):
        self.seed = seed & 0xFFFFFFFF
        self.frame = 0
        self.rng = Rng(self.seed)
        self.invulnerable = 0
        self.boss_spawned = False
        self.phase_time = 0
        self.clear_pending = False
        self.player_x, self.player_y = 240.0, 560.0
        self.previous_x, self.previous_y = self.player_x, self.player_y
        self.cooldown = 0
        self.bullets = Pool(4096)
        self.enemies = Pool(128)
        self.score, self.lives, self.phase = 0, 3, 0
    # endregion
        # region rewards-init
        self.items = Pool(64)
        self.power, self.bombs, self.graze_count, self.kill_count = 1, 3, 0, 0
        self.previous_input = 0
        self.event_kind = array('i', [0]) * 64
        self.event_x, self.event_y = array('d', [0.0]) * 64, array('d', [0.0]) * 64
        self.event_count = 0
        # endregion

    # region player-move
    def move_player(self, bits):
        # region previous-player
        self.previous_x, self.previous_y = self.player_x, self.player_y
        # endregion
        # region move-axes
        dx = int(bool(bits & RIGHT)) - int(bool(bits & LEFT))
        dy = int(bool(bits & DOWN)) - int(bool(bits & UP))
        # endregion
        # region move-distance
        speed = FOCUS_SPEED if bits & FOCUS else PLAYER_SPEED
        length = sqrt(dx * dx + dy * dy)
        if length > 0:
            self.player_x += dx * (speed / length)
            self.player_y += dy * (speed / length)
        # endregion
        # region player-clamp
        self.player_x = max(12.0, min(468.0, self.player_x))
        self.player_y = max(12.0, min(628.0, self.player_y))
        # endregion
    # endregion

    # region player-shoot
    def shoot(self, bits):
        if self.cooldown > 0:
            self.cooldown -= 1
        if bits & SHOOT and self.cooldown == 0:
            for i in range(self.power):
                x = self.player_x + (i - (self.power - 1) / 2) * 8
                if self.bullets.add(x, self.player_y - 14, 0.0, -SHOT_SPEED) >= 0:
                    self.emit(1, x, self.player_y - 14)
            self.cooldown = SHOT_PERIOD
    # endregion

    # region bullet-step
    # 역순으로 지워야 옮겨 온 요소를 같은 스텝에 다시 움직이지 않는다. 시간 O(n), 추가 공간 O(1).
    def move_bullets(self):
        pool = self.bullets
        for i in range(pool.count - 1, -1, -1):
            pool.x[i] += pool.vx[i]
            pool.y[i] += pool.vy[i]
            pool.age[i] += 1
            if pool.x[i] < -32 or pool.x[i] > WIDTH + 32 or pool.y[i] < -32 or pool.y[i] > HEIGHT + 32:
                pool.erase(i)
    # endregion



    # region ring
    # 탄수 n에 대해 시간 O(n), 추가 공간 O(1)이며 풀에 바로 기록한다.
    def ring(self, x, y, count, speed, turn=0.0):
        for i in range(count):
            angle = turn + i / count
            self.bullets.add(x, y, dcos(angle) * speed, dsin(angle) * speed, radius=4.0, kind=1)
    # endregion

    # 각도 역변환 없이 정규화한 벡터를 회전한다. 시간 O(n), 추가 공간 O(1).
    # region aimed-fan
    def aimed_fan(self, x, y, count, speed):
        # region aim-vector
        dx, dy = self.player_x - x, self.player_y - y
        length = sqrt(dx * dx + dy * dy)
        ux = dx / length if length > 0 else 0.0
        uy = dy / length if length > 0 else 1.0
        # endregion
        for i in range(count):
            # region fan-velocity
            angle = (i - (count - 1) / 2) * .025
            c, s = dcos(angle), dsin(angle)
            vx = (ux * c - uy * s) * speed
            vy = (ux * s + uy * c) * speed
            self.bullets.add(x, y, vx, vy, radius=4.0, kind=1)
            # endregion
    # endregion

    # region spiral
    def spiral(self, x, y, count, speed, tick):
        self.ring(x, y, count, speed, tick * .007)
    # endregion

    # 위상은 시간에만 두고 탄환 인덱스는 부채꼴 간격으로 펼친다. 인덱스를 위상에 더하면
    # 한 번에 사인 한 주기를 모두 찍어 전체가 흔들리지 않고 대칭인 두 탄환이 겹친다. 시간 O(n), 추가 공간 O(1).
    # region wave
    def wave(self, x, y, count, speed, tick):
        for i in range(count):
            angle = .25 + dsin(tick / 180) * .12 + (i - (count - 1) / 2) * .025
            self.bullets.add(x, y, dcos(angle) * speed, dsin(angle) * speed, radius=4.0, kind=1)
    # endregion

    # region pattern-dispatch
    def fire_pattern(self, x, y, mode, count=8, speed=2.5, tick=None):
        tick = self.frame if tick is None else tick
        if mode == 0:
            self.ring(x, y, count, speed)
        elif mode == 1:
            self.aimed_fan(x, y, count, speed)
        elif mode == 2:
            self.spiral(x, y, count, speed, tick)
        elif mode == 3:
            self.wave(x, y, count, speed, tick)
        else:
            raise ValueError('패턴 번호는 0부터 3까지입니다')
    # endregion


    # region boss-find
    # 교환 삭제로 인덱스가 달라지므로 종류로 다시 찾는다. 시간 O(e), 추가 공간 O(1).
    def find_boss(self):
        for i in range(self.enemies.count - 1, -1, -1):
            if self.enemies.kind[i] == 1:
                return i
        return -1
    # endregion

    # region boss-spawn
    def spawn_boss(self):
        if self.boss_spawned:
            return -1
        index = self.enemies.add(240.0, 100.0, 0.0, 0.0, radius=28.0, kind=1, hp=180.0)
        if index >= 0:
            self.boss_spawned = True
            self.phase, self.phase_time = 1, 0
        return index
    # endregion

    # region clear-enemy-bullets
    # 탄환 순회를 시작하기 전에만 호출한다. 시간 O(b), 추가 공간 O(1).
    def clear_enemy_bullets(self):
        removed = 0
        for i in range(self.bullets.count - 1, -1, -1):
            if self.bullets.kind[i] == 1:
                self.bullets.erase(i)
                removed += 1
        return removed
    # endregion

    # region boss-step
    def update_boss(self, i):
        pool = self.enemies
        # region boss-move
        old_x = pool.x[i]
        pool.age[i] += 1
        pool.x[i] = 240 + 140 * dsin(pool.age[i] / 240)
        pool.vx[i] = pool.x[i] - old_x
        # endregion
        # region boss-transition
        self.phase_time += 1
        if self.phase < 3 and (self.phase_time >= 300 or pool.hp[i] <= 180 - self.phase * 60):
            self.phase += 1
            self.phase_time = 0
            self.emit(7, pool.x[i], pool.y[i])
            self.clear_enemy_bullets()
        # endregion
        # region boss-fire
        interval = 45 if self.phase == 1 else 32 if self.phase == 2 else 4
        if self.phase_time % interval == 0:
            x, y = pool.x[i], pool.y[i] + 24
            if self.phase == 1:
                self.ring(x, y, 12, 2.0, self.frame * .001)
            elif self.phase == 2:
                self.aimed_fan(x, y, 7, 3.0)
            else:
                # 나선은 4스텝마다 세 팔을 이어 쏘고 파동은 그중 20스텝마다 겹쳐 쏜다.
                self.spiral(x, y, 3, 2.5, self.frame)
                if self.phase_time % 20 == 0:
                    self.wave(x, y, 6, 3.0, self.frame)
        # endregion
    # endregion

    # region enemy-spawn
    def spawn_enemy(self):
        x = 32 + self.rng.next() % 416
        index = self.enemies.add(x, -16.0, 0.0, 1.2, radius=12.0, kind=0, hp=3.0)
        if index >= 0:
            self.enemies.mark[index] = (self.frame // 90) % 4
        return index
    # endregion

    # region enemy-step
    def move_enemies(self):
        pool = self.enemies
        for i in range(pool.count - 1, -1, -1):
            if pool.kind[i] == 1:
                self.update_boss(i)
                continue
            pool.x[i] += pool.vx[i]
            pool.y[i] += pool.vy[i]
            pool.age[i] += 1
            if pool.y[i] > HEIGHT + 32:
                pool.erase(i)
                continue
            # 나선은 링 전체를 가끔 쏘면 회전이 링 대칭에 상쇄되므로 두 팔을 6스텝마다 이어 쏜다.
            stream = pool.mark[i] == 2
            if pool.age[i] % (6 if stream else 60) == 0:
                self.fire_pattern(pool.x[i], pool.y[i] + 12, pool.mark[i], 2 if stream else 8)
    # endregion

    # region player-hurt
    def hurt(self):
        if self.invulnerable > 0 or self.lives <= 0:
            return False
        self.emit(2, self.player_x, self.player_y)
        self.lives -= 1
        self.invulnerable = 120
        self.player_x, self.player_y = 240.0, 560.0
        self.previous_x, self.previous_y = self.player_x, self.player_y
        return True
    # endregion

    # region enemy-defeat
    def defeat_enemy(self, i):
        if self.enemies.kind[i] == 1:
            self.score += 1000
            self.phase = 4
            self.clear_pending = True
            self.emit(8, self.enemies.x[i], self.enemies.y[i])
        else:
            self.score += 100
            self.kill_count += 1
            self.emit(3, self.enemies.x[i], self.enemies.y[i])
            if self.kill_count % 3 == 0:
                self.items.add(self.enemies.x[i], self.enemies.y[i], 0.0, 1.5, radius=6.0)
        self.enemies.erase(i)
    # endregion

    # region player-bullet-hit
    # 총알 b개와 적 e개의 직접 비교는 시간 O(b*e), 추가 공간 O(1)이다.
    def player_bullet_hits(self):
        bullets, enemies = self.bullets, self.enemies
        for bi in range(bullets.count - 1, -1, -1):
            if bullets.kind[bi] != 0:
                continue
            for ei in range(enemies.count - 1, -1, -1):
                if overlaps(bullets.x[bi], bullets.y[bi], bullets.radius[bi],
                            enemies.x[ei], enemies.y[ei], enemies.radius[ei]):
                    enemies.hp[ei] -= 1
                    bullets.erase(bi)
                    if enemies.hp[ei] <= 0:
                        self.defeat_enemy(ei)
                    break
    # endregion

    # region enemy-bullet-hit
    def enemy_bullet_hits(self):
        pool = self.bullets
        for i in range(pool.count - 1, -1, -1):
            if pool.kind[i] == 1 and overlaps(self.player_x, self.player_y, PLAYER_RADIUS,
                                             pool.x[i], pool.y[i], pool.radius[i]) and self.hurt():
                pool.erase(i)
    # endregion

    # region enemy-body-hit
    def enemy_body_hits(self):
        pool = self.enemies
        for i in range(pool.count - 1, -1, -1):
            if overlaps(self.player_x, self.player_y, PLAYER_RADIUS,
                        pool.x[i], pool.y[i], pool.radius[i]) and self.hurt():
                if pool.kind[i] != 1:
                    pool.erase(i)
    # endregion

    # region event-emit
    # 알림 포화가 게임 계산에 영향을 주지 않게 한다. 시간 O(1), 추가 공간 O(1).
    def emit(self, kind, x, y):
        if self.event_count == 64:
            return False
        i = self.event_count
        self.event_kind[i], self.event_x[i], self.event_y[i] = kind, x, y
        self.event_count += 1
        return True
    # endregion

    # region graze
    # 표식은 풀의 교환 삭제와 함께 이동한다. 시간 O(b), 추가 공간 O(1).
    def graze(self):
        if self.invulnerable > 0 or self.lives <= 0:
            return
        pool = self.bullets
        for i in range(pool.count):
            if pool.kind[i] != 1 or pool.mark[i] != 0:
                continue
            x, y, r = pool.x[i], pool.y[i], pool.radius[i]
            if (overlaps(self.player_x, self.player_y, GRAZE_RADIUS, x, y, r)
                    and not overlaps(self.player_x, self.player_y, PLAYER_RADIUS, x, y, r)):
                pool.mark[i] = 1
                self.graze_count += 1
                self.score += 10
                self.emit(4, x, y)
    # endregion

    # region bomb
    # 적탄 순회 전에 광역 피해를 확정한다. 시간 O(b+e), 추가 공간 O(1).
    def bomb(self, bits):
        pressed = bits & BOMB and not self.previous_input & BOMB
        self.previous_input = bits
        if not pressed or self.bombs <= 0 or self.lives <= 0:
            return
        self.bombs -= 1
        self.score += self.clear_enemy_bullets() * 5
        self.invulnerable = max(self.invulnerable, 180)
        self.emit(5, self.player_x, self.player_y)
        for i in range(self.enemies.count - 1, -1, -1):
            self.enemies.hp[i] -= 30
            if self.enemies.hp[i] <= 0:
                self.defeat_enemy(i)
    # endregion

    # region item-step
    # 수집과 화면 밖 삭제를 역순으로 처리한다. 시간 O(i), 추가 공간 O(1).
    def move_items(self):
        pool = self.items
        for i in range(pool.count - 1, -1, -1):
            pool.x[i] += pool.vx[i]
            pool.y[i] += pool.vy[i]
            if pool.y[i] > HEIGHT + 32:
                pool.erase(i)
            elif overlaps(self.player_x, self.player_y, 12.0, pool.x[i], pool.y[i], pool.radius[i]):
                self.power = min(3, self.power + 1)
                self.score += 50
                self.emit(6, pool.x[i], pool.y[i])
                pool.erase(i)
    # endregion

    # region game-step
    def step(self, bits):
        if not isinstance(bits, int) or not 0 <= bits <= 511:
            raise ValueError('입력은 0부터 511까지의 비트 정수여야 합니다')
        self.event_count = 0
        if self.invulnerable > 0:
            self.invulnerable -= 1
        self.move_player(bits)
        self.shoot(bits)
        if self.frame % 90 == 30:
            self.spawn_enemy()
        if self.frame >= 600 and not self.boss_spawned:
            self.spawn_boss()
        self.bomb(bits)
        self.move_enemies()
        self.move_bullets()
        self.player_bullet_hits()
        # region deferred-clear
        if self.clear_pending:
            self.clear_enemy_bullets()
            self.clear_pending = False
        # endregion
        self.enemy_bullet_hits()
        self.enemy_body_hits()
        self.graze()
        self.move_items()
        self.frame += 1
    # endregion

    # region snapshot
    # 좌표를 같은 단위로 내림해 언어 간 상태를 비교한다. 시간 O(n), 추가 공간 O(1).
    def snapshot(self):
        checksum = 0
        for i in range(self.bullets.count):
            checksum = (checksum + floor(self.bullets.x[i] * 16) * 31 + floor(self.bullets.y[i] * 16)) & 0xFFFFFFFF
        return {'frame': self.frame, 'bullets': self.bullets.count, 'enemies': self.enemies.count,
                'score': self.score, 'lives': self.lives, 'phase': self.phase, 'checksum': checksum}
    # endregion
