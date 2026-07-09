# -*- coding: utf-8 -*-
# =============================================================
#  PyDoom — 레이캐스팅 Doom 클론 (pygame 단일 파일 완성본)
#  실행: pip install pygame  →  python doom.py
#  조작: W/S 전진·후진, A/D 좌우 회전, Q/E 옆걸음(스트레이프)
#        Space 발사, F 문 열기, Tab 미니맵, Esc 종료
# =============================================================
import math
import sys
import pygame

# ---------- 1. 상수 ----------
W, H       = 640, 400          # 내부 렌더 해상도 (낮을수록 빠름)
SCALE      = 2                 # 화면 확대 배율 → 실제 창 1280x800
HALF_H     = H // 2
FOV        = math.pi / 3       # 시야각 60도
NUM_RAYS   = W                 # 화면 세로줄 하나당 광선 하나
MAX_DEPTH  = 24.0              # 광선 최대 사거리
TEX        = 64                # 텍스처 한 변 크기
MOVE_SPD   = 3.2               # 초당 이동 칸수
ROT_SPD    = 2.6               # 초당 회전 라디안
FPS        = 60

# ---------- 2. 맵 ----------
# 0 빈칸 / 1 벽돌 / 2 돌 / 3 금속 / 4 문(닫힘) / 5 출구
MAP_STR = [
    "1111111111111111",
    "1000000110000001",
    "1020000110000201",
    "1000000000000001",
    "1000111141110001",
    "1000100000010001",
    "1300100000010031",
    "1000100000010001",
    "1000111411110001",
    "1000000000000001",
    "1020000330000201",
    "1000000330000001",
    "1000000000000051",
    "1111111111111111",
]
MAP_W, MAP_H = len(MAP_STR[0]), len(MAP_STR)
world = [[int(c) for c in row] for row in MAP_STR]

def cell(x, y):
    if 0 <= x < MAP_W and 0 <= y < MAP_H:
        return world[y][x]
    return 1

