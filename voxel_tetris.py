"""
복셀 테트리스 (pygame) — 앞서 만든 복셀 엔진으로 렌더링.
보드(폭10 × 높이20 × 깊이1)의 각 채워진 셀을 큐브로 그린다.

조작:  ← → 이동,  ↑ 회전,  ↓ 소프트드롭,  Space 하드드롭,  R 재시작,  ESC 종료
실행:  python voxel_tetris.py
"""
import math, random, pygame

# ==================== 복셀 엔진(축약) ====================
def vsub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def vdot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]

def view_transform(cam, p):
    dx, dy, dz = p[0]-cam['pos'][0], p[1]-cam['pos'][1], p[2]-cam['pos'][2]
    cy, sy = math.cos(cam['yaw']), math.sin(cam['yaw'])
    x1, z1 = dx*cy - dz*sy, dx*sy + dz*cy
    cp, sp = math.cos(cam['pitch']), math.sin(cam['pitch'])
    return (x1, dy*cp - z1*sp, dy*sp + z1*cp)

def project(v, W, H, focal):
    s = focal / v[2]
    return (W*0.5 + v[0]*s, H*0.5 - v[1]*s)

FACES = [
    ((0, 1, 0), (0, 1, 0), ((0,1,0),(0,1,1),(1,1,1),(1,1,0)), 1.00),
    ((0,-1, 0), (0,-1, 0), ((0,0,1),(0,0,0),(1,0,0),(1,0,1)), 0.45),
    ((0, 0,-1), (0, 0,-1), ((0,0,0),(0,1,0),(1,1,0),(1,0,0)), 0.80),
    ((0, 0, 1), (0, 0, 1), ((1,0,1),(1,1,1),(0,1,1),(0,0,1)), 0.80),
    ((-1,0, 0), (-1,0, 0), ((0,0,1),(0,1,1),(0,1,0),(0,0,0)), 0.62),
    ((1, 0, 0), (1, 0, 0), ((1,0,0),(1,1,0),(1,1,1),(1,0,1)), 0.62),
]
PAL = {1:(124,196,84), 2:(230,150,40), 3:(70,110,210), 4:(230,210,60),
       5:(210,70,90), 6:(70,200,220), 7:(180,90,210), 8:(90,96,110)}

def shade(rgb, f): return (int(rgb[0]*f), int(rgb[1]*f), int(rgb[2]*f))

def build_faces(voxels, cam, W, H, focal):
    """voxels: dict (x,y,z)->color"""
    out = []
    for (x, y, z), block in voxels.items():
        for n, d, verts, lit in FACES:
            if (x+d[0], y+d[1], z+d[2]) in voxels:
                continue
            cx, cy, cz = x+0.5+n[0]*0.5, y+0.5+n[1]*0.5, z+0.5+n[2]*0.5
            if vdot(n, vsub(cam['pos'], (cx, cy, cz))) <= 0:
                continue
            pts, behind, dsum = [], False, 0.0
            for lv in verts:
                cs = view_transform(cam, (x+lv[0], y+lv[1], z+lv[2]))
                if cs[2] < 0.05:
                    behind = True; break
                dsum += cs[2]
                pts.append(project(cs, W, H, focal))
            if behind:
                continue
            out.append((dsum*0.25, pts, shade(PAL.get(block, PAL[1]), lit)))
    out.sort(key=lambda f: -f[0])
    return out

def draw_faces(surf, faces):
    for _, pts, col in faces:
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, (10, 12, 16), pts, 1)

def look_at(pos, target):
    d = vsub(target, pos); h = math.hypot(d[0], d[2])
    return {'pos': pos, 'yaw': math.atan2(d[0], d[2]), 'pitch': math.atan2(d[1], h)}

# ==================== 테트리스 로직 ====================
COLS, ROWS = 10, 20
SHAPES = {
    'I': (6, [(0,1),(1,1),(2,1),(3,1)]),
    'O': (4, [(1,0),(2,0),(1,1),(2,1)]),
    'T': (7, [(1,0),(0,1),(1,1),(2,1)]),
    'S': (1, [(1,0),(2,0),(0,1),(1,1)]),
    'Z': (5, [(0,0),(1,0),(1,1),(2,1)]),
    'J': (3, [(0,0),(0,1),(1,1),(2,1)]),
    'L': (2, [(2,0),(0,1),(1,1),(2,1)]),
}
BAG = list(SHAPES.keys())

