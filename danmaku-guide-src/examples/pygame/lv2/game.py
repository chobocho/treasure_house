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
        self.player_x, self.player_y = 240.0, 560.0
        self.previous_x, self.previous_y = self.player_x, self.player_y
        self.cooldown = 0
        self.bullets = Pool(4096)
        self.enemies = Pool(128)
        self.score, self.lives, self.phase = 0, 3, 0
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
            self.bullets.add(self.player_x, self.player_y - 14, 0.0, -SHOT_SPEED)
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


    # region enemy-spawn
    def spawn_enemy(self):
        x = 32 + self.rng.next() % 416
        return self.enemies.add(x, -16.0, 0.0, 1.2, radius=12.0, kind=0, hp=3.0)
    # endregion

    # region enemy-step
    def move_enemies(self):
        pool = self.enemies
        for i in range(pool.count - 1, -1, -1):
            pool.x[i] += pool.vx[i]
            pool.y[i] += pool.vy[i]
            pool.age[i] += 1
            if pool.y[i] > HEIGHT + 32:
                pool.erase(i)
                continue
            if pool.age[i] % 60 == 0:
                self.bullets.add(pool.x[i], pool.y[i] + 12, 0.0, 2.5, radius=4.0, kind=1)
    # endregion

    # region player-hurt
    def hurt(self):
        if self.invulnerable > 0 or self.lives <= 0:
            return False
        self.lives -= 1
        self.invulnerable = 120
        self.player_x, self.player_y = 240.0, 560.0
        self.previous_x, self.previous_y = self.player_x, self.player_y
        return True
    # endregion

    # region enemy-defeat
    def defeat_enemy(self, i):
        self.score += 100
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
                pool.erase(i)
    # endregion

    # region game-step
    def step(self, bits):
        if not isinstance(bits, int) or not 0 <= bits <= 511:
            raise ValueError('입력은 0부터 511까지의 비트 정수여야 합니다')
        if self.invulnerable > 0:
            self.invulnerable -= 1
        self.move_player(bits)
        self.shoot(bits)
        if self.frame % 90 == 30:
            self.spawn_enemy()
        self.move_enemies()
        self.move_bullets()
        self.player_bullet_hits()
        self.enemy_bullet_hits()
        self.enemy_body_hits()
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