# ---------- 3. 절차적 텍스처 ----------
def make_textures():
    """이미지 파일 없이 코드로 64x64 텍스처 5장을 만든다."""
    texs = {}
    for tid in (1, 2, 3, 4, 5):
        surf = pygame.Surface((TEX, TEX))
        for y in range(TEX):
            for x in range(TEX):
                if tid == 1:                       # 벽돌
                    row = y // 16
                    off = 16 if row % 2 else 0
                    mortar = (y % 16 < 2) or ((x + off) % 32 < 2)
                    c = (60, 24, 20) if mortar else (150, 60, 44)
                    if not mortar and (x * 7 + y * 13) % 31 == 0:
                        c = (120, 46, 36)
                elif tid == 2:                     # 돌
                    n = (x * x * 3 + y * y * 7 + x * y) % 97
                    g = 90 + (n % 40)
                    c = (g, g, g + 8)
                    if (x + y * 3) % 23 == 0:
                        c = (70, 70, 78)
                elif tid == 3:                     # 금속판
                    g = 70 + (y % 16) * 3
                    c = (g - 20, g, g + 14)
                    if x % 16 in (0, 1) or y % 16 in (0, 1):
                        c = (40, 46, 56)
                    if (x % 16, y % 16) in ((4, 4), (12, 4), (4, 12), (12, 12)):
                        c = (180, 190, 205)
                elif tid == 4:                     # 문
                    c = (40, 90, 60) if (x // 8 + y // 8) % 2 else (30, 70, 46)
                    if 28 <= x < 36:
                        c = (200, 170, 60)
                else:                              # 출구
                    c = (160, 30, 30) if (x // 8 + y // 8) % 2 else (240, 220, 210)
                surf.set_at((x, y), c)
        texs[tid] = surf
        # 어두운 버전(그늘진 남북 벽면용)을 미리 만들어 둔다
        dark = surf.copy()
        dark.fill((128, 128, 128), special_flags=pygame.BLEND_MULT)
        texs[tid + 100] = dark
    return texs

# ---------- 4. 스프라이트(적/아이템) ----------
def make_imp():
    """간단한 픽셀 아트 악마 스프라이트를 코드로 그린다."""
    s = pygame.Surface((TEX, TEX), pygame.SRCALPHA)
    body = (140, 70, 40)
    for y in range(TEX):
        for x in range(TEX):
            dx, dy = x - 32, y - 34
            if dx * dx // 2 + dy * dy < 500:            # 몸통
                s.set_at((x, y), body)
    pygame.draw.circle(s, (120, 55, 30), (32, 16), 11)  # 머리
    pygame.draw.circle(s, (255, 240, 80), (27, 14), 3)  # 눈
    pygame.draw.circle(s, (255, 240, 80), (37, 14), 3)
    pygame.draw.circle(s, (0, 0, 0), (27, 14), 1)
    pygame.draw.circle(s, (0, 0, 0), (37, 14), 1)
    pygame.draw.polygon(s, (200, 180, 160), [(22, 8), (18, 0), (26, 6)])   # 뿔
    pygame.draw.polygon(s, (200, 180, 160), [(42, 8), (46, 0), (38, 6)])
    pygame.draw.rect(s, body, (14, 30, 8, 20))          # 팔
    pygame.draw.rect(s, body, (42, 30, 8, 20))
    pygame.draw.rect(s, (110, 50, 28), (24, 52, 7, 12)) # 다리
    pygame.draw.rect(s, (110, 50, 28), (33, 52, 7, 12))
    return s

def make_medkit():
    s = pygame.Surface((TEX, TEX), pygame.SRCALPHA)
    pygame.draw.rect(s, (235, 235, 235), (16, 34, 32, 22), border_radius=3)
    pygame.draw.rect(s, (200, 40, 40), (28, 38, 8, 14))
    pygame.draw.rect(s, (200, 40, 40), (25, 41, 14, 8))
    return s

class Sprite:
    def __init__(self, x, y, kind):
        self.x, self.y, self.kind = x, y, kind   # kind: 'imp' | 'medkit'
        self.hp = 3 if kind == 'imp' else 0
        self.alive = True
        self.cool = 0.0                          # 공격 쿨타임

# ---------- 5. 게임 상태 ----------
class Player:
    def __init__(self):
        self.x, self.y = 1.5, 1.5
        self.ang = 0.3
        self.hp = 100
        self.ammo = 40

def reset_world():
    global world
    world = [[int(c) for c in row] for row in MAP_STR]
    sprites = [
        Sprite(9.5, 1.5, 'imp'), Sprite(12.5, 6.5, 'imp'),
        Sprite(6.5, 11.5, 'imp'), Sprite(10.5, 10.5, 'imp'),
        Sprite(2.5, 12.2, 'imp'),
        Sprite(4.5, 9.5, 'medkit'), Sprite(14.5, 2.5, 'medkit'),
    ]
    return Player(), sprites

# ---------- 6. DDA 레이캐스팅 ----------
def cast_ray(px, py, ang):
    """(맞은 칸 값, 수직거리, 벽면 x좌표 0~1, 남북면 여부)를 돌려준다."""
    sin_a, cos_a = math.sin(ang), math.cos(ang)
    map_x, map_y = int(px), int(py)
    # 한 칸 이동에 필요한 광선 길이
    ddx = abs(1 / cos_a) if cos_a else 1e30
    ddy = abs(1 / sin_a) if sin_a else 1e30
    if cos_a < 0:
        step_x, side_x = -1, (px - map_x) * ddx
    else:
        step_x, side_x = 1, (map_x + 1 - px) * ddx
    if sin_a < 0:
        step_y, side_y = -1, (py - map_y) * ddy
    else:
        step_y, side_y = 1, (map_y + 1 - py) * ddy
    side = 0
    for _ in range(64):
        if side_x < side_y:                 # 다음 세로 격자선이 더 가깝다
            side_x += ddx
            map_x += step_x
            side = 0
        else:                               # 다음 가로 격자선이 더 가깝다
            side_y += ddy
            map_y += step_y
            side = 1
        tile = cell(map_x, map_y)
        if tile > 0:
            dist = (side_x - ddx) if side == 0 else (side_y - ddy)
            hit = (py + dist * sin_a) if side == 0 else (px + dist * cos_a)
            return tile, max(dist, 1e-4), hit - int(hit), side
    return 1, MAX_DEPTH, 0.0, 0

# ---------- 7. 렌더링 ----------
def render_walls(buf, texs, pl):
    zbuf = [MAX_DEPTH] * NUM_RAYS
    for col in range(NUM_RAYS):
        # 화면 x좌표 → 광선 각도 (탄젠트 기반: 어안 왜곡 없음)
        cam = 2 * col / NUM_RAYS - 1            # -1 .. +1
        ray_ang = pl.ang + math.atan(cam * math.tan(FOV / 2))
        tile, dist, wall_x, side = cast_ray(pl.x, pl.y, ray_ang)
        depth = dist * math.cos(ray_ang - pl.ang)   # 어안 보정
        zbuf[col] = depth
        line_h = int(H / depth)
        tex = texs[tile + (100 if side == 1 else 0)]
        tex_x = int(wall_x * TEX) % TEX
        # 텍스처 한 줄(1xTEX)을 잘라 세로로 늘려 붙인다
        column = tex.subsurface(tex_x, 0, 1, TEX)
        y0 = HALF_H - line_h // 2
        if line_h < H * 3:
            column = pygame.transform.scale(column, (1, line_h))
            buf.blit(column, (col, y0))
        else:                                    # 벽이 화면보다 훨씬 클 때
            vis = pygame.Rect(0, int((0 - y0) / line_h * TEX), 1,
                              max(1, int(H / line_h * TEX)))
            vis = vis.clip(column.get_rect())
            column = pygame.transform.scale(column.subsurface(vis), (1, H))
            buf.blit(column, (col, 0))
        # 거리 안개(멀수록 어둡게)
        fog = min(1.0, depth / 12.0)
        if fog > 0.05:
            shade = pygame.Surface((1, min(line_h, H)))
            shade.set_alpha(int(fog * 180))
            buf.blit(shade, (col, max(y0, 0)))
    return zbuf

def render_sprites(buf, images, pl, sprites, zbuf):
    order = sorted((s for s in sprites if s.alive),
                   key=lambda s: -((s.x - pl.x) ** 2 + (s.y - pl.y) ** 2))
    for s in order:
        dx, dy = s.x - pl.x, s.y - pl.y
        dist = math.hypot(dx, dy)
        if dist < 0.4 or dist > MAX_DEPTH:
            continue
        # 플레이어 시선 기준 상대 각도
        rel = math.atan2(dy, dx) - pl.ang
        rel = (rel + math.pi) % (2 * math.pi) - math.pi
        if abs(rel) > FOV / 2 + 0.4:
            continue
        depth = dist * math.cos(rel)
        size = int(H / depth)
        if size <= 1:
            continue
        # 화면 x좌표: tan 비율로 투영
        sx = int((0.5 + math.tan(rel) / (2 * math.tan(FOV / 2))) * W - size / 2)
        sy = HALF_H - size // 2
        img = pygame.transform.scale(images[s.kind], (size, size))
        # 세로줄 단위로 z버퍼와 비교해 벽 뒤 부분은 그리지 않는다
        for i in range(max(0, -sx), min(size, W - sx)):
            col = sx + i
            if depth < zbuf[col]:
                buf.blit(img, (col, sy), pygame.Rect(i, 0, 1, size))

def render_minimap(buf, pl, sprites):
    mm = 6
    pygame.draw.rect(buf, (10, 10, 14), (0, 0, MAP_W * mm, MAP_H * mm))
    for y in range(MAP_H):
        for x in range(MAP_W):
            if world[y][x]:
                col = (90, 90, 110) if world[y][x] != 4 else (60, 160, 90)
                pygame.draw.rect(buf, col, (x * mm, y * mm, mm - 1, mm - 1))
    for s in sprites:
        if s.alive and s.kind == 'imp':
            pygame.draw.circle(buf, (220, 60, 40), (int(s.x * mm), int(s.y * mm)), 2)
    pygame.draw.circle(buf, (80, 220, 120), (int(pl.x * mm), int(pl.y * mm)), 2)
    ex = pl.x + math.cos(pl.ang) * 1.2
    ey = pl.y + math.sin(pl.ang) * 1.2
    pygame.draw.line(buf, (80, 220, 120),
                     (pl.x * mm, pl.y * mm), (ex * mm, ey * mm))

def render_hud(buf, font, pl, msg, gun_kick):
    # 총 (화면 하단 중앙의 간단한 스프라이트)
    gx, gy = W // 2 - 22, H - 62 + int(gun_kick * 18)
    pygame.draw.polygon(buf, (55, 60, 70),
                        [(gx, H), (gx + 16, gy), (gx + 30, gy), (gx + 44, H)])
    pygame.draw.rect(buf, (35, 38, 46), (gx + 17, gy - 14, 12, 20))
    if gun_kick > 0.55:                          # 총구 화염
        pygame.draw.circle(buf, (255, 220, 90), (gx + 23, gy - 20), 10)
        pygame.draw.circle(buf, (255, 120, 30), (gx + 23, gy - 20), 5)
    # 상태 표시줄
    pygame.draw.rect(buf, (16, 16, 22), (0, H - 24, W, 24))
    hp_col = (90, 220, 90) if pl.hp > 30 else (230, 70, 50)
    buf.blit(font.render('HP %3d' % pl.hp, False, hp_col), (10, H - 20))
    buf.blit(font.render('AMMO %2d' % pl.ammo, False, (240, 200, 80)), (110, H - 20))
    if msg:
        t = font.render(msg, False, (255, 255, 255))
        buf.blit(t, (W // 2 - t.get_width() // 2, 30))

# ---------- 8. 게임 로직 ----------
def try_move(pl, nx, ny):
    """벽에 부딪히면 축별로 나눠 미끄러지게 한다."""
    r = 0.25
    if cell(int(nx + math.copysign(r, nx - pl.x)), int(pl.y)) == 0:
        pl.x = nx
    if cell(int(pl.x), int(ny + math.copysign(r, ny - pl.y))) == 0:
        pl.y = ny

def fire(pl, sprites):
    if pl.ammo <= 0:
        return '탄약이 없다!'
    pl.ammo -= 1
    # 시선과 가장 가까운(각도차가 작은) 살아있는 적을 찾는다
    best, best_d = None, 1e9
    for s in sprites:
        if not s.alive or s.kind != 'imp':
            continue
        d = math.hypot(s.x - pl.x, s.y - pl.y)
        rel = math.atan2(s.y - pl.y, s.x - pl.x) - pl.ang
        rel = (rel + math.pi) % (2 * math.pi) - math.pi
        if abs(rel) < 0.12 and d < best_d:
            # 벽이 가로막고 있으면 못 맞춘다
            _, wall_d, _, _ = cast_ray(pl.x, pl.y, math.atan2(s.y - pl.y, s.x - pl.x))
            if wall_d > d:
                best, best_d = s, d
    if best:
        best.hp -= 1
        if best.hp <= 0:
            best.alive = False
            return '악마 처치!'
        return ''
    return ''

def update_enemies(pl, sprites, dt):
    hurt = ''
    for s in sprites:
        if not s.alive:
            continue
        if s.kind == 'medkit':
            if math.hypot(s.x - pl.x, s.y - pl.y) < 0.5 and pl.hp < 100:
                pl.hp = min(100, pl.hp + 25)
                s.alive = False
                hurt = '구급상자 +25'
            continue
        d = math.hypot(s.x - pl.x, s.y - pl.y)
        if d > 8 or d < 0.001:
            continue
        # 시야가 트여 있을 때만 추적
        ang = math.atan2(pl.y - s.y, pl.x - s.x)
        _, wall_d, _, _ = cast_ray(s.x, s.y, ang)
        if wall_d < d:
            continue
        if d > 1.0:                              # 추적
            spd = 1.3 * dt
            nx, ny = s.x + math.cos(ang) * spd, s.y + math.sin(ang) * spd
            if cell(int(nx), int(s.y)) == 0:
                s.x = nx
            if cell(int(s.x), int(ny)) == 0:
                s.y = ny
        else:                                    # 공격
            s.cool -= dt
            if s.cool <= 0:
                pl.hp -= 8
                s.cool = 1.0
                hurt = '피격! -8'
    return hurt

def open_door(pl):
    tx = int(pl.x + math.cos(pl.ang) * 1.2)
    ty = int(pl.y + math.sin(pl.ang) * 1.2)
    if cell(tx, ty) == 4:
        world[ty][tx] = 0
        return '문이 열렸다'
    if cell(tx, ty) == 5:
        return 'EXIT'
    return ''

# ---------- 9. 메인 루프 ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((W * SCALE, H * SCALE))
    pygame.display.set_caption('PyDoom — Raycasting Clone')
    clock = pygame.time.Clock()
    buf = pygame.Surface((W, H))
    font = pygame.font.SysFont('monospace', 14, bold=True)
    texs = make_textures()
    images = {'imp': make_imp(), 'medkit': make_medkit()}
    pl, sprites = reset_world()
    show_map, msg, msg_t, gun_kick, over = True, '', 0.0, 0.0, ''

    while True:
        dt = clock.tick(FPS) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if e.key == pygame.K_TAB:
                    show_map = not show_map
                if e.key == pygame.K_SPACE and not over:
                    m = fire(pl, sprites)
                    gun_kick = 1.0
                    if m: msg, msg_t = m, 1.2
                if e.key == pygame.K_f and not over:
                    m = open_door(pl)
                    if m == 'EXIT':
                        over = '탈출 성공! R로 재시작'
                    elif m:
                        msg, msg_t = m, 1.2
                if e.key == pygame.K_r and over:
                    pl, sprites = reset_world()
                    over = ''

        keys = pygame.key.get_pressed()
        if not over:
            if keys[pygame.K_a]: pl.ang -= ROT_SPD * dt
            if keys[pygame.K_d]: pl.ang += ROT_SPD * dt
            dx = math.cos(pl.ang) * MOVE_SPD * dt
            dy = math.sin(pl.ang) * MOVE_SPD * dt
            if keys[pygame.K_w]: try_move(pl, pl.x + dx, pl.y + dy)
            if keys[pygame.K_s]: try_move(pl, pl.x - dx, pl.y - dy)
            if keys[pygame.K_q]: try_move(pl, pl.x + dy, pl.y - dx)
            if keys[pygame.K_e]: try_move(pl, pl.x - dy, pl.y + dx)

            m = update_enemies(pl, sprites, dt)
            if m: msg, msg_t = m, 1.2
            if pl.hp <= 0:
                pl.hp = 0
                over = '전사... R로 재시작'

        gun_kick = max(0.0, gun_kick - dt * 4)
        msg_t = max(0.0, msg_t - dt)

        # ---- 그리기 ----
        buf.fill((30, 34, 44), (0, 0, W, HALF_H))            # 천장
        buf.fill((52, 46, 40), (0, HALF_H, W, HALF_H))       # 바닥
        zbuf = render_walls(buf, texs, pl)
        render_sprites(buf, images, pl, sprites, zbuf)
        render_hud(buf, font, pl, msg if msg_t > 0 else '', gun_kick)
        if show_map:
            render_minimap(buf, pl, sprites)
        if over:
            t = font.render(over, False, (255, 80, 60))
            buf.blit(t, (W // 2 - t.get_width() // 2, HALF_H - 8))
        pygame.transform.scale(buf, screen.get_size(), screen)
        pygame.display.flip()

if __name__ == '__main__':
    main()