class Game:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.board = [[0]*COLS for _ in range(ROWS)]
        self.bag = []
        self.score = 0; self.lines = 0; self.over = False
        self.cur = self.spawn(self.next_kind())
        self.nxt = self.next_kind()

    def next_kind(self):
        if not self.bag:
            self.bag = BAG[:]; self.rng.shuffle(self.bag)
        return self.bag.pop()

    def spawn(self, kind):
        c, cells = SHAPES[kind]
        return {'kind': kind, 'c': c, 'cells': [list(p) for p in cells], 'x': 3, 'y': 0}

    def rotated(self, p):
        if p['kind'] == 'O':
            return [list(c) for c in p['cells']]
        size = 3 if p['kind'] == 'I' else 2
        return [[size-ry, rx] for rx, ry in p['cells']]

    def cells_at(self, p, cells=None, ox=None, oy=None):
        cells = cells or p['cells']
        ox = p['x'] if ox is None else ox
        oy = p['y'] if oy is None else oy
        return [(cx+ox, cy+oy) for cx, cy in cells]

    def collides(self, p, cells=None, ox=None, oy=None):
        for x, y in self.cells_at(p, cells, ox, oy):
            if x < 0 or x >= COLS or y >= ROWS:
                return True
            if y >= 0 and self.board[y][x]:
                return True
        return False

    def move(self, dx):
        if not self.collides(self.cur, ox=self.cur['x']+dx):
            self.cur['x'] += dx

    def rotate(self):
        r = self.rotated(self.cur)
        for k in (0, -1, 1, -2, 2):
            if not self.collides(self.cur, r, ox=self.cur['x']+k):
                self.cur['cells'] = r; self.cur['x'] += k; return

    def soft(self):
        if not self.collides(self.cur, oy=self.cur['y']+1):
            self.cur['y'] += 1
        else:
            self.settle()

    def hard(self):
        while not self.collides(self.cur, oy=self.cur['y']+1):
            self.cur['y'] += 1
        self.settle()

    def settle(self):
        for x, y in self.cells_at(self.cur):
            if 0 <= y < ROWS and 0 <= x < COLS:
                self.board[y][x] = self.cur['c']
        n = 0
        y = ROWS-1
        while y >= 0:
            if all(self.board[y]):
                del self.board[y]; self.board.insert(0, [0]*COLS); n += 1
            else:
                y -= 1
        self.lines += n; self.score += [0, 100, 300, 500, 800][n]
        self.cur = self.spawn(self.nxt); self.nxt = self.next_kind()
        if self.collides(self.cur):
            self.over = True

def to_voxels(g):
    """보드 → 복셀 dict. 화면 아래가 y=0 이 되도록 뒤집는다."""
    vox = {}
    for by in range(ROWS):
        for bx in range(COLS):
            v = g.board[by][bx]
            if v:
                vox[(bx, ROWS-1-by, 0)] = v
    if not g.over:
        for x, y in g.cells_at(g.cur):
            if 0 <= y < ROWS and 0 <= x < COLS:
                vox[(x, ROWS-1-y, 0)] = g.cur['c']
    return vox

def main():
    pygame.init()
    W, H = 640, 720
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("복셀 테트리스 — pygame")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 22, bold=True)
    g = Game()
    center = (COLS/2, ROWS/2, 0.5)
    drop_ms, acc = 600, 0
    running = True
    while running:
        dt = clock.tick(60)
        acc += dt
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: running = False
                elif e.key == pygame.K_r: g = Game()
                elif not g.over:
                    if e.key == pygame.K_LEFT:  g.move(-1)
                    elif e.key == pygame.K_RIGHT: g.move(1)
                    elif e.key == pygame.K_UP:    g.rotate()
                    elif e.key == pygame.K_DOWN:  g.soft()
                    elif e.key == pygame.K_SPACE: g.hard()
        if not g.over and acc >= drop_ms:
            acc = 0; g.soft()
        cam = look_at((center[0], center[1], -26), center)
        screen.fill((24, 26, 34))
        draw_faces(screen, build_faces(to_voxels(g), cam, W, H, 720))
        screen.blit(font.render("SCORE %d  LINES %d" % (g.score, g.lines), True, (240,240,240)), (16, 12))
        if g.over:
            screen.blit(font.render("GAME OVER — R", True, (255,120,120)), (W//2-100, H//2))
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
