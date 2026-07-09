"""
복셀 엔진 (pygame) — 큐브 래스터라이저.
바닐라 JS 캔버스 버전과 동일한 수학·면 테이블·컬링·화가 알고리즘을 사용한다.

조작:  드래그 = 궤도 회전,  휠 / W·S = 확대·축소,  R = 지형 재생성,  ESC = 종료
실행:  python voxel.py
"""
import math, pygame

# ---------- 벡터 (튜플 기반) ----------
def vsub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def vdot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def vlen(a):    return math.sqrt(vdot(a, a))
def vnorm(a):
    l = vlen(a) or 1.0
    return (a[0]/l, a[1]/l, a[2]/l)

# ---------- 카메라: 월드 점 → 카메라 공간(+z 정면) ----------
def view_transform(cam, p):
    dx, dy, dz = p[0]-cam['pos'][0], p[1]-cam['pos'][1], p[2]-cam['pos'][2]
    cy, sy = math.cos(cam['yaw']), math.sin(cam['yaw'])
    x1 =  dx*cy - dz*sy
    z1 =  dx*sy + dz*cy
    cp, sp = math.cos(cam['pitch']), math.sin(cam['pitch'])
    y2 =  dy*cp - z1*sp        # pitch>0 이면 위를 바라봄
    z2 =  dy*sp + z1*cp
    return (x1, y2, z2)

def project(v, W, H, focal):
    s = focal / v[2]
    return (W*0.5 + v[0]*s, H*0.5 - v[1]*s)

# ---------- 큐브 6면: 정점4 + 바깥 법선 + 이웃 방향 + 밝기 ----------
FACES = [
    ((0, 1, 0), (0, 1, 0), ((0,1,0),(0,1,1),(1,1,1),(1,1,0)), 1.00),  # 윗면
    ((0,-1, 0), (0,-1, 0), ((0,0,1),(0,0,0),(1,0,0),(1,0,1)), 0.45),  # 아랫면
    ((0, 0,-1), (0, 0,-1), ((0,0,0),(0,1,0),(1,1,0),(1,0,0)), 0.80),  # -z
    ((0, 0, 1), (0, 0, 1), ((1,0,1),(1,1,1),(0,1,1),(0,0,1)), 0.80),  # +z
    ((-1,0, 0), (-1,0, 0), ((0,0,1),(0,1,1),(0,1,0),(0,0,0)), 0.62),  # -x
    ((1, 0, 0), (1, 0, 0), ((1,0,0),(1,1,0),(1,1,1),(1,0,1)), 0.62),  # +x
]

PAL = {1:(124,196,84), 2:(150,110,74), 3:(130,132,140), 4:(210,180,70),
       5:(210,70,60), 6:(70,130,210), 7:(200,120,200), 8:(235,235,240)}

def shade(rgb, f):
    return (int(rgb[0]*f), int(rgb[1]*f), int(rgb[2]*f))

# ---------- 복셀 월드 ----------
class World:
    def __init__(self, sx, sy, sz):
        self.sx, self.sy, self.sz = sx, sy, sz
        self.data = bytearray(sx*sy*sz)
    def inb(self, x, y, z):
        return 0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz
    def get(self, x, y, z):
        return self.data[(y*self.sz+z)*self.sx+x] if self.inb(x, y, z) else 0
    def set(self, x, y, z, v):
        if self.inb(x, y, z):
            self.data[(y*self.sz+z)*self.sx+x] = v

# ---------- 가시 면 추출: 이웃컬링 + 백페이스컬링 + 화가 정렬 ----------
def build_faces(w, cam, W, H, focal):
    out = []
    for y in range(w.sy):
        for z in range(w.sz):
            for x in range(w.sx):
                block = w.get(x, y, z)
                if not block:
                    continue
                for n, d, verts, lit in FACES:
                    if w.get(x+d[0], y+d[1], z+d[2]):        # 이웃이 막으면 내부 면
                        continue
                    cx, cy, cz = x+0.5+n[0]*0.5, y+0.5+n[1]*0.5, z+0.5+n[2]*0.5
                    if vdot(n, vsub(cam['pos'], (cx, cy, cz))) <= 0:   # 백페이스
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
    out.sort(key=lambda f: -f[0])           # 먼 면 먼저(화가 알고리즘)
    return out

def draw_faces(surf, faces):
    for _, pts, col in faces:
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, (0, 0, 0), pts, 1)

# ---------- 예제 지형 ----------
def terrain(sx=16, sz=16, sy=10):
    w = World(sx, sy, sz)
    for x in range(sx):
        for z in range(sz):
            h = int(2 + (math.sin(x*0.5)+math.cos(z*0.4)+2)*1.4)
            for y in range(min(h, sy)):
                w.set(x, y, z, 1 if y == h-1 else 2)
    return w

def look_at(pos, target):
    d = vsub(target, pos); h = math.hypot(d[0], d[2])
    return {'pos': pos, 'yaw': math.atan2(d[0], d[2]), 'pitch': math.atan2(d[1], h)}

def main():
    pygame.init()
    W, H = 800, 600
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("복셀 엔진 — pygame")
    clock = pygame.time.Clock()
    world = terrain()
    center = (world.sx/2, 2, world.sz/2)
    yaw, pitch, dist = 0.7, 0.6, 26.0
    dragging = False; running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: running = False
                elif e.key == pygame.K_r: world = terrain()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1: dragging = True
                elif e.button == 4: dist = max(8, dist-2)
                elif e.button == 5: dist = min(60, dist+2)
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                dragging = False
            elif e.type == pygame.MOUSEMOTION and dragging:
                yaw -= e.rel[0]*0.01
                pitch = max(-1.4, min(1.4, pitch + e.rel[1]*0.01))
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: dist = max(8, dist-0.4)
        if keys[pygame.K_s]: dist = min(60, dist+0.4)
        eye = (center[0]+math.sin(yaw)*math.cos(pitch)*dist,
               center[1]+math.sin(pitch)*dist,
               center[2]+math.cos(yaw)*math.cos(pitch)*dist)
        cam = look_at(eye, center)
        screen.fill((30, 34, 44))
        draw_faces(screen, build_faces(world, cam, W, H, 620))
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    main()
